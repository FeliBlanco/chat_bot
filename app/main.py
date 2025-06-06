from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from config import settings
import time
import json
from sqlalchemy.orm import Session
import models
import schemas
from database import SessionLocal, engine, Base
import calendar_service
from send_message import send_message

Base.metadata.create_all(bind=engine)

app = FastAPI()

#configuramos el cors etc
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

motor_gpt = "gpt-3.5-turbo"
modo_bot = "asistente"

#para conectarse a openai
client = OpenAI(api_key=settings.OPENAI_API_KEY)

#creamos el thread para comenzar la conversacion
thread = client.beta.threads.create()

#traemos la instancia de la db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/dispo")
def get_dispo():
    return calendar_service.get_disponibilidad("2025-06-05T18:00")

@app.post("/modelo")
async def change_model(request: Request):
    data = await request.json()
    global motor_gpt, modo_bot
    motor_gpt = data["modelo"]
    modo_bot = data["mode"]
    return {
        "modelo": motor_gpt,
        "mode": modo_bot
    }

@app.get("/modelo")
def get_model():
    return {
        "modelo": motor_gpt,
        "mode": modo_bot
    }

@app.get("/citas")
def get_citas():
    print("Obteniendo citas")
    try:
        eventos = calendar_service.get_eventos()
        return {"eventos": eventos}
    except Exception as e:
        return {"error": str(e)}
    

#ruta para hablar con el asistente
@app.get("/test")
def test():
    calendar_service.sacar_turno("2025-06-05T18:00")
    return "hola"

@app.post("/")
async def chat(request: Request):
    try:
        data = await request.json()
        if modo_bot == "asistente":
            return ejecutar_asistente(data["prompt"])
        elif modo_bot == "chat":
            return ejecutar_chat(data["prompt"])
    except Exception as e:
        return {"error": str(e)}

@app.get("/logs/", response_model=list[schemas.LogOut])
def listar_logs(db: Session = Depends(get_db)):
    return db.query(models.ChatLog).all()

@app.get("/productos/", response_model=list[schemas.ProductoOut])
def listar_productos(db: Session = Depends(get_db)):
    return db.query(models.Producto).all()

@app.get("/producto/", response_model=schemas.ProductoOut)
def crear_producto(nombre: str, precio: int, db: Session = Depends(get_db)):
    db_producto = models.Producto(nombre=nombre, precio=precio)
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def ejecutar_chat(prompt: str):
    response = client.responses.create(
        model=motor_gpt,
        input=prompt
    )
    return response.output_text

def ejecutar_asistente(prompt: str):
    #crear mensaje en el thread
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        #creamos el run y lo asociamos al asistente
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=settings.ASSISTANT_ID
        )

        #el loop para ver los estados y respuestas del run
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id   
            )

            #si necesita ejecutar una funcion
            if run_status.status == "requires_action":
                tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for call in tool_calls:
                    if call.function.name == "get_products":
                        #llama a la funcion de buscar producto
                        args = json.loads(call.function.arguments)
                        resultado = buscar_producto(args["nombre"])
                        tool_outputs.append({
                            "tool_call_id": call.id,
                            "output": json.dumps(resultado)
                        })
                    elif call.function.name == "get_horarios":
                        #o si llama a la funcion de horarios
                        horarios = get_horarios()
                        tool_outputs.append({
                            "tool_call_id": call.id,
                            "output": json.dumps(horarios)
                        })
                    elif call.function.name == "schedule_appointment":
                        print("BUSCAR AGENDAA")
                        args = json.loads(call.function.arguments)
                        print(args)
                        fecha_hora_str = f"{args['date']}T{args['time']}"
                        nuevo_turno = calendar_service.sacar_turno(fecha_hora_str)
                        if nuevo_turno == True:
                            tool_outputs.append({
                                "tool_call_id": call.id,
                                "output": "Turno sacado correctamente"
                            })

                            send_message(args['whatsapp'], "Sacaste un turno para el " + args['date'] + " a las " + args['time'] + ".")
          
                        else:
                            tool_outputs.append({
                                "tool_call_id": call.id,
                                "output": "No hay turnos disponibles en esa fecha y hora"
                            })  
                            

                client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )

            elif run_status.status in ['completed', 'failed']:
                break

            time.sleep(1)

        #listamos los mensajes
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in messages.data:
            if msg.role == "assistant":
                print("Assistant:", msg.content[0].text.value)
                guardar_chat(prompt, msg.content[0].text.value)
                return msg.content[0].text.value

        return "ok"

def buscar_producto(nombre: str):
    print("BUSCAR PRODUCTOS")
    try:
        db: Session = next(get_db())
        producto = db.query(models.Producto).filter(models.Producto.nombre.ilike(f"%{nombre.rstrip('s')}%")).first()
        if producto:
            print("Si hay producto")
            return {
                "id": producto.id,
                "nombre": producto.nombre,
                "precio": producto.precio
            }
        else:
            print("No hay producto")
            return {"error": "Producto no encontrado"}
    except Exception as e:
        print(e)
        return {"error": str(e)}
    
def get_horarios():
    with open("horarios.json", "r", encoding="utf-8") as f:
        return json.load(f)
    
def guardar_chat(pregunta: str, respuesta: str):
    db: Session = next(get_db())
    log = models.ChatLog(pregunta=pregunta, respuesta=respuesta)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from openai import OpenAI
from config import settings
import time
import json
from sqlalchemy.orm import Session
import models
import schemas
from database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

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

#ruta para hablar con el asistente
@app.get("/")
def chat(prompt: str = None):
    try:
        if settings.ENGINE_IA == 0:
            return ejecutar_asistente(prompt)
        elif settings.ENGINE_IA == 1:
            return ejecutar_chat(prompt)
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
        model="gpt-4.1",
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
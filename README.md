# CHAT BOT
Con este bot, podrás configurarlo para poder usarlo como un chat normal o como un asistente de una tienda, donde podrás entrenarlo para responder sobre los productos que tengas disponibles.


## Deployment

Para ejecutar el proyecto, sólo debe ejecutar

```bash
  docker-compose up --build
```


## Environment Variables

Para ejecutar el proyecto, debes configurar el archivo .env con los datos necesarios

`OPENAI_API_KEY`

`ENGINE_IA` Donde 0 es para usar el asistente y 1 para usar el chat común

`GOOGLE_API_KEY`

`GOOGLE_CLIENT_ID`

`SECRET_KEY`

`ASSISTANT_ID`


## Usage/Examples

```javascript
import Component from 'my-project'

function App() {
  return <Component />
}
```


# Documentation

Endpoints:

GET`http://localhost:8000/productos`
Lista los productos de la base de datos

GET `http://localhost:8000/producto?nombre=&precio=`
Agrega un producto a la base de datos

GET `http://localhost:8000/logs`
Muestra los logs de consulta y respuesta al bot

GET `http://localhost:8000?prompt=`
Habla con el bot

### Archivo horarios.json
En este archivo, podrás agregar los dias y horarios de atención, para que el bot pueda responder.
Ejemplo:

`[
    {
        "dia": "Lunes a Viernes",
        "horarios": [
            "08:30 a 12:00",
            "15:30 a 20:0"
        ]
    },
    {
        "dia": "Sábados",
        "horarios": [
            "08:30 a 12:00"
        ]
    }
]`
## Tech Stack

**Server:** Python, FastAPI, PostgreSQL, Docker
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime, timedelta
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar']

credentials = service_account.Credentials.from_service_account_file(
    'permisos.json', scopes=SCOPES)

def get_calendar_service():
    service = build('calendar', 'v3', credentials=credentials)
    return service

def crear_evento():
    service = get_calendar_service()
    event = {
        'summary': 'Reunión con cliente',
        'location': 'Buenos Aires',
        'description': 'Discutir proyecto nuevo',
        'start': {
            'dateTime': '2025-06-04T10:00:00-03:00',
            'timeZone': 'America/Argentina/Buenos_Aires',
        },
        'end': {
            'dateTime': '2025-06-04T11:00:00-03:00',
            'timeZone': 'America/Argentina/Buenos_Aires',
        },
    }

    event = service.events().insert(calendarId='blancofeli9@gmail.com', body=event).execute()
    return {"message": "Evento creado", "link": event.get("htmlLink")}

def get_eventos():
    service = get_calendar_service()
    eventos = service.events().list(
        calendarId='blancofeli9@gmail.com',
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return eventos.get('items', [])

def get_eventos_por_fecha(fecha_str):
    service = get_calendar_service()

    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    time_min = fecha.isoformat() + 'Z'
    time_max = (fecha + timedelta(days=1)).isoformat() + 'Z'

    eventos = service.events().list(
        calendarId="blancofeli9@gmail.com",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return eventos.get('items', [])

def sacar_turno(fecha_hora_str):
    service = get_calendar_service()

    fecha_hora = datetime.strptime(fecha_hora_str, "%Y-%m-%dT%H:%M")

    tz = pytz.timezone("America/Argentina/Buenos_Aires")
    fecha_inicio = tz.localize(fecha_hora)
    fecha_fin = fecha_inicio + timedelta(minutes=20)


    body = {
        "timeMin": fecha_inicio.isoformat(),
        "timeMax": fecha_fin.isoformat(),
        "timeZone": "America/Argentina/Buenos_Aires",
        "items": [{"id": "blancofeli9@gmail.com"}]
    }

    response = service.freebusy().query(body=body).execute()
    ocupados = response['calendars']['blancofeli9@gmail.com']['busy']

    print("---------------")
    print(ocupados)
    if ocupados:
        return False
    else:
        service = get_calendar_service()
        evento = {
            'summary': 'Reunión con cliente',
            'location': 'Córdoba',
            'description': 'Cita para consulta de un equipo',
            'start': {
                'dateTime': fecha_hora.isoformat(),
                'timeZone': 'America/Argentina/Buenos_Aires',
            },
            'end': {
                'dateTime': fecha_fin.isoformat(),
                'timeZone': 'America/Argentina/Buenos_Aires',
            }
        }
        evento_creado = service.events().insert(calendarId='blancofeli9@gmail.com', body=evento).execute()
        return True

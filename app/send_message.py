import requests

url = 'http://micro_wsp:8001/send-message'

def send_message(number: str, message: str):
    response = requests.get(url, params={'number': number, 'message': message})
    return response.json()

# Importación de bibliotecas necesarias
import json
from dotenv import load_dotenv
import os
import requests
import aiohttp
import asyncio

# --------------------------------------------------------------
# Cargar variables de entorno
# --------------------------------------------------------------

# Carga las variables de entorno del archivo .env
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

# --------------------------------------------------------------
# Enviar un mensaje de plantilla de WhatsApp
# --------------------------------------------------------------

# Función para enviar un mensaje de plantilla predefinido
def send_whatsapp_message():
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": "Bearer " + ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT_WAID,
        "type": "template",
        "template": {"name": "hello_world", "language": {"code": "en_US"}},
    }
    response = requests.post(url, headers=headers, json=data)
    return response

# Llamada a la función y impresión de la respuesta
response = send_whatsapp_message()
print(response.status_code)
print(response.json())

# --------------------------------------------------------------
# Enviar un mensaje de texto personalizado de WhatsApp
# --------------------------------------------------------------

# NOTA: ¡Primero responde al mensaje del usuario en WhatsApp!

# Función para crear el cuerpo del mensaje de texto
def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

# Función para enviar el mensaje
def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        print("Status:", response.status_code)
        print("Content-type:", response.headers["content-type"])
        print("Body:", response.text)
        return response
    else:
        print(response.status_code)
        print(response.text)
        return response

# Preparar y enviar un mensaje de prueba
data = get_text_message_input(
    recipient=RECIPIENT_WAID, text="Hello, this is a test message."
)

response = send_message(data)

# --------------------------------------------------------------
# Enviar un mensaje de texto personalizado de WhatsApp de forma asíncrona
# --------------------------------------------------------------

# NOTA: No funciona con Jupyter

# Función asíncrona para enviar mensajes
async def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    async with aiohttp.ClientSession() as session:
        url = "https://graph.facebook.com" + f"/{VERSION}/{PHONE_NUMBER_ID}/messages"
        try:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    print("Status:", response.status)
                    print("Content-type:", response.headers["content-type"])

                    html = await response.text()
                    print("Body:", html)
                else:
                    print(response.status)
                    print(response)
        except aiohttp.ClientConnectorError as e:
            print("Connection Error", str(e))

# Función para crear el cuerpo del mensaje (igual que antes)
def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

# Preparar y enviar un mensaje de prueba de forma asíncrona
data = get_text_message_input(
    recipient=RECIPIENT_WAID, text="Hello, this is a test message."
)

loop = asyncio.get_event_loop()
loop.run_until_complete(send_message(data))
loop.close()
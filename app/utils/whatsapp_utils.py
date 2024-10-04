# Importación de bibliotecas necesarias
import logging
from flask import current_app, jsonify
import json
import requests
from dotenv import load_dotenv
import os
from app.services.openai_service import generate_response
import re

# Cargar variables de entorno
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Función para registrar la respuesta HTTP
def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")

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

# Función para enviar el mensaje a través de la API de WhatsApp
def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Tiempo de espera agotado al enviar el mensaje")
        return jsonify({"status": "error", "message": "Tiempo de espera agotado"}), 408
    except requests.RequestException as e:
        logging.error(f"La solicitud falló debido a: {e}")
        return jsonify({"status": "error", "message": "Fallo al enviar el mensaje"}), 500
    else:
        log_http_response(response)
        return response

# Función para procesar el texto para WhatsApp (eliminar corchetes y ajustar formato)
def process_text_for_whatsapp(text):
    pattern = r"\【.*?\】"
    text = re.sub(pattern, "", text).strip()
    pattern = r"\*\*(.*?)\*\*"
    replacement = r"*\1*"
    whatsapp_style_text = re.sub(pattern, replacement, text)
    return whatsapp_style_text

# Función principal para procesar los mensajes de WhatsApp
def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    # Generar respuesta usando OpenAI
    response = generate_response(message_body, wa_id, name)
    response = process_text_for_whatsapp(response)

    data = get_text_message_input(wa_id, response)
    send_message(data)

# Función para verificar si el mensaje de WhatsApp es válido
def is_valid_whatsapp_message(body):
    """
    Verifica si el evento entrante del webhook tiene una estructura válida de mensaje de WhatsApp.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
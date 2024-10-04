# Importación de bibliotecas necesarias
import logging
import json
from dotenv import load_dotenv
import os

from flask import Blueprint, request, jsonify, current_app

from .decorators.security import signature_required
from .utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)

# Cargar variables de entorno
load_dotenv()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# Crear un Blueprint de Flask para el webhook
webhook_blueprint = Blueprint("webhook", __name__)

# Función para manejar los mensajes entrantes
def handle_message():
    """
    Maneja los eventos entrantes del webhook de la API de WhatsApp.

    Esta función procesa los mensajes entrantes de WhatsApp y otros eventos,
    como los estados de entrega. Si el evento es un mensaje válido, se procesa.
    Si la carga útil entrante no es un evento reconocido de WhatsApp,
    se devuelve un error.

    Cada mensaje enviado activará 4 solicitudes HTTP a tu webhook: mensaje, enviado, entregado, leído.

    Retorna:
        response: Una tupla que contiene una respuesta JSON y un código de estado HTTP.
    """
    body = request.get_json()

    # Verificar si es una actualización de estado de WhatsApp
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Recibida una actualización de estado de WhatsApp.")
        return jsonify({"status": "ok"}), 200

    try:
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
            return jsonify({"status": "ok"}), 200
        else:
            # Si la solicitud no es un evento de la API de WhatsApp, devolver un error
            return (
                jsonify({"status": "error", "message": "No es un evento de la API de WhatsApp"}),
                404,
            )
    except json.JSONDecodeError:
        logging.error("Fallo al decodificar JSON")
        return jsonify({"status": "error", "message": "JSON proporcionado inválido"}), 400

# Verificación de webhook requerida para WhatsApp
def verify():
    # Analizar los parámetros de la solicitud de verificación del webhook
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    # Verificar si se enviaron un token y un modo
    if mode and token:
        # Verificar si el modo y el token enviados son correctos
        if mode == "subscribe" and token == VERIFY_TOKEN:
            # Responder con 200 OK y el token de desafío de la solicitud
            logging.info("WEBHOOK_VERIFICADO")
            return challenge, 200
        else:
            # Responder con '403 Forbidden' si los tokens de verificación no coinciden
            logging.info("VERIFICACIÓN_FALLIDA")
            return jsonify({"status": "error", "message": "Verificación fallida"}), 403
    else:
        # Responder con '400 Bad Request' si faltan parámetros
        logging.info("PARÁMETRO_FALTANTE")
        return jsonify({"status": "error", "message": "Parámetros faltantes"}), 400

# Ruta GET para la verificación del webhook
@webhook_blueprint.route("/webhook", methods=["GET"])
def webhook_get():
    return verify()

# Ruta POST para manejar los mensajes entrantes
@webhook_blueprint.route("/webhook", methods=["POST"])
@signature_required
def webhook_post():
    return handle_message()
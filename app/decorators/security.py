from functools import wraps
from flask import current_app, jsonify, request
import logging
import hashlib
import hmac
from dotenv import load_dotenv
import os


# Carga de variables de entorno
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")


def validate_signature(payload, signature):
    """
    Validate the incoming payload's signature against our expected signature
    """
    # Use the App Secret to hash the payload
    expected_signature = hmac.new(
        bytes(APP_SECRET, "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Check if the signature matches
    return hmac.compare_digest(expected_signature, signature)


def signature_required(f):
    """
    Decorator to ensure that the incoming requests to our webhook are valid and signed with the correct signature.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = request.headers.get("X-Hub-Signature-256", "")[
            7:
        ]  # Removing 'sha256='
        if not validate_signature(request.data.decode("utf-8"), signature):
            logging.info("Signature verification failed!")
            return jsonify({"status": "error", "message": "Invalid signature"}), 403
        return f(*args, **kwargs)

    return decorated_function

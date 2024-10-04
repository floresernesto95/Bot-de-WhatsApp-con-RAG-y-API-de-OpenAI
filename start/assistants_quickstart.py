# Importación de bibliotecas necesarias
from openai import OpenAI
import shelve
from dotenv import load_dotenv
import os
import time

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

# Inicialización del cliente de OpenAI
OPEN_AI_API_KEY = OPENAI_API_KEY
client = OpenAI(api_key=OPEN_AI_API_KEY)

# --------------------------------------------------------------
# Función para subir archivos
# --------------------------------------------------------------
def upload_file(path):
    # Sube un archivo con el propósito "assistants"
    file = client.files.create(file=open(path, "rb"), purpose="assistants")
    return file

# Ejemplo de uso de la función upload_file (comentado)
file = "/media/ernesto/Data/Projects/AI/Bot - WhatsApp/python-whatsapp-bot/v0.3 - File ids/data/airbnb-faq.pdf"

# --------------------------------------------------------------
# Función para crear un asistente
# --------------------------------------------------------------
def create_assistant():
    # Crea un asistente con instrucciones específicas
    assistant = client.beta.assistants.create(
        name="WhatsApp AirBnb Assistant",
        instructions="You're a helpful WhatsApp assistant that can assist guests that are staying in our Paris AirBnb. Use your knowledge base to best respond to customer queries. If you don't know the answer, say simply that you cannot help with question and advice to contact the host directly. Be friendly and funny.",
        tools=[{"type": "file_search"}],
        model="gpt-4o-mini"
    )
    return assistant

# Crear el asistente
assistant = create_assistant()

# --------------------------------------------------------------
# Subir archivos y crear un vector store
# --------------------------------------------------------------
# Crea un vector store llamado "Airbnb Information"
vector_store = client.beta.vector_stores.create(name="Airbnb Information")

# Prepara los archivos para subirlos a OpenAI
file_paths = [file]
file_streams = [open(path, "rb") for path in file_paths]

# Utiliza el SDK para subir los archivos, añadirlos al vector store y esperar la finalización
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)

# Imprime el estado y el conteo de archivos del lote
print(file_batch.status)
print(file_batch.file_counts)

# --------------------------------------------------------------
# Actualizar el asistente
# --------------------------------------------------------------
# Actualiza el asistente con los recursos del vector store
assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# --------------------------------------------------------------
# Manejo de hilos de conversación
# --------------------------------------------------------------
def check_if_thread_exists(wa_id):
    # Verifica si existe un hilo para un ID de WhatsApp dado
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)

def store_thread(wa_id, thread_id):
    # Almacena un nuevo hilo para un ID de WhatsApp
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id

# --------------------------------------------------------------
# Generar respuesta
# --------------------------------------------------------------
def generate_response(message_body, wa_id, name):
    # Genera una respuesta para un mensaje de WhatsApp
    thread_id = check_if_thread_exists(wa_id)

    if thread_id is None:
        print(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Añade el mensaje al hilo
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Ejecuta el asistente y obtiene el nuevo mensaje
    new_message = run_assistant(thread)
    print(f"To {name}:", new_message)
    return new_message

# --------------------------------------------------------------
# Ejecutar el asistente
# --------------------------------------------------------------
def run_assistant(thread):
    # Recupera el asistente y lo ejecuta
    assistant = client.beta.assistants.retrieve("asst_ZEjluFnL8RliI6VKwfRoib8C")

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    # Espera a que se complete la ejecución
    while run.status != "completed":
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Recupera los mensajes y devuelve el más reciente
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    print(f"Generated message: {new_message}")
    return new_message

# --------------------------------------------------------------
# Prueba del asistente
# --------------------------------------------------------------
# Ejemplos de uso del asistente con diferentes usuarios y preguntas
new_message = generate_response("What's the check in time?", "123", "John")

new_message = generate_response("What's the pin for the lockbox?", "456", "Sarah")

new_message = generate_response("What was my previous question?", "123", "John")

new_message = generate_response("What was my previous question?", "456", "Sarah")
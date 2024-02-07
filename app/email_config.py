import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app import drive
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(to):
    CLIENT_SECRET_FILE = 'app/client_secret.json'
    API_NAME = 'gmail'
    API_VERSION = 'v1'
    SCOPES = ['https://mail.google.com/']

    service = drive.Create_Email_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

    emailMsg = 'Visibilidad cambiada correctamente'
    mimeMessage = MIMEMultipart()
    mimeMessage['to'] = to
    mimeMessage['subject'] = 'Visibilidad cambiada correctamente'
    mimeMessage.attach(MIMEText(emailMsg, 'plain'))
    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()

    message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
    print(message)


def get_file_owner(service, file_id):
    try:
        # Obtiene la metadata del archivo
        file_metadata = service.files().get(fileId=file_id, fields='owners').execute()

        # Obtiene la lista de propietarios del archivo
        owners = file_metadata.get('owners', [])

        if owners:
            # Devuelve el correo electrónico del primer propietario encontrado
            return owners[0].get('emailAddress')
        else:
            return None

    except Exception as e:
        print("Error al obtener el propietario del archivo:", e)
        return None

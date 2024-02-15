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

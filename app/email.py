from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import mysql.connector
import smtplib
from email.mime.text import MIMEText


# Enviar correo electrónico de notificación
def send_notification_email(owner_email):
    # Configurar los parámetros del correo electrónico
    sender_email = "your-email"
    sender_password = "your-password"
    subject = "Cambio de visibilidad de archivo en Google Drive"
    message = "Estimado/a propietario/a del archivo, queremos informarte que la visibilidad de tu archivo en Google Drive ha sido cambiada de público a privado."

    # Crear el objeto MIMEText para el correo electrónico
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = owner_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    # Establecer la conexión con el servidor SMTP de Gmail
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)

    # Enviar el correo electrónico
    server.sendmail(sender_email, owner_email, msg.as_string())

    # Cerrar la conexión con el servidor SMTP
    server.quit()


def process_public_files(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM files WHERE visibility = 'public'")
    public_files = cursor.fetchall()

    if not public_files:
        print("No se encontraron archivos públicos para modificar.")
    else:
        for file in public_files:
            # Modificar la configuración de visibilidad a "private" en la base de datos
            try:
                cursor.execute("UPDATE files SET visibility = 'private' WHERE id = %s", (file['id'],))
                conn.commit()
            except Exception as e:
                print("Error al actualizar la configuración de visibilidad:", e)
                conn.rollback()
                continue

            # Enviar un correo electrónico al propietario notificando el cambio realizado
            owner_email = file['owner_email']
            subject = "Cambio de visibilidad de archivo en tu unidad de Drive"
            message = f"Estimado {file['owner']},\n\nEl archivo '{file['name']}' ha sido cambiado de público a privado en tu unidad de Drive."
            send_notification_email(owner_email)

    cursor.close()




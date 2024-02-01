import mysql.connector
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import mysql.connector
import smtplib
from email.mime.text import MIMEText


def authenticate(credentials_file):
    """
    Autenticación con la API de Google Drive utilizando las credenciales proporcionadas.
    """
    creds = Credentials.from_authorized_user_file(credentials_file)
    return build('drive', 'v3', credentials=creds)


def connect_db(host, username, password):
    # Establece una conexión con la base de datos MySQL.
    try:
        conn = mysql.connector.connect(
            host=host,
            user=username,
            password=password,

        )
        print("Conexión exitosa!")
        return conn
    except mysql.connector.Error as err:
        print("Error: ", err)


def create_db(conn):
    # Crear la base de datos
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS drive_inventory_db")
    cursor.execute("USE drive_inventory_db")
    print("Base de datos creada correctamente")

    # Crear la tabla de archivos
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                extension VARCHAR(255),
                owner VARCHAR(255) NOT NULL,
                visibility ENUM('public', 'private') NOT NULL,
                last_modified DATETIME
            )
        """)

    # Cerrar la conexión
    cursor.close()


def insert_or_update_file(conn, file_info):
    """
    Inserta un nuevo archivo en la base de datos o actualiza la información si ya existe.
    """
    cursor = conn.cursor()
    query = """
        INSERT INTO files (name, extension, owner, visibility, last_modified)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        extension = VALUES(extension),
        owner = VALUES(owner),
        visibility = VALUES(visibility),
        last_modified = VALUES(last_modified)
    """
    cursor.execute(query, (
        file_info['name'], file_info['extension'], file_info['owner'], file_info['visibility'],
        file_info['last_modified']))
    conn.commit()
    cursor.close()

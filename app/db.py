import mysql.connector
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from datetime import datetime


def authenticate(credentials_file):
    # Autenticación con la API de Google Drive utilizando las credenciales proporcionadas.

    creds = Credentials.from_authorized_user_file(credentials_file)
    return build('drive', 'v3', credentials=creds)

def connect_db(host, username, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=database
        )
        print("Conexión exitosa!")
        return conn
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            try:
                conn = mysql.connector.connect(
                    host=host,
                    user=username,
                    password=password
                )
                cursor = conn.cursor()
                cursor.execute("CREATE DATABASE {}".format(database))
                print("Base de datos creada correctamente!")
                conn.database = database
                return conn
            except mysql.connector.Error as err:
                print("Error al crear la base de datos: {}".format(err))
                return None
        else:
            print("Hubo un error con la conexión: ", err)
            return None


def create_db(conn):
    try:
        # Crear la base de datos
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS drive_inventory_db")
        cursor.execute("USE drive_inventory_db")

        # Crear la tabla de archivos
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    extension VARCHAR(255),
                    owner VARCHAR(255) NOT NULL,
                    visibility ENUM('public', 'private') NOT NULL,
                    last_modified DATETIME
                )
            """)
        print("Base de datos y tabla creadas correctamente")

        # Cerrar la conexión
        cursor.close()

    except mysql.connector.Error as err:
        print("Hubo un error con la creacion de la base de datos: ", err)


def list_files_from_db(conn):
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM files")
        files = cursor.fetchall()
        if not files:
            print("No hay archivos en la base de datos.")
        else:
            print("{:<50} {:<70} {:<15} {:<30} {:<15} {:<40}".format(
                "ID", "Nombre", "Extensión", "Propietario", "Visibilidad", "Última Modificación"
            ))
            print("-" * 200)
            for file in files:
                print("{:<50} {:<70} {:<15} {:<30} {:<15} {:<40}".format(
                    file['id'], file['name'], file['extension'], file['owner'], file['visibility'],
                    file['last_modified']
                ))
            return files
    except mysql.connector.Error as err:
        print("Hubo un error al listar los archivos:", err)
    finally:
        cursor.close()


# Guardar archivos en la base de datos
def save_files(drive_service, conn):
    cursor = conn.cursor()
    drive_files = drive_service.files().list(pageSize=10,
                                             fields="files(id, name, owners, webViewLink, modifiedTime)").execute().get(
        'files', [])
    for file in drive_files:
        file_info = {
            'id': file['id'],
            'name': file['name'],
            'extension': file['name'].split('.')[-1],  # Obtener la extensión del archivo
            'owner': file['owners'][0]['displayName'],
            'visibility': 'public' if 'anyoneWithLink' in file.get('webViewLink', '') else 'private',
            'last_modified': datetime.strptime(file['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        }
        cursor.execute("SELECT id FROM files WHERE id = %s", (file_info['id'],))
        result = cursor.fetchone()
        if not result:
            cursor.execute("""
                INSERT INTO files (id, name, extension, owner, visibility, last_modified)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                file_info['id'], file_info['name'], file_info['extension'], file_info['owner'], file_info['visibility'],
                file_info['last_modified']))
            conn.commit()
    print("Archivos guardados y actualizados correctamente.")
    cursor.close()


# Limpiar la base de datos
def clear_database(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files")
        conn.commit()
        cursor.close()
        print("Base de datos limpiada correctamente")

    except mysql.connector.Error as err:
        print("Hubo un error con la limpieza de la base de datos: ", err)


# Guardar archivos nuevos o actualizar existentes
def save_files(drive_service, conn):
    cursor = conn.cursor()
    drive_files = drive_service.files().list(pageSize=10,
                                             fields="files(id, name, owners, webViewLink, modifiedTime)").execute().get(
        'files', [])
    for file in drive_files:
        file_info = {
            'id': file['id'],
            'name': file['name'],
            'extension': file['name'].split('.')[-1],  # Obtener la extensión del archivo
            'owner': file['owners'][0]['displayName'],
            'visibility': 'public' if 'anyoneWithLink' in file.get('webViewLink', '') else 'private',
            'last_modified': datetime.strptime(file['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        }
        cursor.execute("SELECT id FROM files WHERE id = %s", (file_info['id'],))
        result = cursor.fetchone()
        if result:
            # Archivo existente, actualizar si es necesario
            cursor.execute("""
                UPDATE files 
                SET name = %s, extension = %s, owner = %s, visibility = %s, last_modified = %s
                WHERE id = %s
            """, (file_info['name'], file_info['extension'], file_info['owner'], file_info['visibility'],
                  file_info['last_modified'], file_info['id']))
        else:
            # Archivo nuevo, insertar
            cursor.execute("""
                INSERT INTO files (id, name, extension, owner, visibility, last_modified)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                file_info['id'], file_info['name'], file_info['extension'], file_info['owner'], file_info['visibility'],
                file_info['last_modified']))
        # Guardar cambios
        conn.commit()
    cursor.close()


# Mantener un inventario histórico de archivos públicos
def save_public_files_history(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE visibility = 'public'")
    public_files = cursor.fetchall()
    for file in public_files:
        # Registrar el archivo público en el historial
        cursor.execute("""
            INSERT INTO public_files_history (id, name, extension, owner, visibility, last_modified)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file['id'], file['name'], file['extension'], file['owner'], file['visibility'], file['last_modified']))
        # Eliminar el archivo de la tabla principal (opcional)
        cursor.execute("DELETE FROM files WHERE id = %s", (file['id'],))
        conn.commit()
    cursor.close()



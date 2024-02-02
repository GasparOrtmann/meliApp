import mysql.connector
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from app import email


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

        # Crear la tabla de historial de archivos públicos
        cursor.execute("""
                   CREATE TABLE IF NOT EXISTS public_files_history (
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

def list_public_files_history(conn):
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM public_files_history")
        public_files_history = cursor.fetchall()
        if not public_files_history:
            print("No hay archivos en la tabla 'public_files_history'.")
        else:
            print("{:<50} {:<70} {:<15} {:<30} {:<15} {:<40}".format(
                "ID", "Nombre", "Extensión", "Propietario", "Visibilidad", "Última Modificación"
            ))
            print("-" * 200)
            for file in public_files_history:
                print("{:<50} {:<70} {:<15} {:<30} {:<15} {:<40}".format(
                    file['id'], file['name'], file['extension'], file['owner'], file['visibility'],
                    file['last_modified']
                ))
            return public_files_history
    except mysql.connector.Error as err:
        print("Hubo un error al listar los archivos de la tabla 'public_files_history':", err)
    finally:
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
            email.send_notification_email(owner_email)

    cursor.close()

# Mantener un inventario histórico de archivos públicos
def save_public_files_history(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE visibility = 'public'")
    public_files = cursor.fetchall()
    for file in public_files:
        try:
            # Intentar insertar el archivo público en el historial
            cursor.execute("""
                INSERT IGNORE INTO public_files_history (id, name, extension, owner, visibility, last_modified)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (file[0], file[1], file[2], file[3], file[4], file[5]))
            conn.commit()
        except mysql.connector.Error as err:
            print(f"Error al insertar el archivo {file[1]} en el historial:", err)
            conn.rollback()
    cursor.close()




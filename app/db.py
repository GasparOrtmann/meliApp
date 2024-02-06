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
                last_modified DATETIME,
                is_directory BOOLEAN NOT NULL DEFAULT FALSE
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


def get_visibility(service, file_id):
    try:
        # Consulta a la API de Google Drive para obtener los permisos del archivo
        permissions = service.permissions().list(fileId=file_id, fields="permissions(id, role)").execute()

        # Si hay algún permiso asignado al archivo
        if 'permissions' in permissions:
            for perm in permissions['permissions']:
                # Si hay un permiso con el rol de 'reader', entonces el archivo es público
                if perm['role'] == 'reader':
                    return 'public'

        # Si no se encontró un permiso de 'reader', el archivo es privado
        return 'private'

    except Exception as e:
        print(f"Error al obtener los permisos del archivo {file_id}:", e)
        return 'private'


def list_files_from_google_drive(service, folder_id='root'):
    try:
        # Consulta específica para obtener archivos y carpetas dentro de una carpeta
        query = f"'{folder_id}' in parents and trashed=false"

        # Listar archivos y carpetas de Google Drive
        results = service.files().list(q=query, pageSize=10,
                                       fields="nextPageToken, files(id, name, mimeType, owners, webViewLink, modifiedTime)").execute()
        items = results.get('files', [])
        #print("ITEMS", items)
        if not items:
            print("No hay archivos en Google Drive.")
        else:
            print("{:<50} {:<70} {:<15} {:<30} {:<15} {:<40}".format(
                "ID", "Nombre", "Tipo", "Propietario", "Visibilidad", "Última Modificación"
            ))
            print("-" * 200)
            for item in items:
                owner_info = item.get('owners', [{'displayName': 'Propietario_Desconocido'}])
                owner_name = owner_info[0]['displayName']
                item['owners'] = owner_name
                # Determinar la visibilidad del archivo a partir de los permisos asignados
                visibility = get_visibility(service, item['id'])

                last_modified = item.get('modifiedTime', 'Desconocida')

                # Agrega el campo visibility al diccionario del elemento actual
                item['visibility'] = visibility

                print("{:<50} {:<70} {:<15} {:<30} {:<15} {:<40}".format(
                    item['id'], item['name'], item['mimeType'], owner_name, visibility, last_modified
                ))
            return items

    except Exception as e:
        print("Hubo un error al listar los archivos desde Google Drive:", e)


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


def save_files(service, conn):
    cursor = conn.cursor()

    try:
        # Consulta específica para obtener archivos y carpetas dentro de la raíz
        query = "'root' in parents and trashed=false"

        # Listar archivos y carpetas de Google Drive
        results = service.files().list(q=query, pageSize=10,
                                       fields="files(id, name, mimeType, owners, webViewLink, modifiedTime)").execute()
        drive_files = results.get('files', [])

        for file in drive_files:
            file_info = {
                'id': file['id'],
                'name': file['name'],
                'extension': file['mimeType'] if file['mimeType'] != 'application/vnd.google-apps.folder' else None,
                'owner': file['owners'][0]['displayName'],
                'visibility': get_visibility(service, file['id']),
                'last_modified': datetime.strptime(file['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                'is_directory': file['mimeType'] == 'application/vnd.google-apps.folder'
            }

            cursor.execute("SELECT id FROM files WHERE id = %s", (file_info['id'],))
            result = cursor.fetchone()
            if result:
                # Archivo existente, actualizar si es necesario
                cursor.execute("""
                    UPDATE files 
                    SET name = %s, extension = %s, owner = %s, visibility = %s, last_modified = %s, is_directory = %s
                    WHERE id = %s
                """, (file_info['name'], file_info['extension'], file_info['owner'], file_info['visibility'],
                      file_info['last_modified'], file_info['is_directory'], file_info['id']))
            else:
                # Archivo nuevo, insertar
                cursor.execute("""
                    INSERT INTO files (id, name, extension, owner, visibility, last_modified, is_directory)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    file_info['id'], file_info['name'], file_info['extension'], file_info['owner'],
                    file_info['visibility'],
                    file_info['last_modified'], file_info['is_directory']))
            # Guardar cambios
            conn.commit()
    except Exception as e:
        print("Hubo un error al guardar los archivos desde Google Drive:", e)
        conn.rollback()
    finally:
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


# Listar todos los archivos encontrados en la unidad "My Drive".
def list_allfiles(service, folder_id='root'):
    all_files = []

    try:
        # Consulta específica para obtener archivos y carpetas dentro de una carpeta
        query = f"'{folder_id}' in parents and trashed=false"

        # Listar archivos y carpetas de Google Drive
        results = service.files().list(q=query, pageSize=10,
                                       fields="nextPageToken, files(id, name, mimeType, owners, webViewLink, modifiedTime)").execute()
        items = results.get('files', [])

        if not items:
            print(f"No hay archivos en la carpeta con ID: {folder_id}.")
        else:
            for item in items:
                # Determinar el propietario del archivo
                owner_info = item.get('owners', [{'displayName': 'Propietario_Desconocido'}])
                owner_name = owner_info[0]['displayName']

                # Determinar la visibilidad del archivo
                visibility = 'publico' if 'anyoneWithLink' in item.get('webViewLink', '') else 'privado'

                # Obtener la última fecha de modificación del archivo
                last_modified = item.get('modifiedTime', 'Desconocida')

                # Agregar los campos de propietario, visibilidad y última modificación al diccionario del elemento actual
                item['owners'] = owner_name
                item['visibility'] = visibility
                item['last_modified'] = last_modified

                all_files.append(item)

                # Si el elemento es un directorio, explorar sus archivos de manera recursiva
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    subdirectory_files = list_files_from_google_drive(service, folder_id=item['id'])
                    all_files.extend(subdirectory_files)

        return all_files

    except Exception as e:
        print(f"Hubo un error al listar los archivos desde la carpeta con ID {folder_id}:", e)
        return []

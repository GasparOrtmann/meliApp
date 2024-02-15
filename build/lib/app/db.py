import mysql.connector
import mysql.connector
from datetime import datetime
import tkinter as tk


def connect_db(host, username, password, database):
    try:
        # Intenta conectar a la base de datos
        conn = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=database
        )
        return conn

    except mysql.connector.Error as err:
        # Si hay un error de conexión
        if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            try:
                # Intenta crear la base de datos
                conn = mysql.connector.connect(
                    host=host,
                    user=username,
                    password=password
                )
                cursor = conn.cursor()
                cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(database))
                cursor.close()
                conn.close()

                # Intenta conectar nuevamente después de crear la base de datos
                conn = mysql.connector.connect(
                    host=host,
                    user=username,
                    password=password,
                    database=database
                )
                return conn

            except mysql.connector.Error as err:
                print("Error al crear la base de datos: {}".format(err))
                return None
        else:
            # Si hay otro tipo de error de conexión
            print("Error al conectar a la base de datos: {}".format(err))
            return None


def create_db(conn, service):
    try:
        # Verificar si la base de datos está creada
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [database[0] for database in cursor.fetchall()]

        if 'drive_inventory_db' in databases:
            # La base de datos existe, verificar si tiene tablas
            cursor.execute("USE drive_inventory_db")
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]

            if 'files' not in tables or 'public_files_history' not in tables:
                # Limpiar los archivos en Google Drive
                clean_google_drive(service)

                # Crear las tablas de archivos y historial de archivos públicos
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
                print("Tabla 'files' creada correctamente")
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
                print("Tabla 'public_files_history' creada correctamente")

                print("Base de datos y tablas creadas correctamente")

            else:
                print("La base de datos ya tiene las tablas 'files' y 'public_files_history'")

        else:
            print("La base de datos 'drive_inventory_db' no existe")

        # Cerrar la conexión
        cursor.close()

    except mysql.connector.Error as err:
        print("Hubo un error con la creación de la base de datos: ", err)


def clean_google_drive(service):
    try:
        # Obtener la lista de archivos de Google Drive
        results = service.files().list(fields="files(id, name)").execute()
        files = results.get('files', [])

        # Eliminar cada archivo de Google Drive
        for file in files:
            service.files().delete(fileId=file['id']).execute()

        print("Archivos en Google Drive eliminados correctamente")

    except Exception as e:
        print("Error al limpiar los archivos en Google Drive: ", e)


def list_files_from_google_drive(service, folder_id='root'):
    try:
        # Consulta específica para obtener archivos y carpetas dentro de una carpeta
        query = f"'{folder_id}' in parents and trashed=false"

        # Listar archivos y carpetas de Google Drive
        results = service.files().list(q=query, pageSize=10,
                                       fields="nextPageToken, files(id, name, mimeType, owners, webViewLink, "
                                              "modifiedTime)").execute()
        items = results.get('files', [])
        # print("ITEMS", items)
        if not items:
            print("No hay archivos en Google Drive.")
        else:
            # print("{:<50} {:<70} {:<15} {:<30} {:<15} {:<40}".format(
            #     "ID", "Nombre", "Tipo", "Propietario", "Visibilidad", "Última Modificación"
            # ))
            # print("-" * 200)
            for item in items:
                owner_info = item.get('owners', [{'displayName': 'Propietario_Desconocido'}])
                owner_name = owner_info[0]['displayName']
                item['owners'] = owner_name
                visibility = detect_visibility(service, item.get('id'))
                modifiedTime = item.get('modifiedTime', 'Desconocida')

                print("{:<50} {:<70} {:<15} {:<30} {:<15} {:<40}".format(
                    item['id'], item['name'], item['mimeType'], owner_name, visibility, modifiedTime
                ))
            return items

    except Exception as e:
        print("Hubo un error al listar los archivos desde Google Drive:", e)


def get_files(conn):
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM files")
        files = cursor.fetchall()
        return files
    except mysql.connector.Error as err:
        print(f"Error al recuperar archivos de la base de datos: {err}")
        return []


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


def sync_db(service, conn):
    cursor = conn.cursor()

    try:
        # Delete existing files in the database
        cursor.execute("DELETE FROM files")

        # Get files from Google Drive
        files = list_files_from_google_drive(service)
        # Insert files into the database
        for file in files:
            file_id = file['id']
            file_name = file['name'].rsplit('.', 1)[0]  # Eliminar la extensión del nombre del archivo
            file_extension = file['mimeType'].rsplit('/', 1)[1]  # Obtiene lo que está después del último '/'
            if '.' in file_extension:
                file_extension = file_extension.rsplit('.', 1)[1]  # Obtiene lo que está después del último '.'
            file_owner = file['owners'].split('@')[0]

            # Obtener la fecha y hora actual en el formato correcto si 'modifiedTime' está disponible
            if 'modifiedTime' in file and file['modifiedTime']:
                modified_time_str = file['modifiedTime']
                modified_time_obj = datetime.strptime(modified_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                file_last_modified = modified_time_obj.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Asignar un valor predeterminado si no hay 'modifiedTime'
                file_last_modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Determinar visibilidad según permisos
            file_visibility = detect_visibility(service, file['id'])

            try:
                cursor.execute("""
                      INSERT INTO files (id, name, extension, owner, visibility, last_modified)
                      VALUES (%s, %s, %s, %s, %s, %s)
                  """, (file_id, file_name, file_extension, file_owner, file_visibility, file_last_modified))
                conn.commit()
                print(f"Archivo sincronizado: {file_name}")
            except mysql.connector.Error as err:
                print(f"Error al insertar el archivo {file_name} en la base de datos: {err}")
                conn.rollback()

        print("Sincronización de archivos y base de datos completada.")
        tk.messagebox.showinfo("Sincronización", "Sincronización de archivos y base de datos completada.")

    except Exception as e:
        print("Error al sincronizar archivos y base de datos:", e)
        tk.messagebox.showinfo("Error al sincronizar archivos y base de datos.")
        conn.rollback()

    finally:
        cursor.close()


def detect_visibility(service, file_id):
    try:
        # Consultar la API de Google Drive para obtener los permisos del archivo
        permissions = service.permissions().list(fileId=file_id, fields="permissions(role)").execute()

        # Verificar si hay algún permiso que indique que el archivo es público
        for permission in permissions.get('permissions', []):
            role = permission.get('role')
            if role == 'reader':
                return 'public'

        # Si no se encuentra ningún permiso de 'reader', el archivo es privado
        return 'private'

    except Exception as e:
        print(f"Error al obtener los permisos del archivo {file_id}: {e}")
        return 'private'


def change_file_visibility(service, file_id):
    try:
        # Eliminamos el permiso público existente si existe
        permissions = service.permissions().list(fileId=file_id).execute()
        for permission in permissions.get('permissions', []):
            if permission['type'] == 'anyone' and permission['role'] == 'reader':
                service.permissions().delete(fileId=file_id, permissionId=permission['id']).execute()
                print(f"Visibilidad del archivo con ID {file_id} cambiada a privado.")
                return
        print(f"El archivo con ID {file_id} ya es privado.")
    except Exception as e:
        print(f"Error al cambiar la visibilidad del archivo con ID {file_id}: {e}")


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

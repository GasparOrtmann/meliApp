from datetime import datetime

from app import db


def main():
    # Autenticación con la API de Google Drive
    credentials_file = 'app/token.json'
    drive_service = db.authenticate(credentials_file)

    # Conexión a la base de datos MySQL
    host = "localhost"
    username = "root"
    password = "root"
    database_name = "drive_inventory_db"

    conn = db.connect_db(host, username, password)

    # Crear la tabla de archivos si no existe
    db.create_db(conn)

    # Listar archivos de Google Drive
    results = drive_service.files().list(pageSize=10,
                                         fields="nextPageToken, files(id, name, owners, webViewLink, modifiedTime)").execute()
    items = results.get('files', [])

    # Procesar y guardar archivos en la base de datos
    for item in items:
        file_info = {
            'name': item['name'],
            'extension': item['name'].split('.')[-1],  # Extraer la extensión del nombre del archivo
            'owner': item['owners'][0]['displayName'],
            'visibility': 'public' if 'anyoneWithLink' in item.get('webViewLink', '') else 'private',
            'last_modified': datetime.strptime(item['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
        }

        # Insertar o actualizar en la base de datos
        db.insert_or_update_file(conn, file_info)

    # Cerrar conexión a la base de datos
    conn.close()


if __name__ == '__main__':
    main()

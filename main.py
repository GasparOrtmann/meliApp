from app import db

def main():


    # Conexión a la base de datos MySQL
    host = "localhost"
    username = "root"
    password = "root"
    database_name = "drive_inventory_db"

    conn = db.connect_db(host, username, password)

    # Crear la tabla de archivos si no existe
    db.create_db(conn)

   
    # Cerrar conexión a la base de datos
    conn.close()

if __name__ == '__main__':
    main()



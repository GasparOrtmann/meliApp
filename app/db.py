import mysql.connector

def connect_db(host,username, password, db_name):
    # Establece una conexión con la base de datos MySQL.
    try:
        conn = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=db_name
        )
        print("Conexión exitosa!")
        return conn
    except mysql.connector.Error as err:
        print("Error: ", err)

def create_db():
        conn = connect_db('localhost', 'root', 'root', 'meli_test')
        # Crear la base de datos
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS drive_inventory_db")
        cursor.execute("USE drive_inventory_db")
        print("Base de datos creada correctamente")

        # Crear la tabla de archivos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                extension VARCHAR(10),
                owner VARCHAR(50) NOT NULL,
                visibility ENUM('public', 'private') NOT NULL,
                last_modified DATETIME
            )
        """)

        # Cerrar la conexión
        cursor.close()
        conn.close()
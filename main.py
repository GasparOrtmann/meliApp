import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import mysql.connector
from app import db
from app import email


def main():
    print("Bienvenido a la aplicación de inventario de archivos de Google Drive")

    try:
        # Autenticación con Google Drive
        credentials_file = 'app/token.json'
        drive_service = db.authenticate(credentials_file)

        # Conexión con la base de datos
        host = "localhost"  # input("Por favor, ingresa el host de la base de datos MySQL: ")
        username = "root"  # input("Por favor, ingresa el nombre de usuario de la base de datos MySQL: ")
        password = "root"  # input("Por favor, ingresa la contraseña de la base de datos MySQL: ")
        database = "drive_inventory_db"
        conn = db.connect_db(host, username, password, database)
        db.create_db(conn)

        # Menú de opciones
        while True:
            print("\nOpciones disponibles:")
            print("1. Listar archivos en Google Drive")
            print("2. Actualizar archivos de Drive en la base de datos")
            print("3. Cambiar visibilidad de archivos y enviar notificaciones")
            print("4. Salir")

            option = input("Por favor, elige una opción: ")

            if option == "1":
                db.list_files_from_db(conn)
            elif option == "2":
                db.save_files(drive_service, conn)
            elif option == "3":
                email.process_public_files(conn)
            elif option == "4":
                print("Saliendo de la aplicación...")
                break
            else:
                print("Opción no válida. Por favor, elige una opción válida.")

    except Exception as e:
        print("Error:", str(e))

    finally:
        # Cierre de la conexión con la base de datos al salir
        if 'conn' in locals() and conn.is_connected():
            conn.close()


if __name__ == '__main__':
    main()

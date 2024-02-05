import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import mysql.connector
from app import db
from app import email
from interface import windows
import tkinter as tk
from tkinter import messagebox


def main():
    #print("Bienvenido a la aplicación de inventario de archivos de Google Drive")

    #try:
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
        def handle_listar_archivos():
           windows.show_files(drive_service)


        def handle_actualizar_archivos():
            try:
                db.save_files(drive_service, conn)
                db.save_public_files_history(conn)
                messagebox.showinfo("Actualizar archivos", "Archivos actualizados con éxito")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error al actualizar los archivos: {str(e)}")

        def handle_cambiar_visibilidad():
            db.save_public_files_history(conn)
            windows.change_visibility(conn)

        def handle_listar_publicos():
            windows.show_public_files(conn)


        # Crear la ventana principal
        root = tk.Tk()
        root.title("Inventario de archivos de Google Drive")
        root.geometry("600x400")

        # Crear botones para las diferentes opciones
        btn_listar = tk.Button(root, text="Listar archivos", command=handle_listar_archivos)
        btn_listar.pack(pady=5)

        btn_actualizar = tk.Button(root, text="Actualizar archivos", command=handle_actualizar_archivos)
        btn_actualizar.pack(pady=5)

        btn_visibilidad = tk.Button(root, text="Cambiar visibilidad", command=handle_cambiar_visibilidad)
        btn_visibilidad.pack(pady=5)

        btn_publicos = tk.Button(root, text="Historial de archivos publicos", command=handle_listar_publicos)
        btn_publicos.pack(pady=5)

        btn_salir = tk.Button(root, text="Salir", command=root.quit)
        btn_salir.pack(pady=5)

        root.mainloop()

    #except Exception as e:
    #    print("Error:", str(e))

   # finally:
        # Cierre de la conexión con la base de datos al salir
   #     if 'conn' in locals() and conn.is_connected():
   #         conn.close()


if __name__ == '__main__':
    main()

from app import db, drive
from interface import windows
import tkinter as tk
from tests import test_files


def main():

    drive_service = drive.drive_service()


    # Conexión con la base de datos
    host = "localhost"  # input("Por favor, ingresa el host de la base de datos MySQL: ")
    username = "root"  # input("Por favor, ingresa el nombre de usuario de la base de datos MySQL: ")
    password = "root"  # input("Por favor, ingresa la contraseña de la base de datos MySQL: ")
    database = "drive_inventory_db"
    conn = db.connect_db(host, username, password, database)

    # Crear database
    db.create_db(conn, drive_service)

    # Crear archivos de prueba
    test_files.create_files(drive_service)

    # Sincronizar base de datos con Drive
    db.sync_db(drive_service, conn)

    # Guardar archivos publicos
    db.save_public_files_history(conn)

    # Menú de opciones
    def handle_listar_archivos():
        windows.show_files(conn,drive_service)

    def handle_actualizar_archivos():
        db.sync_db(drive_service, conn)

    def handle_cambiar_visibilidad():
        db.save_public_files_history(conn)
        windows.change_visibility(drive_service, conn)

    def handle_listar_publicos():
        db.save_public_files_history(conn)
        windows.show_public_files(conn)

    # Crear la ventana principal
    root = tk.Tk()
    root.title("Inventario de archivos de Google Drive")
    root.geometry("600x400")

    # Crear botones para las diferentes opciones
    btn_listar = tk.Button(root, text="Listar archivos", command=handle_listar_archivos)
    btn_listar.pack(pady=5)

    btn_actualizar = tk.Button(root, text="Sincronizar archivos", command=handle_actualizar_archivos)
    btn_actualizar.pack(pady=5)

    btn_visibilidad = tk.Button(root, text="Cambiar visibilidad a privado", command=handle_cambiar_visibilidad)
    btn_visibilidad.pack(pady=5)

    btn_publicos = tk.Button(root, text="Historial de archivos publicos", command=handle_listar_publicos)
    btn_publicos.pack(pady=5)

    btn_salir = tk.Button(root, text="Salir", command=root.quit)
    btn_salir.pack(pady=5)

    root.mainloop()


if __name__ == '__main__':
    main()

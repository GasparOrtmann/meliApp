import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from app import db


def show_files(conn):
    files = db.list_files_from_db(conn)
    if files:
        window_files = tk.Toplevel()
        window_files.title("Archivos en Google Drive")
        window_files.geometry("1000x400")  # Establecer tamaño inicial de la ventana

        # Crear un Frame contenedor
        frame = ttk.Frame(window_files)
        frame.pack(fill=tk.BOTH, expand=True)

        # Crear un treeview para mostrar los archivos
        tree = ttk.Treeview(frame, columns=("Nombre", "Propietario", "Visibilidad", "Última Modificación"))

        # Agregar scrollbars
        y_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        x_scrollbar.pack(side="bottom", fill="x")

        tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        tree.pack(fill=tk.BOTH, expand=True)

        # Definir encabezados de columnas
        tree.heading("#0", text="ID")
        tree.heading("Nombre", text="Nombre")
        tree.heading("Propietario", text="Propietario")
        tree.heading("Visibilidad", text="Visibilidad")
        tree.heading("Última Modificación", text="Última Modificación")

        # Definir anchuras de columnas
        tree.column("#0", width=350)
        tree.column("Nombre", width=200)
        tree.column("Propietario", width=150)
        tree.column("Visibilidad", width=100)
        tree.column("Última Modificación", width=200)

        # Insertar datos en el treeview
        for file in files:
            tree.insert("", tk.END, text=file["id"], values=(
                file["name"],
                file["owner"],
                file["visibility"],
                file["last_modified"]
            ))

    else:
        messagebox.showinfo("Listar archivos", "No se encontraron archivos en Google Drive")


def show_public_files(conn):
    files = db.list_public_files_history(conn)
    if files:
        # Crear una nueva ventana para mostrar los archivos públicos
        window_files = tk.Toplevel()
        window_files.title("Archivos Públicos en Google Drive")
        window_files.geometry("1000x400")  # Establecer tamaño inicial de la ventana

        # Crear un Frame contenedor
        frame = ttk.Frame(window_files)
        frame.pack(fill=tk.BOTH, expand=True)

        # Crear un Treeview para mostrar los archivos
        tree = ttk.Treeview(frame, columns=("Nombre", "Propietario", "Visibilidad", "Última Modificación"))

        # Agregar scrollbars
        y_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        x_scrollbar.pack(side="bottom", fill="x")

        tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        tree.pack(fill=tk.BOTH, expand=True)

        # Definir encabezados de columnas
        tree.heading("#0", text="ID")
        tree.heading("Nombre", text="Nombre")
        tree.heading("Propietario", text="Propietario")
        tree.heading("Visibilidad", text="Visibilidad")
        tree.heading("Última Modificación", text="Última Modificación")

        # Definir anchuras de columnas
        tree.column("#0", width=350)
        tree.column("Nombre", width=200)
        tree.column("Propietario", width=150)
        tree.column("Visibilidad", width=100)
        tree.column("Última Modificación", width=200)

        # Insertar datos en el treeview
        for file in files:
            tree.insert("", tk.END, text=file["id"], values=(
                file["name"],
                file["owner"],
                file["visibility"],
                file["last_modified"]
            ))

    else:
        tk.messagebox.showinfo("Listar archivos", "No se encontraron archivos públicos en Google Drive")
def change_visibility(conn):
    files = db.list_files_from_db(conn)
    if files:
        window_files = tk.Toplevel()
        window_files.title("Archivos en Google Drive")
        window_files.geometry("800x400")  # Establecer tamaño inicial de la ventana

        # Crear un Frame contenedor
        frame = ttk.Frame(window_files)
        frame.pack(fill=tk.BOTH, expand=True)

        # Crear un treeview para mostrar los archivos con opción de selección
        tree = ttk.Treeview(frame, columns=("Nombre", "Propietario", "Visibilidad", "Última Modificación"),
                            selectmode="browse")

        # Encabezados de las columnas
        tree.heading("#0", text="ID")
        tree.column("#0", width=100, stretch=tk.NO)
        tree.heading("Nombre", text="Nombre")
        tree.column("Nombre", width=200, anchor=tk.W, stretch=tk.YES)
        tree.heading("Propietario", text="Propietario")
        tree.column("Propietario", width=150, anchor=tk.W, stretch=tk.YES)
        tree.heading("Visibilidad", text="Visibilidad")
        tree.column("Visibilidad", width=100, anchor=tk.W, stretch=tk.YES)
        tree.heading("Última Modificación", text="Última Modificación")
        tree.column("Última Modificación", width=150, anchor=tk.W, stretch=tk.YES)

        for file in files:
            tree.insert("", "end", text=file['id'],
                        values=(file['name'], file['owner'], file['visibility'], file['last_modified']))

        tree.pack(fill=tk.BOTH, expand=True)

        # Definir evento de doble clic
        def on_double_click(event):
            item = tree.selection()[0]
            selected_file_id = tree.item(item, "text")
            selected_file_name = tree.item(item, "values")[0]
            print("Doble clic en archivo:", selected_file_id, selected_file_name)

            # Cambiar la visibilidad del archivo seleccionado a privado en la base de datos
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE files SET visibility = 'private' WHERE id = %s", (selected_file_id,))
                conn.commit()
                print(f"Visibilidad del archivo '{selected_file_name}' cambiada a privado.")
                cursor.close()

                # Actualizar la lista después del cambio
                window_files.destroy()  # Cerrar la ventana actual
                show_files(conn)  # Mostrar la lista actualizada
            except Exception as e:
                print("Error al cambiar la visibilidad del archivo:", e)
                conn.rollback()

        tree.bind("<Double-1>", on_double_click)

    else:
        tk.messagebox.showinfo("Listar archivos", "No se encontraron archivos en Google Drive")
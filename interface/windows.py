import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from app import db


def show_files(service):
    # Obtener archivos y carpetas de Google Drive
    files = db.list_files_from_google_drive(service)

    if not files:
        messagebox.showinfo("Listar archivos", "No se encontraron archivos en Google Drive")
        return  # Salir de la función si no hay archivos

    # Crear la ventana y el árbol solo si hay archivos
    window_files = tk.Toplevel()
    window_files.title("Archivos en Google Drive")
    window_files.geometry("1000x400")  # Establecer tamaño inicial de la ventana

    # Crear un Frame contenedor
    frame = ttk.Frame(window_files)
    frame.pack(fill=tk.BOTH, expand=True)

    # Crear un treeview para mostrar los archivos
    tree = ttk.Treeview(frame, columns=("Nombre", "Extensión", "Propietario", "Visibilidad", "Última Modificación"))

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
    tree.heading("Extensión", text="Extensión")
    tree.heading("Propietario", text="Propietario")
    tree.heading("Visibilidad", text="Visibilidad")
    tree.heading("Última Modificación", text="Última Modificación")

    # Definir anchuras de columnas
    tree.column("#0", width=350)
    tree.column("Nombre", width=200)
    tree.column("Extensión", width=100)  # Ancho ajustable según la extensión
    tree.column("Propietario", width=150)
    tree.column("Visibilidad", width=100)
    tree.column("Última Modificación", width=200)

    # Insertar archivos en el treeview
    for file in files:
        if file.get("is_directory"):
            directory_id = file["id"]
            directory_node = tree.insert("", tk.END, text=file["id"], values=(
                file["name"],
                "",  # No se muestra la extensión para los directorios
                file["owners"],
                file["visibility"],
                file["modifiedTime"]
            ), open=False)
        else:
            # Obtener la extensión del archivo si está disponible
            extension = file["mimeType"].split(".")[-1] if "." in file["mimeType"] else ""
            tree.insert("", tk.END, text=file["id"], values=(
                file["name"],
                extension,
                file["owners"],
                file.get("visibility", "Desconocido"),
                file.get("modifiedTime", "Desconocida")
            ))

    # Asignar evento de doble clic para mostrar el contenido del directorio
    # tree.bind("<Double-1>", lambda event: show_directory_contents(event, tree, service))


def show_directory_contents(event, tree, service):
    # Obtener la fila seleccionada
    selected_items = tree.selection()

    # Verificar si hay elementos seleccionados
    if selected_items:
        # Obtener el ID del directorio seleccionado
        directory_id = selected_items[0]  # Seleccionar el primer elemento si hay múltiples selecciones

        # Verificar si el directorio seleccionado existe en el árbol
        if tree.exists(directory_id):
            # Limpiar el contenido actual del árbol en caso de que ya esté mostrando algo
            for item in tree.get_children():
                tree.delete(item)

            # Obtener el contenido del directorio utilizando la API de Google Drive o desde la base de datos, según sea necesario
            directory_contents = list_directory_contents(service, directory_id)

            # Insertar los archivos y carpetas en el treeview
            if directory_contents:
                for item in directory_contents:
                    if item.get("is_directory"):
                        subdirectory_id = item["id"]
                        subdirectory_node = tree.insert(directory_id, tk.END, text=item["id"], values=(
                            item["name"],
                            item["owner"],
                            item["visibility"],
                            item["modifiedTime"]
                        ), open=False)
                    else:
                        tree.insert(directory_id, tk.END, text=item["id"], values=(
                            item["name"],
                            item["owner"],
                            item["visibility"],
                            item["modifiedTime"]
                        ))
            else:
                messagebox.showinfo("Contenido del directorio", "El directorio está vacío o no se pudo cargar.")
        else:
            messagebox.showwarning("Error de selección",
                                   f"El elemento seleccionado {directory_id} no existe en el árbol.")
    else:
        # No se seleccionó ningún elemento, mostrar un mensaje de advertencia
        messagebox.showwarning("Error de selección", "No se ha seleccionado ningún directorio.")


def list_directory_contents(service, directory_id):
    try:
        # Llama a la API de Google Drive para obtener los archivos y carpetas dentro del directorio
        results = service.files().list(q=f"'{directory_id}' in parents",
                                       fields="files(id, name, mimeType, owners, webViewLink, modifiedTime)").execute()
        items = results.get('files', [])
        directory_contents = []

        # Procesar los resultados y agregarlos a la lista directory_contents
        for item in items:
            file_info = {
                'id': item['id'],
                'name': item['name'],
                'is_directory': item['mimeType'] == 'application/vnd.google-apps.folder',
                'owner': item.get('owners', [{'displayName': 'Propietario_Desconocido'}])[0]['displayName'],
                'visibility': 'público' if 'anyoneWithLink' in item.get('webViewLink', '') else 'privado',
                'last_modified': item.get('modifiedTime', 'Desconocida')
            }
            directory_contents.append(file_info)

        return directory_contents

    except Exception as e:
        print("Error al listar el contenido del directorio:", e)
        return []


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
        tree = ttk.Treeview(frame, columns=("Nombre", "Extensión", "Propietario", "Visibilidad", "Última Modificación"))

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
        tree.heading("Extensión", text="Extensión")
        tree.heading("Propietario", text="Propietario")
        tree.heading("Visibilidad", text="Visibilidad")
        tree.heading("Última Modificación", text="Última Modificación")

        # Definir anchuras de columnas
        tree.column("#0", width=350)
        tree.column("Nombre", width=200)
        tree.column("Extensión", width=100)  # Ancho ajustable según la extensión
        tree.column("Propietario", width=150)
        tree.column("Visibilidad", width=100)
        tree.column("Última Modificación", width=200)

    if files:
        for file in files:
            print(file)
            # Obtener la extensión del archivo si está disponible
            extension = file["extension"].split(".")[-1] if "." in file["extension"] else ""
            tree.insert("", tk.END, text=file["id"], values=(
                file["name"],
                extension,
                file["owner"],
                file.get("visibility", "Desconocido"),
                file.get("last_modified", "Desconocida")
            ))

    else:
        tk.messagebox.showinfo("Listar archivos", "No se encontraron archivos públicos en Google Drive")


def change_visibility(service):
    try:
        # Obtener archivos y carpetas de Google Drive
        files = db.list_files_from_google_drive(service)

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
                            values=(file['name'], file['owners'], file['visibility'], file['modifiedTime']))

            tree.pack(fill=tk.BOTH, expand=True)

            # Definir evento de doble clic
            def on_double_click(event):
                item = tree.selection()[0]
                selected_file_id = tree.item(item, "text")
                selected_file_name = tree.item(item, "values")[0]
                print("Doble clic en archivo:", selected_file_id, selected_file_name)

                # Cambiar la visibilidad del archivo seleccionado a privado en Google Drive
                try:
                    # Obtener el archivo seleccionado
                    selected_file = next((f for f in files if f['id'] == selected_file_id), None)
                    if selected_file:
                        # Verificar si la visibilidad actual es pública
                        if selected_file['visibility'] == 'public':
                            # Cambiar la visibilidad del archivo a privado
                            selected_file['visibility'] = 'private'

                            # Actualizar la visibilidad del archivo en Google Drive
                            updated_file = service.files().update(
                                fileId=selected_file_id,
                                body={'visibility': 'private'},
                                fields='id'
                            ).execute()

                            # Verificar si la actualización fue exitosa
                            if updated_file.get('id') == selected_file_id:
                                print(f"Visibilidad del archivo '{selected_file_name}' cambiada a privado.")
                                # Actualizar la lista después del cambio
                                window_files.destroy()  # Cerrar la ventana actual
                                change_visibility(service)  # Mostrar la lista actualizada
                            else:
                                print(f"Error al cambiar la visibilidad del archivo '{selected_file_name}'.")

                except Exception as e:
                    print("Error al cambiar la visibilidad del archivo:", e)

            tree.bind("<Double-1>", on_double_click)

        else:
            tk.messagebox.showinfo("Listar archivos", "No se encontraron archivos en Google Drive")

    except Exception as e:
        print("Error al obtener archivos desde Google Drive:", e)


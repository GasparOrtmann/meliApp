import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from app import db


def show_files(service):
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

    # Obtener archivos y carpetas de Google Drive
    files = db.list_files_from_google_drive(service)
    print("ARCHIVOS:",files)
    if files:
        for file in files:
            if file.get("is_directory"):
                directory_id = file["id"]
                directory_node = tree.insert("", tk.END, text=file["id"], values=(
                    file["name"],
                    file["owners"],
                    file["visibility"],
                    file["modifiedTime"]
                ), open=False)
                # Agregar evento para mostrar el contenido del directorio al hacer clic
                tree.bind("<ButtonRelease-1>",
                          lambda event, directory=directory_id: show_directory_contents(event, directory, tree,
                                                                                        service))

            # Insertar en el treeview con visibilidad predeterminada en caso de que no esté presente en el diccionario

            tree.insert("", tk.END, text=file["id"], values=(

                file["name"],

                file["owners"],

                # Acceder a la visibilidad utilizando get() con un valor predeterminado
                file.get("visibility", "Desconocido"),

                file.get("modifiedTime", "Desconocida")  # Manejo de la modificación del tiempo

            ))


    else:
        messagebox.showinfo("Listar archivos", "No se encontraron archivos en Google Drive")


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


def show_directory_contents(event, directory_id, tree, service):
    # Limpiar el contenido actual del árbol en caso de que ya esté mostrando algo
    for item in tree.get_children():
        tree.delete(item)

    # Obtener el contenido del directorio utilizando la API de Google Drive o desde la base de datos, según sea necesario
    # Por ejemplo, podrías llamar a una función como list_directory_contents(directory_id)

    # Supongamos que list_directory_contents es una función que devuelve una lista de archivos y carpetas dentro del directorio
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
                    item["last_modified"]
                ), open=False)
                # Agregar evento para mostrar el contenido del subdirectorio al hacer clic
                tree.bind("<ButtonRelease-1>",
                          lambda event, subdirectoryid=subdirectory_id: show_directory_contents(event, subdirectoryid,
                                                                                                tree))
            else:
                tree.insert(directory_id, tk.END, text=item["id"], values=(
                    item["name"],
                    item["owner"],
                    item["visibility"],
                    item["last_modified"]
                ))
    else:
        messagebox.showinfo("Contenido del directorio", "El directorio está vacío o no se pudo cargar.")


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

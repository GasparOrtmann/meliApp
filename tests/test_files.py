def create_files(service):
    test_files = [
        {
            'name': 'Document_Public.txt',
            'mimeType': 'text/plain',
            'visibility': 'public'
        },
        {
            'name': 'Document_Private.txt',
            'mimeType': 'text/plain',
            'visibility': 'private'
        },
        {
            'name': 'Spreadsheet_Public.csv',
            'mimeType': 'text/csv',
            'visibility': 'public'
        },
        {
            'name': 'Spreadsheet_Private.csv',
            'mimeType': 'text/csv',
            'visibility': 'private'
        },
        {
            'name': 'Presentation_Public.pptx',
            'mimeType': 'application/vnd.google-apps.presentation',
            'visibility': 'public'
        },
        {
            'name': 'Presentation_Private.pptx',
            'mimeType': 'application/vnd.google-apps.presentation',
            'visibility': 'private'
        },
        {
            'name': 'Image_Public.jpg',
            'mimeType': 'image/jpeg',
            'visibility': 'public'
        },
        {
            'name': 'Image_Private.jpg',
            'mimeType': 'image/jpeg',
            'visibility': 'private'
        }
    ]

    for file_data in test_files:
        file_name = file_data['name']

        # Verificar si el archivo ya existe
        files = service.files().list(q=f"name='{file_name}'").execute().get('files', [])

        if not files:
            file_metadata = {
                'name': file_name,
                'mimeType': file_data['mimeType']
            }

            # Establecer la visibilidad
            if file_data['visibility'] == 'public':
                file_metadata['visibility'] = 'public'
            else:
                file_metadata['visibility'] = 'private'

            # Crear el archivo
            file = service.files().create(body=file_metadata, fields='id').execute()
            print(f"Test file created: {file_name} (ID: {file.get('id')})")
        else:
            print(f"El archivo {file_name} ya existe, no se ha creado.")

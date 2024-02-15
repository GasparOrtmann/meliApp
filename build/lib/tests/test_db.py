import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import mysql.connector
import pytest
from app import db


@pytest.fixture
def mock_detect_visibility():
    return MagicMock()


class TestGoogleDriveFunctions(unittest.TestCase):

    @patch('mysql.connector.connect')
    def test_connect_db_success(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        host = 'localhost'
        username = 'test_user'
        password = 'test_password'
        database = 'test_db'

        conn = db.connect_db(host, username, password, database)
        self.assertEqual(conn, mock_conn)

    @patch('mysql.connector.connect')
    def test_connect_db_failure(self, mock_connect):
        mock_connect.side_effect = mysql.connector.Error()

        host = 'localhost'
        username = 'test_user'
        password = 'test_password'
        database = 'test_db'

        conn = db.connect_db(host, username, password, database)
        self.assertIsNone(conn)

    @patch('mysql.connector.connect')
    def test_clean_google_drive(self, mock_connect):
        service_mock = MagicMock()
        service_mock.files().list().execute.return_value = {'files': [{'id': '123', 'name': 'file1.txt'}]}

        db.clean_google_drive(service_mock)

        service_mock.files().delete.assert_called_once_with(fileId='123')

    @patch('detect_visibility')
    def test_list_files_from_google_drive(self, mock_detect_visibility):
        # Configura el mock del servicio de Google Drive
        service_mock = MagicMock()
        files_list_mock = MagicMock()
        files_list_mock.execute.return_value = {
            'files': [
                {'id': '123', 'name': 'archivo1.txt', 'mimeType': 'texto/plain',
                 'owners': [{'displayName': 'Propietario1'}], 'modifiedTime': '2024-01-01'},
                {'id': '456', 'name': 'archivo2.pdf', 'mimeType': 'application/pdf',
                 'owners': [{'displayName': 'Propietario2'}], 'modifiedTime': '2024-01-02'}
            ]
        }
        service_mock.files.return_value.list.return_value = files_list_mock

        # Configura el mock de detect_visibility para devolver "privado" para todos los archivos
        mock_detect_visibility.return_value = "privado"

        # Llama a la función que quieres probar
        result = db.list_files_from_google_drive(service_mock)

        # Verifica que la función devuelve la lista de archivos esperada
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'archivo1.txt')
        self.assertEqual(result[1]['name'], 'archivo2.pdf')

        # Verifica que detect_visibility se haya llamado una vez por cada archivo
        self.assertEqual(mock_detect_visibility.call_count, 2)

    @patch('mysql.connector.connect')
    def test_get_files(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = [{'id': '123', 'name': 'file1.txt'}]

        result = db.get_files(mock_conn)
        self.assertEqual(len(result), 1)

    @patch('mysql.connector.connect')
    def test_list_public_files_history(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = [{'id': '123', 'name': 'file1.txt'}]

        result = db.list_public_files_history(mock_conn)
        self.assertEqual(len(result), 1)

    @patch('db.list_files_from_google_drive')
    def test_sync_db(self, mock_list_files_from_google_drive):
        # Creamos un mock para la conexión a la base de datos
        mock_conn = MagicMock()

        # Creamos un mock para el servicio de Google Drive
        mock_service = MagicMock()

        # Configuramos el mock para que devuelva algunos archivos ficticios
        mock_list_files_from_google_drive.return_value = [
            {'id': '123', 'name': 'file1.txt', 'mimeType': 'text/plain', 'owners': 'owner1@example.com',
             'modifiedTime': '2024-01-31T12:00:00Z'},
            {'id': '456', 'name': 'file2.jpg', 'mimeType': 'image/jpeg', 'owners': 'owner2@example.com',
             'modifiedTime': '2024-01-31T12:30:00Z'}
        ]

        # Ejecutamos la función que queremos probar
        db.sync_db(mock_service, mock_conn)

        # Verificamos que la función haya interactuado correctamente con la base de datos
        mock_conn.cursor.return_value.execute.assert_called()  # Verifica que se haya llamado a execute en el cursor

    @patch('mysql.connector.connect')
    def test_detect_visibility(self, mock_connect):
        service_mock = MagicMock()
        service_mock.permissions().list().execute.return_value = {'permissions': [{'role': 'reader'}]}

        visibility = db.detect_visibility(service_mock, '123')
        self.assertEqual(visibility, 'public')

    @patch('mysql.connector.connect')
    def test_change_file_visibility(self, mock_connect):
        service_mock = MagicMock()
        service_mock.permissions().list().execute.return_value = {'permissions': [{'type': 'anyone', 'role': 'reader',
                                                                                   'id': '456'}]}

        db.change_file_visibility(service_mock, '123')

        service_mock.permissions().delete.assert_called_once_with(fileId='123', permissionId='456')

    @patch('mysql.connector.connect')
    def test_save_public_files_history(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = [{'id': '123', 'name': 'file1.txt', 'extension': 'txt',
                                              'owner': 'user@example.com', 'visibility': 'public',
                                              'last_modified': datetime.now()}]

        db.save_public_files_history(mock_conn)

        self.assertEqual(mock_cursor.execute.call_count, 2)

    @patch('mysql.connector.connect')
    def test_get_file_owner(self, mock_connect):
        service_mock = MagicMock()
        service_mock.files().get().execute.return_value = {'owners': [{'emailAddress': 'user@example.com'}]}

        owner = db.get_file_owner(service_mock, '123')
        self.assertEqual(owner, 'user@example.com')


if __name__ == "__main__":
    unittest.main()

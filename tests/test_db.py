import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import mysql.connector
import pytest
from app import db


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

    @patch('mysql.connector.connect')
    def test_get_files(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = [{'id': '123', 'name': 'file1.txt'}]

        result = db.get_files(mock_conn)
        self.assertEqual(len(result), 1)

    @patch('mysql.connector.connect')
    def test_list_public_files_history(self, mock_connect):
        # Mock de la conexión a la base de datos
        mock_cursor = mock_connect.return_value.cursor.return_value
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'file1', 'extension': 'txt', 'owner': 'user1', 'visibility': 'public',
             'last_modified': '2024-01-31'},
            {'id': 2, 'name': 'file2', 'extension': 'pdf', 'owner': 'user2', 'visibility': 'public',
             'last_modified': '2024-01-30'}
        ]

        # Llamada a la función a probar
        result = db.list_public_files_history(mock_connect)

        # Impresion de archivos
        mock_cursor.execute.assert_called_once_with("SELECT * FROM public_files_history")
        self.assertEqual(mock_cursor.close.call_count, 1)  # Verifica que el cursor se cierre correctamente

        # Salida de la funcion
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'file1')
        self.assertEqual(result[1]['name'], 'file2')

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

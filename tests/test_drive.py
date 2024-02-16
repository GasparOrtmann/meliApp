from unittest.mock import patch
import unittest
from app import drive


class TestDriveService(unittest.TestCase):

    @patch('drive.service_account.Credentials.from_service_account_file')
    @patch('drive.build')
    def test_drive_service(self, mock_build, mock_from_service_account_file):
        # Configura los mocks
        mock_credentials = mock_from_service_account_file.return_value
        mock_service = mock_build.return_value

        # Llamo al google drive service
        result = drive.drive_service()

        # Verifico que se llamen los datos necesarios
        mock_from_service_account_file.assert_called_once_with(
            'app/credentials.json',
            scopes=['https://www.googleapis.com/auth/drive']
        )
        mock_build.assert_called_once_with('drive', 'v3', credentials=mock_credentials)

        # Return de la funcion
        self.assertEqual(result, mock_service)


if __name__ == '__main__':
    unittest.main()

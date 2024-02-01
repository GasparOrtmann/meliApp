import unittest

from app import db


class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Establecemos una conexión temporal a la base de datos en memoria para los tests
        self.conn = db.connect_db('localhost', 'root', 'root', 'meli_test')


if __name__ == '__main__':
    unittest.main()

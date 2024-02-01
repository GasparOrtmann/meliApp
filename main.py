
from app import db



def main():
    conn = db.connect_db('localhost', 'root', 'root', 'meli_test')
    db.create_db()


if __name__ == '__main__':
    main()



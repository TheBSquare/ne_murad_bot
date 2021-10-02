from sqlite3 import connect
from database_handler.singleton_meta import SingletonMeta
from uuid import uuid4
from settings import root_path
import os


class Db(metaclass=SingletonMeta):
    database = os.path.join(root_path, "taxi_orders.db")

    connections = {}

    connection = connect(database)

    cursor = connection.cursor()

    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS
        taxi_orders (
            number INT, 
            pickup_address TEXT,
            destination_address TEXT,
            license_plate TEXT,
            create_date INT,
            expired BOOL
        )
        """
    )

    cursor.execute(
        f"""
            CREATE TABLE IF NOT EXISTS
            users (
                number INT, 
                rule TEXT,
                taxi_number TEXT    
            )
            """
    )

    connection.commit()

    def get_not_expired_orders(self, token):
        connection = self.connections[token]
        cursor = connection.cursor()
        sql = "SELECT * FROM taxi_orders WHERE expired = 0"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        return data

    def get_orders(self, token):
        connection = self.connections[token]
        cursor = connection.cursor()
        sql = "SELECT * FROM taxi_orders"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        return data

    def mark_order(self, token, order_id):
        connection = self.connections[token]
        cursor = connection.cursor()
        sql = "UPDATE taxi_orders SET expired=1 WHERE number=?"
        cursor.execute(sql, (order_id, ))
        cursor.close()

    def delete_user(self, token, chat_id):
        connection = self.connections[token]
        cursor = connection.cursor()
        sql = "DELETE FROM users where number=?"
        cursor.execute(sql, (chat_id, ))
        cursor.close()

    def get_users(self, token):
        connection = self.connections[token]
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users")
        users = {row[0]: {"rule": row[1], "taxi_id": row[2], "is_thread": False} for row in cursor.fetchall()}
        cursor.close()
        return users

    def add_user(self, token, chat_id, rule, taxi_id):
        connection = self.connections[token]
        cursor = connection.cursor()

        sql = f"INSERT INTO users (number, rule, taxi_number) VALUES (?, ?, ?)"

        cursor.execute(sql, (chat_id, rule, taxi_id))

        cursor.close()

    def get_order_by_id(self, token, order_id):
        connection = self.connections[token]
        cursor = connection.cursor()

        sql = f"SELECT * FROM taxi_orders WHERE number = ?"

        cursor.execute(sql, (order_id, ))

        data = cursor.fetchone()

        cursor.close()

        return data

    def add_order(self, token, data):
        connection = self.connections[token]
        cursor = connection.cursor()

        sql = f"""
            INSERT INTO taxi_orders
            (license_plate, number, create_date, pickup_address, destination_address, expired)
            VALUES (?, ?, ?, ?, ?, 0);
        """

        cursor.execute(
            sql, data
        )

        cursor.close()

    def commit_connection(self, token):
        connection = self.connections[token]
        connection.commit()

    def create_connection(self):
        token = uuid4()
        self.connections[token] = connect(self.database)
        return token

    def close_connection(self, token):
        self.connections[token].close()
        del self.connections[token]


def load():
    db = Db()
    tk = db.create_connection()
    db.close_connection(tk)

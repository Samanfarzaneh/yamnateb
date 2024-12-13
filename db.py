import json
import mysql.connector

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            # خواندن فایل پیکربندی
            with open("config.json", "r") as config_file:
                config = json.load(config_file)

            DB_CONFIG = config["database"]

            # اتصال به پایگاه داده
            try:
                db_connection = mysql.connector.connect(
                    host=DB_CONFIG["host"],
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    database=DB_CONFIG["database"]
                )
                cls._instance = db_connection
                cls._cursor = db_connection.cursor()
            except mysql.connector.Error as err:
                print(f"خطا در اتصال به پایگاه داده: {err}")
                exit()

        return cls._instance

    @classmethod
    def get_cursor(cls):
        return cls._cursor

    @classmethod
    def close(cls):
        if cls._cursor:
            cls._cursor.close()
        if cls._instance:
            cls._instance.close()

# استفاده از Singleton


db_connection = DatabaseConnection()
single_db_cursor = DatabaseConnection.get_cursor()

# پس از اتمام کار
DatabaseConnection.close()

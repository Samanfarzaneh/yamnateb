# db.py

import mysql.connector
import json

# بارگذاری تنظیمات دیتابیس از فایل config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)

DB_CONFIG = config["database"]

# اتصال به پایگاه داده
def get_db_connection():
    try:
        db_connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        return db_connection
    except mysql.connector.Error as err:
        print(f"خطا در اتصال به پایگاه داده: {err}")
        return None

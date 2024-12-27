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

# مثال استفاده از اتصال و کرسر
def execute_query(query, params=None):
    db_connection = get_db_connection()
    if db_connection:
        try:
            # ایجاد کرسر و استفاده از with برای مدیریت خودکار
            with db_connection.cursor() as cursor:
                cursor.execute(query, params or ())
                db_connection.commit()
                return cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"خطا در اجرای کوئری: {err}")
        finally:
            db_connection.close()  # بستن اتصال به پایگاه داده
    else:
        print("اتصال به پایگاه داده برقرار نشد.")
        return None

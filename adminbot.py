import mysql.connector
import time
import requests
from telegram import Bot
import json
import sys  # برای خارج کردن برنامه در صورت خطا در اتصال

# 🛠️ بارگذاری پیکربندی از فایل config.json
try:
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
except Exception as e:
    print(f"⚠️ خطا در خواندن فایل config.json: {e}")
    sys.exit(1)  # پایان برنامه

DB_CONFIG = config["database"]
BOT2_TOKEN = config["admin_bot_token"]  # توکن از فایل پیکربندی خوانده می‌شود
CHANNEL_ID = config["channel_id"]  # شناسه کانال از فایل پیکربندی خوانده می‌شود

# 🛠️ اتصال به MySQL (اتصال در ابتدای برنامه فقط یک‌بار انجام می‌شود)
try:
    db_connection = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )
    db_cursor = db_connection.cursor()
    print("✅ اتصال به MySQL برقرار شد.")
except mysql.connector.Error as e:
    print(f"❌ خطا در اتصال به MySQL: {e}")
    sys.exit(1)  # پایان برنامه


# 🛠️ تابع ارسال پیام به کانال
def send_message_to_channel(message):
    try:
        bot = Bot(token=BOT2_TOKEN)
        bot.send_message(chat_id=CHANNEL_ID, text=message)
        print("✅ پیام به کانال ارسال شد.")
    except Exception as e:
        print(f"⚠️ خطا در ارسال پیام به کانال: {e}")


# 🛠️ تابع برای بررسی سفارشات جدید
def check_new_orders():
    try:
        # جستجو برای سفارشات جدید
        db_cursor.execute("SELECT id, order_details FROM orders WHERE status = 'new'")
        new_orders = db_cursor.fetchall()

        if new_orders:
            print(f"📦 {len(new_orders)} سفارش جدید یافت شد.")

        # ارسال پیام برای هر سفارش جدید
        for order in new_orders:
            order_id = order[0]
            order_details = order[1]

            # ارسال پیام به کانال
            send_message_to_channel(f"🛒 سفارش جدید:\n\nجزئیات: {order_details}")

            # پس از ارسال، وضعیت سفارش به "ارسال شده" تغییر می‌کند
            db_cursor.execute("UPDATE orders SET status = 'sent' WHERE id = %s", (order_id,))

        if new_orders:
            db_connection.commit()  # commit یک‌بار پس از تغییر تمام سفارشات

    except mysql.connector.Error as e:
        print(f"⚠️ خطا در اجرای دستورات MySQL: {e}")


# 🛠️ حلقه بررسی سفارشات جدید
def run_check_loop():
    try:
        while True:
            check_new_orders()  # بررسی سفارشات جدید
            time.sleep(60)  # هر 60 ثانیه یک‌بار بررسی می‌کند
    except KeyboardInterrupt:
        print("\n🛑 برنامه با دستور کاربر متوقف شد.")
    finally:
        if db_cursor:
            db_cursor.close()
        if db_connection:
            db_connection.close()
        print("📴 اتصال به MySQL بسته شد.")


if __name__ == "__main__":
    run_check_loop()  # شروع حلقه بررسی سفارشات

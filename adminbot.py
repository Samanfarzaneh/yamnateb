import sqlite3
import time
import requests
from telegram import Bot

# توکن ربات دوم و شناسه چت کانال
BOT2_TOKEN = "YOUR_BOT2_TOKEN"
CHANNEL_ID = "@your_channel_id"  # شناسه کانال یا چت ادمین

# تابع ارسال پیام به کانال
def send_message_to_channel(message):
    try:
        bot = Bot(token=BOT2_TOKEN)
        bot.send_message(chat_id=CHANNEL_ID, text=message)
        print("پیام به کانال ارسال شد.")
    except Exception as e:
        print(f"Error sending message to channel: {e}")

# تابع برای بررسی سفارشات جدید
def check_new_orders():
    # اتصال به دیتابیس
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    # جستجو برای سفارشات جدید
    cursor.execute("SELECT * FROM orders WHERE status = 'new'")  # فرض می‌کنیم که سفارشات جدید با status = 'new' مشخص می‌شوند
    new_orders = cursor.fetchall()

    # ارسال پیام برای هر سفارش جدید
    for order in new_orders:
        order_id = order[0]
        order_details = order[1]

        # ارسال پیام به کانال
        send_message_to_channel(f"🛒 سفارش جدید:\n\nجزئیات: {order_details}")

        # پس از ارسال، وضعیت سفارش به "ارسال شده" تغییر می‌کند
        cursor.execute("UPDATE orders SET status = 'sent' WHERE id = ?", (order_id,))
        conn.commit()

    conn.close()

# حلقه بررسی سفارشات جدید
def run_check_loop():
    while True:
        check_new_orders()  # بررسی سفارشات جدید
        time.sleep(60)  # هر 60 ثانیه یک‌بار بررسی می‌کند

if __name__ == "__main__":
    run_check_loop()  # شروع حلقه بررسی سفارشات

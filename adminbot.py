import json
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, CallbackQueryHandler
import mysql.connector
from adminviews import start, receive_product_name, cancel, add_product, button, receive_product_price, is_admin, \
    create_admin_menu, confirm_add_product, edit_product_view, back_to_main_menu, show_all_products, select_category

# بارگذاری توکن رباط از فایل config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)

BOT_TOKEN = config.get("admin_bot_token")
DB_CONFIG = config.get("database")

# اتصال به پایگاه داده
try:
    db_connection = mysql.connector.connect(
        host=DB_CONFIG.get("host"),
        user=DB_CONFIG.get("user"),
        password=DB_CONFIG.get("password"),
        database=DB_CONFIG.get("database")
    )
    db_cursor = db_connection.cursor()
except mysql.connector.Error as err:
    print(f"خطا در اتصال به پایگاه داده: {err}")
    exit(1)

# ایجاد برنامه رباط
application = ApplicationBuilder().token(BOT_TOKEN).build()

# تعریف وضعیت‌ها
WAITING_FOR_PRODUCT_NAME = 1
WAITING_FOR_PRODUCT_PRICE = 2
WAITING_FOR_CATEGORY_SELECTION = 3
WAITING_FOR_CONFIRMATION = 4
WAITING_FOR_EDIT_PRODUCT_NAME = 5

# دیکشنری برای ذخیره وضعیت ورود کاربر
user_login_status = {}

# تعریف ConversationHandler برای مدیریت وضعیت‌ها
conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        CallbackQueryHandler(add_product, pattern='^add_product_menu$')
    ],
    states={
        WAITING_FOR_PRODUCT_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_product_name),
        ],
        WAITING_FOR_CATEGORY_SELECTION: [
            CallbackQueryHandler(button),
        ],
        WAITING_FOR_PRODUCT_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_product_price),
        ],
        WAITING_FOR_CONFIRMATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_add_product),
        ],
        WAITING_FOR_EDIT_PRODUCT_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_view),
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    # per_message=True
)

# افزودن هندلرها به برنامه
application.add_handler(conversation_handler)

# اضافه کردن هندلرهای اضافی
application.add_handler(CommandHandler("add_product", add_product))
application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern='home_menu_handler'))
application.add_handler(CallbackQueryHandler(show_all_products, pattern="^all_products$"))
application.add_handler(CallbackQueryHandler(select_category, pattern=r"^select_category:"))

application.add_handler(CallbackQueryHandler(button))

# راه‌اندازی رباط
if __name__ == "__main__":
    try:
        print("🤖 رباط فعال شد...")
        application.run_polling()
    except Exception as e:
        print(f"خطا در اجرای رباط: {e}")

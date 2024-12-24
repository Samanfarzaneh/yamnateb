import json
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, CallbackQueryHandler
import mysql.connector
from admin.adminviews import start,add_product, button, confirm_add_product, back_to_main_menu, admin_menu_control
from admin.add_product_views import receive_product_name, receive_product_price
from admin.buttons import cancel_request
from admin.states import WAITING_FOR_PRODUCT_NAME, WAITING_FOR_PRODUCT_PRICE, WAITING_FOR_CATEGORY_SELECTION, \
    WAITING_FOR_CONFIRMATION, WAITING_FOR_SEARCH_PRODUCT
from admin.edit_product import cancel , show_all_products, select_category, \
    edit_product_by_category, start_edit_name, start_edit_price, search_product, \
    search_product_by_name, selected_product_for_edit, delete_product



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


# دیکشنری برای ذخیره وضعیت ورود کاربر
user_login_status = {}

# تعریف ConversationHandler برای مدیریت وضعیت‌ها
conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        CallbackQueryHandler(add_product, pattern='^add_product_menu$'),
        CallbackQueryHandler(search_product, pattern="search_product")
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
        WAITING_FOR_SEARCH_PRODUCT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, search_product_by_name),
        ],
        # WAITING_FOR_EDIT_PRODUCT_NAME: [
        #     MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_name),
        # ],
        # WAITING_FOR_EDIT_PRODUCT_PRICE: [
        #     MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_price),
        # ],
        # WAITING_FOR_EDIT_CATEGORY_SELECTION: [
        #     MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_category),
        # ]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

# افزودن هندلرها به برنامه
application.add_handler(conversation_handler)

# اضافه کردن هندلرهای اضافی
application.add_handler(CommandHandler("add_product", add_product))
application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern='home_menu_handler'))
application.add_handler(CallbackQueryHandler(show_all_products, pattern="^all_products$"))
application.add_handler(CallbackQueryHandler(select_category, pattern=r"^select_category:"))
application.add_handler(CallbackQueryHandler(edit_product_by_category, pattern=r"^edit_product:"))
application.add_handler(CallbackQueryHandler(start_edit_name, pattern="^edit_name:"))
application.add_handler(CallbackQueryHandler(start_edit_price, pattern="^edit_price:"))
application.add_handler(CallbackQueryHandler(admin_menu_control, pattern="admin_menu"))
application.add_handler(CallbackQueryHandler(search_product, pattern="search_product_for_edit"))
application.add_handler(CallbackQueryHandler(selected_product_for_edit, pattern=r"^add_to_cart:"))
application.add_handler(CallbackQueryHandler(delete_product, pattern=r'^delete_product_callback:'))
application.add_handler(CallbackQueryHandler(cancel_request, pattern='cancel_request'))
application.add_handler(CallbackQueryHandler(button))

# راه‌اندازی رباط
if __name__ == "__main__":
    try:
        print("🤖 رباط فعال شد...")
        application.run_polling()
    except Exception as e:
        print(f"خطا در اجرای رباط: {e}")

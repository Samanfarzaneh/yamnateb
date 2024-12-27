import json
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, CallbackQueryHandler
from admin.adminviews import start,add_product, button, confirm_add_product, back_to_main_menu, admin_menu_control
from admin.add_product_views import receive_product_name, receive_product_price
from admin.buttons import cancel_request, restart_conversation
from admin.category import add_category, receive_category, confirm_add_category
from admin.states import WAITING_FOR_PRODUCT_NAME, WAITING_FOR_PRODUCT_PRICE, WAITING_FOR_CATEGORY_SELECTION, \
    WAITING_FOR_CONFIRMATION, WAITING_FOR_SEARCH_PRODUCT, WAITING_FOR_EDIT_PRODUCT_NAME, WAITING_FOR_EDIT_PRODUCT_PRICE, \
    WAITING_FOR_CATEGORY_NAME, WAITING_FOR_CONFIRM_ADD_CATEGORY
from admin.edit_product import cancel, show_all_products, select_category, \
    edit_product_by_category, start_edit_name, start_edit_price, search_product, \
    search_product_by_name, selected_product_for_edit, delete_product, confirm_delete_product, start_edit_category, \
    select_edited_category, save_new_price, save_new_name

# بارگذاری توکن رباط از فایل config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)

BOT_TOKEN = config.get("admin_bot_token")

# ایجاد برنامه رباط
application = ApplicationBuilder().token(BOT_TOKEN).build()


# دیکشنری برای ذخیره وضعیت ورود کاربر
user_login_status = {}


# تعریف ConversationHandler برای مدیریت وضعیت‌ها
conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        CallbackQueryHandler(start_edit_name, pattern='^start_edit_name:'),
        CallbackQueryHandler(start_edit_price, pattern='^start_edit_price:'),
        CallbackQueryHandler(add_product, pattern='^add_product_menu$'),
        CallbackQueryHandler(search_product, pattern="search_product"),
        CallbackQueryHandler(add_category, pattern="add_category")
    ],
    states={
        WAITING_FOR_EDIT_PRODUCT_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_price),
            ],
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
        WAITING_FOR_EDIT_PRODUCT_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_name),
        ],
        WAITING_FOR_CONFIRM_ADD_CATEGORY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_add_category),
        ],
        WAITING_FOR_CATEGORY_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_category),
        ],
        # WAITING_FOR_EDIT_PRODUCT_PRICE: [
        #     MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_price),
        # ]
    },
    fallbacks=[CommandHandler("cancel", cancel),
               CommandHandler("restart", restart_conversation),  # افزودن هندلر restart
    ]
)

# افزودن هندلرها به برنامه
application.add_handler(conversation_handler)


# اضافه کردن هندلرهای اضافی
application.add_handler(CommandHandler("add_product", add_product))
application.add_handler(CallbackQueryHandler(cancel_request, pattern="cancel_request"))
application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern='home_menu_handler'))
application.add_handler(CallbackQueryHandler(show_all_products, pattern="^all_products$"))
application.add_handler(CallbackQueryHandler(select_category, pattern=r"^select_category:"))
application.add_handler(CallbackQueryHandler(edit_product_by_category, pattern=r"^edit_product:"))
application.add_handler(CallbackQueryHandler(start_edit_price, pattern="^start_edit_price:"))
application.add_handler(CallbackQueryHandler(start_edit_category, pattern="^start_edit_category:"))
# application.add_handler(CallbackQueryHandler(select_edited_category, pattern=r"^select_edited_category:"))
application.add_handler(CallbackQueryHandler(admin_menu_control, pattern="admin_menu"))
application.add_handler(CallbackQueryHandler(search_product, pattern="search_product_for_edit"))
# application.add_handler(CallbackQueryHandler(confirm_add_category, pattern="confirm_add_category"))
application.add_handler(CallbackQueryHandler(selected_product_for_edit, pattern=r"^selected_product_for_edit:"))
application.add_handler(CallbackQueryHandler(confirm_delete_product, pattern=r'^confirm_delete_product:'))
application.add_handler(CallbackQueryHandler(delete_product, pattern=r'^delete_product:'))
application.add_handler(CallbackQueryHandler(button))

# راه‌اندازی رباط
if __name__ == "__main__":
    try:
        print("🤖 رباط فعال شد...")
        application.run_polling()
    except Exception as e:
        print(f"خطا در اجرای رباط: {e}")

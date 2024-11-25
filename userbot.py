from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from views import show_categories, show_products_by_category, add_to_cart, show_cart, remove_from_cart, confirm_order, search_products, handle_search, increase_quantity, decrease_quantity, handle_payment_receipt
import json

with open("config.json", "r") as config_file:
    config = json.load(config_file)

BOT_TOKEN = config["bot_token"]

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # دستورات اصلی
    application.add_handler(CommandHandler("start", show_categories))
    application.add_handler(CallbackQueryHandler(show_products_by_category, pattern=r"^show_products:"))
    application.add_handler(CallbackQueryHandler(add_to_cart, pattern=r"^add_to_cart:"))
    application.add_handler(CallbackQueryHandler(show_cart, pattern="show_cart"))
    application.add_handler(CallbackQueryHandler(remove_from_cart, pattern=r"^remove_from_cart:"))
    application.add_handler(CallbackQueryHandler(confirm_order, pattern="confirm_order"))
    application.add_handler(CallbackQueryHandler(show_categories, pattern="^show_categories$"))
    application.add_handler(CallbackQueryHandler(search_products, pattern="search_products"))

    # دکمه‌های افزایش و کاهش تعداد
    application.add_handler(CallbackQueryHandler(increase_quantity, pattern=r"^increase_quantity:"))
    application.add_handler(CallbackQueryHandler(decrease_quantity, pattern=r"^decrease_quantity:"))

    # مدیریت جستجو
    application.add_handler(MessageHandler(filters.TEXT, handle_search))

    # هندلر برای دریافت عکس رسید واریز
    application.add_handler(MessageHandler(filters.PHOTO, handle_payment_receipt))

    # اجرای بوت
    application.run_polling()

if __name__ == "__main__":
    main()

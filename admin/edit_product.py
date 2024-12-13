# import json
# import mysql.connector
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
# from telegram.ext import ContextTypes, ConversationHandler
#
#
#
# WAITING_FOR_PRODUCT_NAME = 1
# WAITING_FOR_PRODUCT_PRICE = 2
# WAITING_FOR_CATEGORY_SELECTION = 3
# WAITING_FOR_CONFIRMATION = 4
#
#
# # بارگذاری کانفیگ و اتصال به پایگاه داده
# with open("config.json", "r") as config_file:
#     config = json.load(config_file)
#
# DB_CONFIG = config["database"]
#
# try:
#     db_connection = mysql.connector.connect(
#         host=DB_CONFIG["host"],
#         user=DB_CONFIG["user"],
#         password=DB_CONFIG["password"],
#         database=DB_CONFIG["database"]
#     )
#     db_cursor = db_connection.cursor()
# except mysql.connector.Error as err:
#     print(f"خطا در اتصال به پایگاه داده: {err}")
#     exit()
#
# async def receive_product_name_for_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     product_name = update.message.text
#     context.user_data['product_name'] = product_name
#
#     try:
#         db_cursor.execute("SELECT id, name, price FROM products WHERE name = %s", (product_name,))
#         product = db_cursor.fetchone()
#     except mysql.connector.Error as err:
#         print(f"خطای پایگاه داده در receive_product_name_for_edit: {err}")
#         await update.message.reply_text("❌ خطایی در دریافت محصول رخ داد.")
#         return ConversationHandler.END
#
#     if not product:
#         await update.message.reply_text("❌ محصولی با این نام یافت نشد.")
#         return ConversationHandler.END
#
#     context.user_data['product_id'] = product[0]
#     context.user_data['product_name'] = product[1]
#     context.user_data['product_price'] = product[2]
#
#     # ساخت دکمه‌ها برای دسته‌بندی‌ها
#     try:
#         db_cursor.execute("SELECT id, name FROM categories")
#         categories = db_cursor.fetchall()
#     except mysql.connector.Error as err:
#         print(f"خطای پایگاه داده در receive_product_name_for_edit: {err}")
#         await update.message.reply_text("❌ خطایی در دریافت دسته‌بندی‌ها رخ داد.")
#         return ConversationHandler.END
#
#     # نمایش جزئیات محصول و دکمه‌های ویرایش
#     keyboard = [[InlineKeyboardButton(f"{cat[1]}", callback_data=f'category_{cat[1]}')] for cat in categories ]
#     keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_name')])
#
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await update.message.reply_text(f"نام محصول: {product[1]}\nقیمت: {product[2]}\nلطفاً دسته‌بندی‌های محصول را انتخاب کنید.",
#                                     reply_markup=reply_markup)
#     return WAITING_FOR_CATEGORY_SELECTION
#
# async def receive_edited_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         product_price = float(update.message.text)
#     except ValueError:
#         await update.message.reply_text("لطفاً قیمت را به درستی وارد کنید.")
#         return WAITING_FOR_PRODUCT_PRICE
#
#     context.user_data['product_price'] = product_price
#     await update.message.reply_text(f"قیمت جدید محصول: {product_price} ثبت شد.")
#
#     product_name = context.user_data.get('product_name', 'نام وارد نشده')
#     category_names = context.user_data.get('selected_categories', [])
#     category_name = ', '.join(category_names) if category_names else 'هیچ دسته‌ای انتخاب نشده'
#
#     confirmation_message = (
#         f"✅ نام محصول: {product_name}\n"
#         f"💲 قیمت جدید: {product_price}\n"
#         f"📂 دسته‌بندی: {category_name}\n\n"
#         "آیا مطمئن هستید که می‌خواهید این تغییرات را اعمال کنید؟"
#     )
#
#     keyboard = [
#         [InlineKeyboardButton("✅ بله", callback_data='confirm_edit_product_menu')],
#         [InlineKeyboardButton("❌ خیر", callback_data='cancel_edit_product')]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#
#     await update.message.reply_text(confirmation_message, reply_markup=reply_markup)
#     return WAITING_FOR_CONFIRMATION
#
# async def confirm_edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#
#     product_id = context.user_data['product_id']
#     product_price = context.user_data['product_price']
#     selected_categories = context.user_data.get('selected_categories', [])
#
#     if not selected_categories:
#         await query.edit_message_text("❌ هیچ دسته‌بندی‌ای انتخاب نشده است.")
#         return ConversationHandler.END
#
#     try:
#         # به‌روزرسانی قیمت محصول
#         db_cursor.execute("UPDATE products SET price = %s WHERE id = %s", (product_price, product_id))
#         db_connection.commit()
#
#         # پاک کردن دسته‌بندی‌های قدیمی و افزودن دسته‌بندی‌های جدید
#         db_cursor.execute("DELETE FROM product_categories WHERE product_id = %s", (product_id,))
#         db_connection.commit()
#
#         # اضافه کردن دسته‌بندی‌های جدید
#         for category_name in selected_categories:
#             db_cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
#             category_result = db_cursor.fetchone()
#
#             if category_result:
#                 category_id = category_result[0]
#                 db_cursor.execute("INSERT INTO product_categories (product_id, category_id) VALUES (%s, %s)", (product_id, category_id))
#                 db_connection.commit()
#
#         category_names = ", ".join(selected_categories)
#         message = f"محصول \"{context.user_data['product_name']}\" با موفقیت ویرایش شد.\n" \
#                   f"قیمت جدید: {product_price}\n" \
#                   f"دسته‌بندی‌ها: {category_names}"
#
#         await query.edit_message_text(message)
#         reply_markup = create_admin_menu()
#         await query.edit_message_reply_markup(reply_markup=reply_markup)
#
#     except mysql.connector.Error as err:
#         print(f"خطای پایگاه داده در قسمت confirm_edit_product: {err}")
#         await query.edit_message_text("❌ خطایی در ویرایش محصول رخ داد.")
#
#     return ConversationHandler.END
#
# async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("❌ عملیات ویرایش لغو شد.")
#     return ConversationHandler.END
#

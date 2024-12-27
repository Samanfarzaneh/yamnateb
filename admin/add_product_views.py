import logging
import mysql.connector
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ConversationHandler, ContextTypes

from admin.buttons import create_admin_menu, cancel_request, restart_conversation
from db import get_db_connection
from contextlib import contextmanager
from .states import WAITING_FOR_PRODUCT_NAME, WAITING_FOR_PRODUCT_PRICE, WAITING_FOR_CATEGORY_SELECTION, \
    WAITING_FOR_CONFIRMATION , ADD_PRODUCT, EDIT_PRODUCT, state_manager, end_conversation_handler






@contextmanager
def get_db_cursor():
    """ایجاد و مدیریت اتصال و کرسر پایگاه داده"""
    db_connection = get_db_connection()
    db_cursor = db_connection.cursor()
    try:
        yield db_connection, db_cursor  # بازگشت هر دو
    finally:
        db_cursor.close()
        db_connection.close()


async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.chat_data.clear()
    await restart_conversation(update, context)
    user_id = update.effective_user.id
    await end_conversation_handler(update, context)
    # بررسی وضعیت قبلی در chat_data (در صورتی که قبلاً ذخیره شده باشد)
    if user_id in context.chat_data:
        print(context.chat_data[user_id])
    # خاتمه دادن به مکالمه قبلی و پاک کردن وضعیت‌ها
    await end_conversation_handler(update, context)  # اطمینان از حذف وضعیت قبلی
    # تنظیم وضعیت جدید
    state_manager.set_state(user_id, ADD_PRODUCT)
    # پاک کردن داده‌های مربوط به وضعیت قبلی
    context.user_data.clear()  # یا می‌توانید فقط chat_data را پاک کنید اگر فقط وضعیت‌ها مدنظر باشند
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("❗ لطفاً نام محصول جدید را وارد کنید.")
    return WAITING_FOR_PRODUCT_NAME


async def receive_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if state_manager.get_state(user_id) != ADD_PRODUCT:
        await update.message.reply_text("❌ شما در وضعیت افزودن محصول نیستید. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END
    product_name = update.message.text
    context.user_data['product_name'] = product_name
    with get_db_cursor() as (db_connection, db_cursor):
        try:
            db_cursor.execute("SELECT id, name FROM categories")
            categories = db_cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"خطای پایگاه داده در receive_product_name: {err}")
            await update.message.reply_text("❌ خطایی در دریافت دسته‌بندی‌ها رخ داد.")
            return ConversationHandler.END

    if not categories:
        await update.message.reply_text("❌ هیچ دسته‌بندی‌ای در پایگاه داده موجود نیست.")
        return ConversationHandler.END

    # ساخت دکمه‌ها برای دسته‌بندی‌ها
    keyboard = [[InlineKeyboardButton(f"{cat[1]}", callback_data=f'category_{cat[1]}')] for cat in categories ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به مرحله قبل", callback_data='back_to_name')])
    keyboard.append([InlineKeyboardButton("❌ لفو", callback_data='cancel_request_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"نام محصول: {product_name}\nلطفاً دسته‌بندی محصول را انتخاب کنید.",
                                    reply_markup=reply_markup)
    return WAITING_FOR_CATEGORY_SELECTION

async def receive_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"User state: {state_manager.get_state(user_id)}")
    try:
        product_price = float(update.message.text)
    except ValueError:
        await update.message.reply_text("لطفاً قیمت را به درستی وارد کنید.")
        return WAITING_FOR_PRODUCT_PRICE

    context.user_data['product_price'] = product_price
    await update.message.reply_text(f"قیمت محصول: {product_price} ثبت شد.")

    product_name = context.user_data.get('product_name', 'نام وارد نشده')
    category_names = context.user_data.get('selected_categories', [])
    print(category_names)
    category_name = ', '.join(category_names) if category_names else 'هیچ دسته‌ای انتخاب نشده'

    confirmation_message = (
        f"✅ نام محصول: {product_name}\n"
        f"💲 قیمت: {product_price}\n"
        f"📂 دسته‌بندی: {category_name}\n\n"
        "آیا مطمئن هستید که می‌خواهید این محصول را اضافه کنید؟"
    )

    keyboard = [
        [InlineKeyboardButton("✅ بله", callback_data='confirm_add_product_menu')],
        [InlineKeyboardButton("❌ خیر", callback_data='cancel_request')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(confirmation_message, reply_markup=reply_markup)
    return WAITING_FOR_CONFIRMATION


async def confirm_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # بررسی اینکه آیا callback_query موجود است
    if not update.callback_query:
        logging.error("❌ callback_query موجود نیست.")
        return ConversationHandler.END

    query = update.callback_query

    # ارسال پاسخ به callback_query
    await query.answer()

    # دریافت داده‌های محصول از context.user_data
    product_name = context.user_data.get('product_name')
    product_price = context.user_data.get('product_price')
    selected_categories = context.user_data.get('selected_categories', [])

    # بررسی وجود دسته‌بندی‌های انتخابی
    if not selected_categories:
        await query.edit_message_text("❌ هیچ دسته‌بندی‌ای انتخاب نشده است.")
        state_manager.clear_state()
        return ConversationHandler.END

    # بررسی نام و قیمت محصول
    if not product_name or not product_price:
        await query.edit_message_text("❌ نام محصول یا قیمت معتبر وارد نشده است.")
        state_manager.clear_state(user_id=user_id)
        return ConversationHandler.END

    try:
        with get_db_cursor() as (db_connection, db_cursor):
            # بررسی وجود محصول در پایگاه داده
            db_cursor.execute(
                "SELECT id FROM products WHERE name = %s AND price = %s",
                (product_name, product_price)
            )
            product_result = db_cursor.fetchone()

            # اگر محصول موجود نباشد، آن را اضافه می‌کنیم
            if not product_result:
                db_cursor.execute(
                    "INSERT INTO products (name, price) VALUES (%s, %s)",
                    (product_name, product_price)
                )
                db_connection.commit()

                # دریافت ID محصول جدید
                db_cursor.execute(
                    "SELECT id FROM products WHERE name = %s AND price = %s",
                    (product_name, product_price)
                )
                product_id = db_cursor.fetchone()[0]
            else:
                # اگر محصول موجود باشد، ID آن را می‌گیریم
                product_id = product_result[0]

            # افزودن دسته‌بندی‌ها به جدول product_categories
            for category_name in selected_categories:
                db_cursor.execute(
                    "SELECT id FROM categories WHERE name = %s",
                    (category_name,)
                )
                category_result = db_cursor.fetchone()

                if category_result:
                    category_id = category_result[0]
                    logging.debug(f"Category: {category_name}, ID: {category_id}")

                    # ذخیره در جدول product_categories
                    db_cursor.execute(
                        "INSERT INTO product_categories (product_id, category_id) VALUES (%s, %s)",
                        (product_id, category_id)
                    )
                else:
                    # اگر دسته‌بندی پیدا نشد
                    await query.edit_message_text(f"❌ دسته‌بندی '{category_name}' یافت نشد.")
                    state_manager.clear_state(user_id=user_id)
                    return ConversationHandler.END

            # اعمال تغییرات در پایگاه داده پس از انجام تمام کارها
            db_connection.commit()

        # آماده‌سازی پیام نهایی
        category_names = ", ".join(selected_categories)
        message = f"✅محصول \"{product_name}\" به قیمت: {product_price} در دسته‌بندی‌های ({category_names}) با موفقیت اضافه شد."
        await query.edit_message_text(message, reply_markup=create_admin_menu())

    except mysql.connector.Error as err:
        logging.error(f"خطای پایگاه داده در قسمت confirm_add_product: {err}")
        await query.edit_message_text("❌ خطایی در افزودن محصول رخ داد.")

    except Exception as e:
        logging.error(f"خطای غیرمنتظره در confirm_add_product: {str(e)}")
        await query.edit_message_text("❌ خطای غیرمنتظره‌ای رخ داد.")
    context.user_data.clear()
    state_manager.clear_state(user_id=user_id)
    return ConversationHandler.END



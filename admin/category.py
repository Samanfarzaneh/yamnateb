import logging

import mysql
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from .buttons import create_admin_menu, restart_conversation
from admin.add_product_views import get_db_cursor
from admin.states import WAITING_FOR_CATEGORY_NAME, WAITING_FOR_CONFIRM_ADD_CATEGORY


async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await restart_conversation(update, context)
    context.user_data.clear()
    if not update.callback_query:  # بررسی وجود callback_query
        await update.message.reply_text("❌ درخواست نامعتبر.")
        return ConversationHandler.END

    await update.callback_query.answer()
    await update.callback_query.message.reply_text("❗ لطفاً نام دسته بندی را وارد کنید.")
    return WAITING_FOR_CATEGORY_NAME


async def receive_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # پاک‌سازی داده‌های قبلی
    category_name = update.message.text
    context.user_data['category_name'] = category_name

    confirmation_message = (
        f"📂 دسته‌بندی: {category_name}\n\n"
        "آیا مطمئن هستید که می‌خواهید این دسته بندی را اضافه کنید؟"
    )

    keyboard = [
        [InlineKeyboardButton("✅ بله", callback_data='confirm_add_category_menu')],
        [InlineKeyboardButton("❌ خیر", callback_data='cancel_request')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(confirmation_message, reply_markup=reply_markup)
    return ConversationHandler.END


async def confirm_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        logging.error("callback_query is None in confirm_add_category.")
        context.user_data.clear()
        return ConversationHandler.END

    await query.answer()
    category_name = context.user_data.get('category_name')

    if not category_name:
        await query.edit_message_text("❌ نام دسته‌بندی وارد نشده است.")
        context.user_data.clear()
        return ConversationHandler.END

    try:
        with get_db_cursor() as (db_connection, db_cursor):
            db_cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
            result = db_cursor.fetchone()
            reply_markup = create_admin_menu()

            if result:
                await query.edit_message_text(f"❗ دسته‌بندی '{category_name}' قبلاً وجود دارد.", reply_markup=reply_markup)
            else:
                db_cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category_name,))
                db_connection.commit()
                await query.edit_message_text(f"✅ دسته‌بندی '{category_name}' با موفقیت اضافه شد.", reply_markup=reply_markup)
                await restart_conversation(update, context)
    except mysql.connector.Error as err:
        logging.error(f"خطای پایگاه داده: {err}")
        await query.edit_message_text("❌ خطایی در افزودن دسته‌بندی رخ داد.")
    except Exception as e:
        logging.error(f"خطای غیرمنتظره: {e}")
        await query.edit_message_text("❌ خطای غیرمنتظره‌ای رخ داد.")
    finally:
        context.user_data.clear()

    return ConversationHandler.END

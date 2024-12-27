import json
from contextlib import contextmanager

from admin.add_product_views import confirm_add_product, add_product
from db import get_db_connection
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, \
    CallbackQueryHandler, CallbackContext
import mysql.connector
import logging
from admin.states import WAITING_FOR_PRODUCT_NAME, WAITING_FOR_PRODUCT_PRICE, WAITING_FOR_CATEGORY_SELECTION, \
    WAITING_FOR_CONFIRMATION, WAITING_FOR_SEARCH_PRODUCT, EDIT_PRODUCT, state_manager, WAITING_FOR_EDIT_PRODUCT_NAME, \
    WAITING_FOR_CONFIRM_ADD_CATEGORY
from .buttons import create_admin_menu, send_message, cancel_request
from .category import confirm_add_category

from .edit_product import delete_product, confirm_delete_product



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


# تابع شروع مکالمه
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if await is_admin(user_id):
        reply_markup = create_admin_menu()
        await update.message.reply_text("✅ با موفقیت وارد شدید!\nلطفاً یکی از گزینه‌ها را انتخاب کنید.", reply_markup=reply_markup)
        return
    else:
        await update.message.reply_text("❌ شما دسترسی به این بخش ندارید.")
        return ConversationHandler.END


async def admin_menu_control(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # استخراج user_id بسته به نوع update
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
    else:
        # اگر هیچ‌کدام موجود نبود، خطا ایجاد کنید
        raise ValueError("Cannot determine user ID. Update type is not supported.")

    # بررسی اینکه آیا کاربر ادمین است
    if await is_admin(user_id):
        reply_markup = create_admin_menu()
        # پاسخ مناسب به message یا callback_query
        if update.message:
            await update.message.reply_text(
                "✅ منوی مدیریت!\nلطفاً یکی از گزینه‌ها را انتخاب کنید.",
                reply_markup=reply_markup
            )
        elif update.callback_query:
            await update.callback_query.message.edit_text(
                "✅ منوی مدیریت!\nلطفاً یکی از گزینه‌ها را انتخاب کنید.",
                reply_markup=reply_markup
            )
    else:
        # پاسخ مناسب برای عدم دسترسی
        if update.message:
            await update.message.reply_text("❌ شما دسترسی به این بخش ندارید.")
        elif update.callback_query:
            await update.callback_query.message.edit_text("❌ شما دسترسی به این بخش ندارید.")





async def back_to_main_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    # فراخوانی منوی خانه
    await update.callback_query.edit_message_text(
        text="منوی مدیریت",
        reply_markup=create_admin_menu()
    )

async def is_admin(user_id: int) -> bool:
    try:
        with get_db_cursor() as (db_connection, db_cursor):
            db_cursor.execute("SELECT id FROM admin WHERE user_id = %s", (user_id,))
            admin = db_cursor.fetchone()
            return admin is not None
    except mysql.connector.Error as err:
        print(f"خطای پایگاه داده: {err}")
        return False



async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # بررسی اینکه آیا query وجود دارد و از نوع CallbackQuery است
    if query:
        await query.answer()
    else:
        print("No callback_query received!")

    callback_data = query.data

    if callback_data == 'add_product_menu':
        await add_product(update, context)
        return WAITING_FOR_PRODUCT_NAME

    elif callback_data == 'back_to_name':
        await query.edit_message_text("🔙 لطفاً نام محصول را دوباره وارد کنید.")
        return WAITING_FOR_PRODUCT_NAME

    elif callback_data.startswith('category_'):
        category_name = callback_data.replace('category_', '')

        if 'selected_categories' not in context.user_data:
            context.user_data['selected_categories'] = []

        if category_name in context.user_data['selected_categories']:
            context.user_data['selected_categories'].remove(category_name)
        else:
            context.user_data['selected_categories'].append(category_name)

        try:
            with get_db_cursor() as (db_connection, db_cursor):
                db_cursor.execute("SELECT name FROM categories")
                categories = db_cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"خطای پایگاه داده در قسمت button: {err}")
            return ConversationHandler.END

        # ساخت دکمه‌ها و دکمه تایید
        keyboard = [[InlineKeyboardButton(
            f"✅ {cat[0]}" if cat[0] in context.user_data['selected_categories'] else f"{cat[0]}",
            callback_data=f'category_{cat[0]}'
        )] for cat in categories]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به مرحله قبل", callback_data='back_to_name')])
        keyboard.append([InlineKeyboardButton("➡️ تایید و مرحله بعد", callback_data='product_price_menu')])
        keyboard.append([InlineKeyboardButton("❌ لفو عملیات", callback_data='cancel_request_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"✅ نام محصول: {context.user_data.get('product_name', 'نام وارد نشده')}\n"
            f"📋 دسته‌های انتخاب شده: {', '.join(context.user_data['selected_categories']) if context.user_data['selected_categories'] else 'هیچ‌کدام'}\n\n"
            "🔹 برای انتخاب یا لغو انتخاب، روی دسته کلیک کنید.\n🔹 برای بازگشت، روی دکمه بازگشت کلیک کنید.",
            reply_markup=reply_markup
        )

    elif callback_data == 'admin_menu':
        await admin_menu_control(update, context)


    elif callback_data == 'product_price_menu':
        await query.edit_message_text("💰 لطفاً قیمت محصول را وارد کنید.")
        return WAITING_FOR_PRODUCT_PRICE

    elif callback_data == 'confirm_add_product_menu':
        await confirm_add_product(update, context)
        return WAITING_FOR_CONFIRMATION

    elif callback_data == 'edit_product_menu':
        user_id = update.effective_user.id
        state_manager.set_state(user_id, EDIT_PRODUCT)
        await update.callback_query.answer()
        search_button = InlineKeyboardButton("🔍 جستجو", callback_data="search_product_for_edit")
        all_products_button = InlineKeyboardButton("🔍 مشاهده همه محصولات", callback_data="all_products")
        back_button = InlineKeyboardButton("بازگشت", callback_data="admin_menu")
        markup = InlineKeyboardMarkup([[all_products_button], [search_button], [back_button]])
        await send_message(update, "یکی از روش های زیر را انتخاب کنید::", reply_markup=markup)

    elif callback_data == 'delete_product_callback':
        await update.callback_query.answer()
        print("yes")
        await delete_product(update, context)

    elif callback_data == 'confirm_add_category_menu':
        await confirm_add_category(update, context)
        return WAITING_FOR_CONFIRM_ADD_CATEGORY

    elif callback_data == 'cancel_request_menu':
        await update.callback_query.answer()
        await cancel_request(update, context)
        return ConversationHandler.END

    # elif callback_data == 'search_product_for_edit':

    return WAITING_FOR_CATEGORY_SELECTION









import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from .states import ADD_PRODUCT, EDIT_PRODUCT, state_manager


def create_admin_menu():
    buttons = [
        [InlineKeyboardButton("➕ اضافه کردن محصول", callback_data="add_product_menu")],
        [InlineKeyboardButton("✏️ ویرایش محصول", callback_data="edit_product_menu")],
        [InlineKeyboardButton("📂 اضافه کردن دسته‌بندی", callback_data="add_category")],
        [InlineKeyboardButton("🛠️ ویرایش دسته‌بندی", callback_data="edit_category")],
        [InlineKeyboardButton("📦 مشاهده سفارشات", callback_data="view_orders")]
    ]

    return InlineKeyboardMarkup(buttons)




async def send_message(update: Update, message_text: str, reply_markup=None):
    try:
        if update.message:
            message = update.message
        elif update.callback_query:
            message = update.callback_query.message
        else:
            return
        await message.reply_text(message_text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in send_message: {e}")



async def cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        # بررسی اینکه آیا پیام یا callback_query موجود است
        if update.message:
            # اگر update.message موجود باشد
            await update.message.reply_text(
                "✅ درخواست شما لغو شد. می‌توانید دوباره اقدام کنید.",
                reply_markup=create_admin_menu()  # اطمینان حاصل کنید که این تابع به درستی پیاده‌سازی شده است
            )
        elif update.callback_query:
            # اگر update.callback_query موجود باشد
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                "✅ درخواست شما لغو شد. می‌توانید دوباره اقدام کنید.",
                reply_markup=create_admin_menu()
            )
        else:
            # اگر هیچ‌کدام از موارد موجود نباشد
            logging.warning("Neither message nor callback_query is available.")
    except Exception as e:
        # ثبت خطا در صورت بروز مشکل
        logging.error(f"Error in cancel_request: {e}")


async def restart_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع یک مکالمه جدید و حذف مکالمه قبلی"""
    # پاک کردن داده‌های مربوط به کاربر و چت
    context.user_data.clear()
    context.chat_data.clear()
    return ConversationHandler.END


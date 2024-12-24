import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler


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
    try:
        # بررسی اینکه آیا پیام یا callback_query موجود است
        if update.message:
            await update.message.reply_text(
                "✅ درخواست شما لغو شد. می‌توانید دوباره اقدام کنید.",
                reply_markup=create_admin_menu()
            )
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                "✅ درخواست شما لغو شد. می‌توانید دوباره اقدام کنید.",
                reply_markup=create_admin_menu()
            )
        else:
            logging.warning("Neither message nor callback_query is available.")
    except Exception as e:
        logging.error(f"Error in cancel_request: {e}")

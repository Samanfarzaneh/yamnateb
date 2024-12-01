from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application
import os  # برای کار با فایل‌ها

async def get_admin_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    print(f"Admin Chat ID: {chat_id}")  # چاپ chat_id در کنسول
    await update.message.reply_text(f"Your Chat ID is: {chat_id}")

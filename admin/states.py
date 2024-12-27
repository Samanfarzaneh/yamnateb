# states.py یا conversation_states.py
from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

WAITING_FOR_PRODUCT_NAME = 1
WAITING_FOR_PRODUCT_PRICE = 2
WAITING_FOR_CATEGORY_SELECTION = 3
WAITING_FOR_CONFIRMATION = 4
WAITING_FOR_EDIT_PRODUCT_NAME = 5
WAITING_FOR_EDIT_PRODUCT_PRICE = 6
WAITING_FOR_EDIT_CATEGORY_SELECTION = 7
WAITING_FOR_SEARCH_PRODUCT = 8
WAITING_FOR_CATEGORY_NAME = 9
WAITING_FOR_CONFIRM_ADD_CATEGORY = 10
ADD_PRODUCT = 100
EDIT_PRODUCT = 200



class UserStateManager:
    def __init__(self):
        self.user_states = {}

    def set_state(self, user_id, state):
        self.user_states[user_id] = state

    def get_state(self, user_id):
        return self.user_states.get(user_id)

    def clear_state(self, user_id):
        if user_id in self.user_states:
            del self.user_states[user_id]

state_manager = UserStateManager()


async def end_conversation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # پاک کردن وضعیت و داده‌های مرتبط با کاربر
    if user_id in context.chat_data:
        context.chat_data.pop(user_id, None)

    # خاتمه دادن به مکالمه
    await update.callback_query.answer()

    # اگر وضعیت‌ها را در `user_data` ذخیره کرده‌اید، آن‌ها را نیز پاک کنید
    context.user_data.clear()

    return ConversationHandler.END


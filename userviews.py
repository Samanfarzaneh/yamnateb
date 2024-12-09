# userviews.py
import asyncio
import json
import os
import mysql.connector
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot
from telegram.ext import ContextTypes

# خواندن فایل کانفیگ
with open("config.json", "r") as config_file:
    config = json.load(config_file)

DB_CONFIG = config["database"]
# اتصال به MySQL
db_connection = mysql.connector.connect(
    host=DB_CONFIG["host"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    database=DB_CONFIG["database"]
)
db_cursor = db_connection.cursor()


# تابعی برای ارسال پیام
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


# نمایش دسته‌بندی‌ها
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db_cursor.execute("SELECT id, name FROM categories")
        categories = db_cursor.fetchall()

        if not categories:
            await send_message(update, "هیچ دسته‌بندی موجود نیست.")
            return

        keyboard = [
            [InlineKeyboardButton(category[1], callback_data=f"show_products:{category[0]}")]
            for category in categories
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await send_message(update, "دسته‌بندی‌ها:", reply_markup=markup)
    except Exception as e:
        print(f"Error in show_categories: {e}")
        await send_message(update, "خطا در بارگذاری دسته‌بندی‌ها.")


# تابعی برای بازگشت به دسته‌بندی‌ها
async def handle_back_to_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # فراخوانی تابع نمایش دسته‌بندی‌ها
        await show_categories(update, context)
    except Exception as e:
        print(f"Error in handle_back_to_categories: {e}")
        await send_message(update, "خطا در بازگشت به دسته‌بندی‌ها.")


async def show_products_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        category_id = int(query.data.split(":")[1])

        # دریافت محصولات مرتبط با دسته‌بندی از جدول واسط product_categories
        db_cursor.execute("""
            SELECT p.id, p.name, p.price
            FROM products p
            JOIN product_categories pc ON p.id = pc.product_id
            WHERE pc.category_id = %s
        """, (category_id,))

        products = db_cursor.fetchall()

        if not products:
            await send_message(update, "هیچ محصولی در این دسته‌بندی موجود نیست.")
            return

        # ساخت کیبورد برای نمایش محصولات
        keyboard = [
            [InlineKeyboardButton(f"{product[1]} - {product[2]} تومان", callback_data=f"add_to_cart:{product[0]}")]
            for product in products
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await send_message(update, "محصولات این دسته‌بندی:", reply_markup=markup)

        # دکمه‌های جستجو و بازگشت
        search_button = InlineKeyboardButton("🔍 جستجو", callback_data="search_products")
        back_button = InlineKeyboardButton("بازگشت", callback_data="show_categories")
        markup = InlineKeyboardMarkup([[search_button], [back_button]])
        await send_message(update, "برای جستجو، دکمه زیر را فشار دهید:", reply_markup=markup)
    except Exception as e:
        print(f"Error in show_products_by_category: {e}")
        await send_message(update, "خطا در نمایش محصولات.")


# جستجوی محصولات
async def search_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        # از کاربر درخواست جستجو می‌کنیم
        await query.message.reply_text("لطفا نام محصول مورد نظر خود را وارد کنید:")
    except Exception as e:
        print(f"Error in search_products: {e}")
        await send_message(update, "خطا در جستجو.")


# انجام جستجو بر اساس ورودی کاربر
async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        search_query = update.message.text

        db_cursor.execute("SELECT id, name, price FROM products WHERE name LIKE %s", ('%' + search_query + '%',))
        results = db_cursor.fetchall()

        if not results:
            await send_message(update, "محصولی با این نام پیدا نشد.")
            return

        # نمایش نتایج جستجو
        keyboard = [
            [InlineKeyboardButton(f"{product[1]} - {product[2]} تومان", callback_data=f"add_to_cart:{product[0]}")]
            for product in results
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await send_message(update, "نتایج جستجو:", reply_markup=markup)
    except Exception as e:
        print(f"Error in handle_search: {e}")
        await send_message(update, "خطا در انجام جستجو.")


# افزودن به سبد خرید
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        product_id = int(query.data.split(":")[1])
        user_id = query.from_user.id

        # بررسی وجود محصول در سبد خرید
        db_cursor.execute(
            "SELECT id FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id)
        )
        cart_item = db_cursor.fetchone()

        if cart_item:
            # افزایش تعداد
            db_cursor.execute(
                "UPDATE cart SET quantity = quantity + 1 WHERE id = %s", (cart_item[0],)
            )
        else:
            # افزودن به سبد
            db_cursor.execute(
                "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                (user_id, product_id, 1),
            )
        db_connection.commit()

        # دکمه‌های ادامه
        continue_button = InlineKeyboardButton("مشاهده سبد خرید", callback_data="show_cart")
        back_button = InlineKeyboardButton("بازگشت به محصولات", callback_data="show_categories")
        markup = InlineKeyboardMarkup([[continue_button], [back_button]])

        await query.message.reply_text("محصول به سبد خرید اضافه شد.", reply_markup=markup)
    except Exception as e:
        print(f"Error in add_to_cart: {e}")
        await send_message(update, "خطا در افزودن محصول به سبد خرید.")


# تابع برای افزایش تعداد محصول
async def increase_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        cart_id = int(query.data.split(":")[1])

        # افزایش تعداد
        db_cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE id = %s", (cart_id,))
        db_connection.commit()

        # به روز رسانی سبد خرید بعد از تغییر
        await show_cart(update, context)
    except Exception as e:
        print(f"Error in increase_quantity: {e}")
        await send_message(update, "خطا در افزایش تعداد محصول.")


# تابع برای کاهش تعداد محصول
async def decrease_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        cart_id = int(query.data.split(":")[1])

        # کاهش تعداد
        db_cursor.execute("UPDATE cart SET quantity = quantity - 1 WHERE id = %s", (cart_id,))
        db_connection.commit()

        # اگر تعداد به صفر برسد، محصول را از سبد خرید حذف می‌کنیم
        db_cursor.execute("SELECT quantity FROM cart WHERE id = %s", (cart_id,))
        new_quantity = db_cursor.fetchone()[0]

        if new_quantity <= 0:
            db_cursor.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
            db_connection.commit()

        # به روز رسانی سبد خرید بعد از تغییر
        await show_cart(update, context)
    except Exception as e:
        print(f"Error in decrease_quantity: {e}")
        await send_message(update, "خطا در کاهش تعداد محصول.")


# تابع برای نمایش سبد خرید
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        db_cursor.execute(""" 
            SELECT c.id, p.name, c.quantity, p.price
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s
        """, (user_id,))
        cart_items = db_cursor.fetchall()

        if not cart_items:
            await send_message(update, "سبد خرید شما خالی است.")
            await show_categories(update, context)
            return

        total_price = 0
        response = "سبد خرید شما:\n\n"
        keyboard = []

        # نمایش هر محصول به همراه دکمه‌های کم و زیاد کردن تعداد
        for item in cart_items:
            item_id, name, quantity, price = item
            total_price += quantity * price
            response += f"{name} - تعداد: {quantity} - قیمت: {quantity * price} تومان\n"

            # دکمه‌های افزایش و کاهش تعداد
            increase_button = InlineKeyboardButton("➕", callback_data=f"increase_quantity:{item_id}")
            decrease_button = InlineKeyboardButton("➖", callback_data=f"decrease_quantity:{item_id}")

            # هر محصول همراه با دکمه‌های افزایش و کاهش در یک ردیف نمایش داده می‌شود
            keyboard.append([InlineKeyboardButton(f"{name} - تعداد: {quantity}", callback_data=f"product_{item_id}")])
            keyboard.append([increase_button, decrease_button])

        # نمایش مجموع قیمت
        response += f"\nمجموع: {total_price} تومان"

        # دکمه ثبت سفارش
        keyboard.append([InlineKeyboardButton("✅ ثبت سفارش", callback_data="confirm_order")])

        markup = InlineKeyboardMarkup(keyboard)
        await send_message(update, response, reply_markup=markup)
    except Exception as e:
        print(f"Error in show_cart: {e}")
        await send_message(update, "خطا در نمایش سبد خرید.")


# تابع برای حذف محصول از سبد خرید
async def remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        cart_id = int(query.data.split(":")[1])
        db_cursor.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
        db_connection.commit()

        # دکمه‌های ادامه
        continue_button = InlineKeyboardButton("مشاهده سبد خرید", callback_data="show_cart")
        back_button = InlineKeyboardButton("بازگشت به محصولات", callback_data="show_categories")
        markup = InlineKeyboardMarkup([[continue_button], [back_button]])

        await query.message.reply_text("محصول از سبد خرید حذف شد.", reply_markup=markup)
    except Exception as e:
        print(f"Error in remove_from_cart: {e}")
        await send_message(update, "خطا در حذف محصول از سبد خرید.")


# تابع برای افزودن جزئیات سفارش
async def print_cart_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        # گرفتن اطلاعات سبد خرید از دیتابیس برای کاربر
        db_cursor.execute("""
            SELECT c.id, p.name, c.quantity, p.price
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s
        """, (user_id,))

        # دریافت نتایج
        cart_items = db_cursor.fetchall()

        # اگر سبد خرید خالی بود
        if not cart_items:
            print(f"سبد خرید کاربر {user_id} خالی است.")
            await send_message(update, "سبد خرید شما خالی است.")
            return

        # اگر سبد خرید پر باشد
        print(f"سبد خرید کاربر {user_id}:")
        for item in cart_items:
            item_id, name, quantity, price = item
            total_price = quantity * price
            print(f"محصول: {name}, تعداد: {quantity}, قیمت هر واحد: {price} تومان, مجموع: {total_price} تومان")

        # اگر نیاز دارید که پیامی هم به کاربر ارسال شود
        await send_message(update, "اطلاعات سبد خرید در کنسول چاپ شد.")

    except Exception as e:
        print(f"Error in print_cart_items: {e}")
        await send_message(update, "خطا در نمایش سبد خرید.")

def get_product_price(db_connection, product_id):
    # فرض کنید یک کوئری برای دریافت قیمت محصول از دیتابیس دارید
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
        result = cursor.fetchone()
        return result[0] if result else 0  # در صورت پیدا نکردن محصول قیمت پیش‌فرض 0

def add_order_details(order_id, cart, db_connection):
    print(order_id)
    print(cart)
    try:
        with db_connection.cursor() as cursor:  # cursor را در داخل بلوک with تعریف می‌کنیم
            for item in cart:
                product_id = item[0]  # شناسه محصول
                quantity = item[1]  # تعداد محصول
                price_per_unit = get_product_price(db_connection, product_id)  # فراخوانی get_product_price

                # اضافه کردن جزئیات به جدول order_details
                cursor.execute("""
                    INSERT INTO order_details (order_id, product_id, quantity, price_per_unit)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, product_id, quantity, price_per_unit))

            # ذخیره تغییرات در دیتابیس
            db_connection.commit()
    except Exception as e:
        print(f"Error in add_order_details: {e}")
        db_connection.rollback()  # در صورت بروز خطا تغییرات لغو می‌شود


# ثبت سفارش نهایی
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_id = db_cursor.lastrowid
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id

        # محاسبه مجموع قیمت
        db_cursor.execute(""" 
            SELECT SUM(c.quantity * p.price) 
            FROM cart c 
            JOIN products p ON c.product_id = p.id 
            WHERE c.user_id = %s 
        """, (user_id,))
        total_price = db_cursor.fetchone()[0]

        if total_price is None or total_price == 0:
            # اگر سبد خرید خالی باشد
            await send_message(update, "سبد خرید شما خالی است❗")
            await send_message(update, "برای مشاهده محصولات، می توانید از بین دسته بندی ها انتخاب کنید:")
            await show_categories(update, context)
            return

        # ایجاد سفارش در دیتابیس
        db_cursor.execute(
            "INSERT INTO orders (user_id, total_price, status) VALUES (%s, %s, 'در حال پردازش')",
            (user_id, total_price)
        )
        db_connection.commit()

        # گرفتن شناسه سفارش ثبت شده
        order_id = db_cursor.lastrowid

        # گرفتن جزئیات سبد خرید کاربر فعلی
        db_cursor.execute("SELECT product_id, quantity FROM cart WHERE user_id = %s", (user_id,))
        cart = db_cursor.fetchall()  # اینجا فقط سبد خرید کاربر فعلی رو می‌گیریم

        # اضافه کردن جزئیات سفارش به جدول order_details
        add_order_details(order_id, cart, db_connection)

        # پاک کردن سبد خرید
        db_cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        db_connection.commit()

        # ارسال پیام به کاربر حاوی اطلاعات سفارش و شناسه سفارش
        message = f"""
        همراه گرامی، برای تکمیل سفارش خود لطفاً مبلغ {total_price} تومان را به شماره حساب زیر واریز نمایید.
        شناسه سفارش شما: {order_id}
        """
        await send_message(update, message)
        context.user_data['total_price'] = total_price
        context.user_data['order_id'] = order_id
        return
    except Exception as e:
        print(f"Error in confirm_order: {e}")
        await send_message(update, "خطا در ثبت سفارش.")


async def handle_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # دریافت عکس از پیام
        photo_file = update.message.photo[-1]  # انتخاب بزرگ‌ترین سایز عکس
        file_id = photo_file.file_id  # گرفتن شناسه فایل
        total_price = context.user_data.get('total_price')
        order_id = context.user_data.get('order_id')
        # دریافت شیء فایل
        file = await context.bot.get_file(file_id)
        print(total_price, order_id)
        # دریافت شناسه پیام (سفارش)
        # order_id = update.message.message_id  # استفاده از شناسه پیام برای نام فایل

        # تعیین مسیر ذخیره فایل
        file_path = os.path.join("payment_receipts", f"payment_receipt_{order_id}.jpg")

        # دانلود فایل به صورت async
        await file.download_to_drive(file_path)  # دانلود و ذخیره فایل در مسیر مشخص

        # تایید دریافت
        await update.message.reply_text("باتشکر از خرید شما. "
                                        "پس از بررسی رسید و تایید آن، همکاران ما با شما تماس خواهند گرفت.")
        # total_price = await get_total_price_by_order_id(order_id)
        # اطلاعات سفارش برای ارسال به کانال
        order_details_subject = f"سفارش جدید به شماره {order_id}  وبه مبلغ {total_price}دریافت شد."
        await send_order_to_channel(order_details_subject)
        print("سفارش دریافت شد")

    except Exception as e:
        print(f"Error in handle_payment_receipt: {e}")
        await update.message.reply_text("خطا در دریافت رسید واریز. لطفا دوباره امتحان کنید.")


async def send_order_to_channel(order_details):
    try:
        bot_token = "7942973073:AAHOTQeXBEJF5T9VgRxyFf21oLpwD26x5EE"  # توکن ربات دوم
        channel_chat_id = "@yamnateb_orders"  # شناسه کانال

        # ساخت یک شی Bot
        bot = Bot(token=bot_token)

        # ارسال پیام به کانال
        await bot.send_message(chat_id=channel_chat_id, text=order_details)
        print("پیام سفارش به کانال ارسال شد.")

    except Exception as e:
        print(f"خطا در ارسال پیام: {e}")

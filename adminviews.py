import json
from db import DatabaseConnection
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, \
    CallbackQueryHandler, CallbackContext
import mysql.connector
from admin import edit_product


# بارگذاری کانفیگ
with open("config.json", "r") as config_file:
    config = json.load(config_file)

DB_CONFIG = config["database"]

# اتصال به پایگاه داده
try:
    db_connection = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )
    db_cursor = db_connection.cursor()
except mysql.connector.Error as err:
    print(f"خطا در اتصال به پایگاه داده: {err}")
    exit()



# وضعیت‌های مکالمه
WAITING_FOR_PRODUCT_NAME = 1
WAITING_FOR_PRODUCT_PRICE = 2
WAITING_FOR_CATEGORY_SELECTION = 3
WAITING_FOR_CONFIRMATION = 4
WAITING_FOR_EDIT_PRODUCT_NAME = 5



# تابع شروع مکالمه
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if await is_admin(user_id):
        reply_markup = create_admin_menu()
        await update.message.reply_text("✅ با موفقیت وارد شدید!\nلطفاً یکی از گزینه‌ها را انتخاب کنید.", reply_markup=reply_markup)
        return WAITING_FOR_PRODUCT_NAME
    else:
        await update.message.reply_text("❌ شما دسترسی به این بخش ندارید.")
        return ConversationHandler.END

def create_admin_menu():
    buttons = [
        [InlineKeyboardButton("اضافه کردن محصول", callback_data="add_product_menu")],
        [InlineKeyboardButton("ویرایش محصول", callback_data="edit_product_menu")],
        [InlineKeyboardButton("اضافه کردن دسته‌بندی", callback_data="add_category")],
        [InlineKeyboardButton("ویرایش دسته‌بندی", callback_data="edit_category")],
        [InlineKeyboardButton("مشاهده سفارشات", callback_data="view_orders")]
    ]
    return InlineKeyboardMarkup(buttons)

async def back_to_main_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    # فراخوانی منوی خانه
    await update.callback_query.edit_message_text(
        text="منوی مدیریت",
        reply_markup=create_admin_menu()
    )

async def is_admin(user_id: int) -> bool:
    try:
        db_cursor.execute("SELECT id FROM admin WHERE user_id = %s", (user_id,))
        admin = db_cursor.fetchone()
        return admin is not None
    except mysql.connector.Error as err:
        print(f"خطای پایگاه داده: {err}")
        return False

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("❗ لطفاً نام محصول را وارد کنید.")
    return WAITING_FOR_PRODUCT_NAME

async def receive_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_name = update.message.text
    context.user_data['product_name'] = product_name

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
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_name')])
    # keyboard.append([InlineKeyboardButton("➡️ تایید و مرحله بعد", callback_data='product_price_menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"نام محصول: {product_name}\nلطفاً دسته‌بندی محصول را انتخاب کنید.",
                                    reply_markup=reply_markup)
    return WAITING_FOR_CATEGORY_SELECTION

async def receive_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        [InlineKeyboardButton("❌ خیر", callback_data='cancel_add_product')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(confirmation_message, reply_markup=reply_markup)
    return WAITING_FOR_CONFIRMATION


async def confirm_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_name = context.user_data['product_name']
    product_price = context.user_data['product_price']
    selected_categories = context.user_data.get('selected_categories', [])

    if not selected_categories:
        await query.edit_message_text("❌ هیچ دسته‌بندی‌ای انتخاب نشده است.")
        return ConversationHandler.END

    try:

        db_cursor.execute("SELECT id FROM products WHERE name = %s AND price = %s", (product_name, product_price))
        product_result = db_cursor.fetchone()

        if not product_result:
            db_cursor.execute("INSERT INTO products (name, price) VALUES (%s, %s)", (product_name, product_price))
            db_connection.commit()

            # دریافت ID محصول جدید
            db_cursor.execute("SELECT id FROM products WHERE name = %s AND price = %s", (product_name, product_price))
            product_id = db_cursor.fetchone()[0]
        else:
            # اگر محصول وجود داشت، ID آن را می‌گیریم
            product_id = product_result[0]

        # حالا برای هر دسته‌بندی انتخابی، آن را به جدول product_categories اضافه می‌کنیم
        for category_name in selected_categories:
            db_cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
            category_result = db_cursor.fetchone()

            if category_result:
                category_id = category_result[0]
                print(f"Category: {category_name}, ID: {category_id}")

                # ذخیره در جدول product_categories
                db_cursor.execute("INSERT INTO product_categories (product_id, category_id) VALUES (%s, %s)",
                                  (product_id, category_id))
                db_connection.commit()
            else:
                print(f"Category '{category_name}' not found.")

        category_names = ", ".join(selected_categories)  # دسته‌بندی‌ها را به صورت رشته‌ای از اسم‌ها نمایش می‌دهیم
        message = f"محصول \"{product_name}\" به قیمت: {product_price} در دسته‌بندی‌های ({category_names}) با موفقیت اضافه شد."

        await query.edit_message_text(message)
        reply_markup = create_admin_menu()
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    except mysql.connector.Error as err:
        print(f"خطای پایگاه داده در قسمت confirm_add_product: {err}")
        await query.edit_message_text("❌ خطایی در افزودن محصول رخ داد.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

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

async def search_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        # از کاربر درخواست جستجو می‌کنیم
        await query.message.reply_text("لطفا نام محصول مورد نظر خود را وارد کنید:")
    except Exception as e:
        print(f"Error in search_products: {e}")
        await send_message(update, "خطا در جستجو.")
async def edit_product_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        # چاپ داده کامل
        print("Full query data:", query.data)

        # اسپلیت کردن رشته برای جدا کردن شناسه
        category_id = query.data.split(":")[1]  # جدا کردن شناسه بعد از ":"

        # اصلاح کوئری برای دریافت شناسه محصولات از جدول product_categories
        query = "SELECT product_id FROM product_categories WHERE category_id = %s"
        db_cursor.execute(query, (category_id,))
        product_ids = db_cursor.fetchall()  # دریافت تمامی شناسه‌های محصولات

        # چک کردن اینکه آیا محصولی وجود دارد
        if product_ids:
            # ایجاد لیستی برای نام محصولات
            product_names = []

            # برای هر شناسه محصول، نام آن را از جدول محصولات دریافت می‌کنیم
            for product_id in product_ids:
                query = "SELECT name FROM products WHERE id = %s"
                db_cursor.execute(query, (product_id[0],))  # استفاده از شناسه محصول
                product_name = db_cursor.fetchone()

                if product_name:
                    product_names.append(product_name[0])  # ذخیره نام محصول

            # نمایش لیست نام محصولات به کاربر
            if product_names:
                keyboard = [
                    [InlineKeyboardButton(f"{name}", callback_data=f"product:{name}")]
                    for name in product_names
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await send_message(update, "محصولات این دسته‌بندی:", reply_markup=reply_markup)
            else:
                await send_message(update, ":", reply_markup=create_admin_menu)
        else:
            await send_message(update, ":", reply_markup=create_admin_menu)

    except Exception as e:
        print(f'Error: {e}')


# تابعی برای دریافت و نمایش تمامی محصولات
async def show_all_products(update: Update, context: CallbackContext):

    # اجرای کوئری برای دریافت تمامی محصولات
    query = "SELECT id, name FROM categories"
    db_cursor.execute(query)
    # دریافت نتایج کوئری
    categories = db_cursor.fetchall()

    # query = "SELECT id, name FROM categories"
    # db_cursor.execute(query)
    # categories = db_cursor.fetchall()
    # print(categories)


    # بررسی اینکه آیا محصولات وجود دارند یا خیر
    # if not products:
    #     await update.message.reply_text("هیچ محصولی در دیتابیس موجود نیست.")
    #     db_cursor.close()
    #     db_connection.close()
    #     return

    keyboard = [
        [InlineKeyboardButton(f"{category[1]}", callback_data=f"select_category:{category[0]}")]
        for category in categories
    ]


    # keyboard = [
    #     [InlineKeyboardButton(f"{product[1]} - {product[0]} تومان", callback_data=f"add_to_cart:{product[0]}")]
    #     for product in products
    # ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, "انتخاب دسته بندی:", reply_markup=reply_markup)
    # # بستن اتصال به دیتابیس
    # db_cursor.close()
    # db_connection.close()







# def register_handlers(dp):
#     dp.add_handler(CommandHandler("show_products", show_all_products))

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
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_name')])
        keyboard.append([InlineKeyboardButton("➡️ تایید و مرحله بعد", callback_data='product_price_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"✅ نام محصول: {context.user_data.get('product_name', 'نام وارد نشده')}\n"
            f"📋 دسته‌های انتخاب شده: {', '.join(context.user_data['selected_categories']) if context.user_data['selected_categories'] else 'هیچ‌کدام'}\n\n"
            "🔹 برای انتخاب یا لغو انتخاب، روی دسته کلیک کنید.\n🔹 برای بازگشت، روی دکمه بازگشت کلیک کنید.",
            reply_markup=reply_markup
        )

    elif callback_data == 'product_price_menu':
        await query.edit_message_text("💰 لطفاً قیمت محصول را وارد کنید.")
        return WAITING_FOR_PRODUCT_PRICE

    elif callback_data == 'confirm_add_product_menu':
        await confirm_add_product(update, context)
        return WAITING_FOR_CONFIRMATION

    elif callback_data == 'edit_product_menu':
        await update.callback_query.answer()
        search_button = InlineKeyboardButton("🔍 جستجو", callback_data="search_products")
        all_products_button = InlineKeyboardButton("🔍 مشاهده همه محصولات", callback_data="all_products")
        back_button = InlineKeyboardButton("بازگشت", callback_data="home_menu_handler")
        markup = InlineKeyboardMarkup([[all_products_button], [search_button], [back_button]])
        await send_message(update, "یکی از روش های زیر را انتخاب کنید::", reply_markup=markup)

        return WAITING_FOR_EDIT_PRODUCT_NAME

    return WAITING_FOR_CATEGORY_SELECTION






import logging
from contextlib import contextmanager

import mysql
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler, ContextTypes

from admin.buttons import send_message, create_admin_menu
from admin.states import WAITING_FOR_SEARCH_PRODUCT, ADD_PRODUCT, EDIT_PRODUCT, \
    WAITING_FOR_EDIT_PRODUCT_PRICE, WAITING_FOR_EDIT_PRODUCT_NAME, state_manager, end_conversation_handler
from db import get_db_connection

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


async def confirm_delete_product(update: Update, context: CallbackContext):
    try:
        callback_query = update.callback_query
        logging.debug(f"Callback query received: {callback_query}")
        await callback_query.answer()

        product_id = callback_query.data.split(":")[1]
        logging.debug(f"Product ID: {product_id}")

        db_query = """
            SELECT p.id, p.name, p.price, c.name AS category_name
            FROM products p
            JOIN product_categories pc ON p.id = pc.product_id
            JOIN categories c ON pc.category_id = c.id
            WHERE p.id = %s
        """
        with get_db_cursor() as (db_connection, db_cursor):
            try:
                logging.debug("Executing DB query")
                db_cursor.execute(db_query, (product_id,))
                result = db_cursor.fetchone()

                if result:
                    logging.debug(f"Query result: {result}")
                    confirmation_message = (
                        f"✅ نام محصول: {result[1]}\n"
                        f"💲 قیمت: {result[2]}\n"
                        f"📂 دسته‌بندی: {result[3]}\n\n"
                        "آیا مطمئن هستید که می‌خواهید این محصول را حذف کنید؟"
                    )
                    keyboard = [
                        [InlineKeyboardButton("✅ بله", callback_data=f'delete_product:{product_id}')],
                        [InlineKeyboardButton("❌ خیر", callback_data='cancel_delete_product')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await callback_query.message.edit_text(text=confirmation_message, reply_markup=reply_markup)
                else:
                    logging.warning("Product not found")
                    await callback_query.message.reply_text("❌ محصول مورد نظر یافت نشد.")
            except mysql.connector.Error as db_error:
                logging.error(f"Database error: {db_error}")
                await callback_query.message.reply_text("❌ خطا در اجرای کوئری پایگاه داده.")
    except Exception as e:
        logging.error(f"Error in confirm_delete_product: {e}")
        await callback_query.message.reply_text("❌ خطا در تأیید حذف محصول.")
async def delete_product(update: Update, context: CallbackContext):
    try:
        with get_db_cursor() as (db_connection, db_cursor):
            query = update.callback_query
            await query.answer()

            # دریافت شناسه محصول از داده callback_data
            product_id = query.data.split(":")[1]

            # اجرای کوئری برای حذف محصول از جدول 'products'
            db_query = "DELETE FROM products WHERE id = %s"
            with get_db_cursor() as (db_connection, db_cursor):
                db_cursor.execute(db_query, (product_id,))

                # حذف محصول از جدول 'product_categories'
                db_query_categories = "DELETE FROM product_categories WHERE product_id = %s"
                db_cursor.execute(db_query_categories, (product_id,))

                # اعمال تغییرات در پایگاه داده
                db_connection.commit()

                # ارسال پیام به کاربر که محصول با موفقیت حذف شد
                await query.message.edit_text(f"✅ محصول با ID {product_id} حذف شد.")
    except Exception as e:
        print(f"Error in delete_product: {e}")
        await query.message.reply_text("❌ خطا در حذف محصول.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def search_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await end_conversation_handler(update, context)
    user_id = update.effective_user.id
    state_manager.set_state(user_id, EDIT_PRODUCT)
    print(f"Current state for user {user_id}: {state_manager.get_state(user_id)}")
    context.user_data.clear()  # ریست کردن داده‌های کاربر

    try:
        # بررسی وجود callback_query
        if update.callback_query:
            query = update.callback_query
            await query.answer()  # پاسخ به درخواست callback_query

            # از کاربر درخواست جستجو می‌کنیم
            await query.message.reply_text("برای جستجو لطفا نام محصول مورد نظر خود را وارد کنید:")
        else:
            # اگر callback_query وجود ندارد، از update.message استفاده می‌کنیم
            await update.message.reply_text("برای جستجو لطفا نام محصول مورد نظر خود را وارد کنید.")

        return WAITING_FOR_SEARCH_PRODUCT
    except Exception as e:
        print(f"Error in search_product: {e}")
        # در صورتی که خطایی رخ دهد، پیام مناسب ارسال می‌کنیم
        if update.callback_query:
            await update.callback_query.message.reply_text("❌ خطا در جستجو.")
        else:
            await update.message.reply_text("❌ خطا در جستجو.")

        return ConversationHandler.END


async def search_product_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state_manager.set_state(user_id, EDIT_PRODUCT)
    print(f"Current state for user {user_id}: {state_manager.get_state(user_id)}")

    # بررسی وضعیت کلی کاربر
    if state_manager.get_state(user_id) != EDIT_PRODUCT:
        await update.message.reply_text("❌ شما در وضعیت ویرایش محصول نیستید. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END

    try:
        context.user_data.clear()  # مطمئن شوید که اطلاعات کاربر فقط در شرایط خاص پاک می‌شود

        # دریافت نام محصول از ورودی کاربر
        product_name = update.message.text.strip()

        if not product_name:
            await update.message.reply_text("❌ نام محصول نمی‌تواند خالی باشد.")
            return ConversationHandler.END

        print(f"Searching for product: {product_name}")

        # اجرای کوئری جستجو
        db_query = "SELECT id, name, price FROM products WHERE name LIKE %s"

        # استفاده از with برای اطمینان از بستن درست کرسر
        with get_db_cursor() as (db_connection, db_cursor):
            db_cursor.execute(db_query, ('%' + product_name + '%',))
            results = db_cursor.fetchall()  # خواندن تمام نتایج

            # اطمینان از مصرف نتایج قبل از انجام هر کار دیگری
            if not results:
                await update.message.reply_text("❌ محصولی با این نام یافت نشد.")
                return ConversationHandler.END

        # اگر نتایج جستجو یافت شد
        if results:
            # نمایش نتایج با دکمه‌های Inline برای اضافه کردن به سبد خرید
            keyboard = [
                [InlineKeyboardButton(f"{product[1]} - {product[2]} تومان", callback_data=f"selected_product_for_edit:{product[0]}")]
                for product in results
            ]
            markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("📋 نتایج جستجو:", reply_markup=markup)

    except Exception as e:
        print(f"Error in search_product_by_name: {e}")
        await update.message.reply_text("❌ خطا در جستجو.")

    finally:
        # بازنشانی وضعیت به حالت اولیه یا مناسب
        return ConversationHandler.END


async def selected_product_for_edit(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        query = update.callback_query
        await query.answer()  # پاسخ به callback_query برای جلوگیری از خطا

        # بررسی اینکه آیا query.data به درستی split می‌شود
        try:
            product_id = query.data.split(":")[1]
        except IndexError:
            raise ValueError("فرمت callback_data نادرست است.")

        print(f"Product ID: {product_id}")

        # اجرای کوئری برای دریافت اطلاعات محصول به همراه نام دسته‌بندی
        db_query = """
            SELECT 
                p.id AS product_id,
                p.name AS product_name,
                p.price AS product_price,
                c.name AS category_name
            FROM 
                products AS p
            INNER JOIN 
                product_categories AS pc ON p.id = pc.product_id
            INNER JOIN 
                categories AS c ON pc.category_id = c.id
            WHERE 
                p.id = %s
        """

        # استفاده از with برای مدیریت کرسر به طور خودکار
        with get_db_cursor() as (db_connection, db_cursor):
            # اجرای کوئری و دریافت نتیجه تنها یک بار
            db_cursor.execute(db_query, (product_id,))
            result = db_cursor.fetchone()  # استفاده از fetchone فقط یک بار

            # بررسی اینکه آیا نتیجه‌ای پیدا شده است یا خیر
            if result:
                product_id = result[0]
                product_name = result[1]
                product_price = result[2]
                category_name = result[3]

                print(f"Product: {product_name}, Price: {product_price}, Category: {category_name}")

                # آماده کردن دکمه‌ها برای نمایش به کاربر
                product_name_btn = InlineKeyboardButton(f"نام محصول: {product_name}", callback_data=f"start_edit_name:{product_id}")
                product_price_btn = InlineKeyboardButton(f"قیمت: {product_price} تومان", callback_data=f"start_edit_price:{product_id}")
                product_category_btn = InlineKeyboardButton(f"دسته‌بندی: {category_name}", callback_data=f"start_edit_category:{product_id}")
                delete_product_btn = InlineKeyboardButton("❌ برای حذف این محصول کلیک کنید", callback_data=f"delete_product_callback:{product_id}")

                # ایجاد کیبورد و ارسال پیام
                reply_markup = InlineKeyboardMarkup([  # ساختار کیبورد اصلاح شده
                    [product_name_btn],
                    [product_price_btn],
                    [product_category_btn],
                    [delete_product_btn]
                ])

                # استفاده از edit_text فقط در صورتی که query.message موجود باشد
                if query.message:
                    try:
                        await query.message.edit_text("عنوان ویرایش خود را انتخاب کنید:", reply_markup=reply_markup)
                    except Exception as e:
                        print(f"Error editing message: {e}")
                        await query.message.reply_text(f"❌ خطا در ویرایش پیام. جزئیات: {str(e)}")
                else:
                    try:
                        await send_message(update, "عنوان ویرایش خود را انتخاب کنید:", reply_markup=reply_markup)
                    except Exception as e:
                        print(f"Error sending message: {e}")
                        await send_message(update, f"❌ خطا در ارسال پیام. جزئیات: {str(e)}")

            else:
                print("❌ محصولی با این مشخصات یافت نشد.")
                await query.message.reply_text("❌ محصولی با این مشخصات یافت نشد.")

    except Exception as e:
        print(f"Error: {e}")

async def start_edit_name(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    state_manager.set_state(user_id, EDIT_PRODUCT)
    print(f"Current state for user {user_id}: {state_manager.get_state(user_id)}")
    query = update.callback_query
    await query.answer()

    try:
        product_id = query.data.split(":")[1]
        context.user_data['product_id'] = product_id
        await query.edit_message_text("لطفاً نام جدید محصول را وارد کنید:")
        return WAITING_FOR_EDIT_PRODUCT_NAME
    except Exception as e:
        print(f"Error in start_edit_name: {e}")
        await query.edit_message_text("❌ مشکلی در پردازش درخواست شما پیش آمده است.")


async def save_new_name(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    product_id = context.user_data.get('product_id')
    new_name = update.message.text

    try:
        with get_db_cursor() as (db_connection, db_cursor):
            db_cursor.execute("UPDATE products SET name = %s WHERE id = %s", (new_name, product_id))
            db_connection.commit()

        await update.message.reply_text(f"✅ نام محصول با موفقیت به **{new_name}** تغییر یافت.")
    except Exception as e:
        print(f"خطا در ذخیره نام جدید: {e}")
        await update.message.reply_text("❌ خطا در ذخیره نام جدید.")
        state_manager.clear_state(user_id)

    return ConversationHandler.END


async def start_edit_price(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    print(f"User state: {context.user_data.get('state')}")
    product_id = query.data.split(":")[1]
    context.user_data['product_id'] = product_id
    user_id = update.effective_user.id
    state_manager.set_state(user_id, EDIT_PRODUCT)
    print(f"Current state for user {user_id}: {state_manager.get_state(user_id)}")
    await query.edit_message_text("لطفاً قیمت جدید محصول را وارد کنید (فقط عدد):")
    return WAITING_FOR_EDIT_PRODUCT_PRICE


async def save_new_price(update: Update, context: CallbackContext):
    print(f"User state: {context.user_data.get('state')}")
    print("save_new_price called")
    product_id = context.user_data.get('product_id')
    new_price = update.message.text

    # بررسی صحت عدد بودن ورودی
    if not new_price.isdigit():
        await update.message.reply_text("❌ لطفاً فقط عدد وارد کنید.")
        return WAITING_FOR_EDIT_PRODUCT_PRICE

    new_price = int(new_price)  # تبدیل به عدد صحیح

    print(f"Updating product ID: {product_id} with new price: {new_price}")

    try:
        with get_db_cursor() as (db_connection, db_cursor):
            print(f"Executing query: UPDATE products SET price = {new_price} WHERE id = {product_id}")
            db_cursor.execute("UPDATE products SET price = %s WHERE id = %s", (new_price, product_id))
            db_connection.commit()

        await update.message.reply_text(f"✅ قیمت محصول با موفقیت به **{new_price} تومان** تغییر یافت.")
    except Exception as e:
        print(f"خطا در ذخیره قیمت جدید: {e}")
        await update.message.reply_text("❌ خطا در ذخیره قیمت جدید.")

    return ConversationHandler.END



async def start_edit_category(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    product_id = query.data.split(":")[1]

    db_query = """
        SELECT p.id, p.name, p.price, c.name AS category_name
        FROM products p
        JOIN product_categories pc ON p.id = pc.product_id
        JOIN categories c ON pc.category_id = c.id
        WHERE p.id = %s
    """

    with get_db_cursor() as (db_connection, db_cursor):
        # اجرای کوئری و دریافت نتیجه تنها یک بار
        db_cursor.execute(db_query, (product_id,))
        result = db_cursor.fetchone()  # استفاده از fetchone فقط یک بار

        # بررسی اینکه آیا نتیجه‌ای پیدا شده است یا خیر
        if result:
            product_id = result[0]
            product_name = result[1]
            product_price = result[2]
            category_name = result[3]

            print(f"Product: {product_name}, Price: {product_price}, Category: {category_name}")

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
    keyboard = [[InlineKeyboardButton(f"{cat[1]}", callback_data=f'edit_category_{cat[1]}')] for cat in categories]
    keyboard.append([InlineKeyboardButton("❌ لفو عملیات", callback_data='cancel_request')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"نام محصول: {product_name}\nلطفاً دسته‌بندی جدید محصول را انتخاب کنید.",
                                    reply_markup=reply_markup)

async def select_edited_category(update: Update, context: CallbackContext):
    query = update.callback_query
    callback_data = query.data
    if callback_data.startswith('edit_category_'):
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
        keyboard.append([InlineKeyboardButton("➡️ تایید و مرحله بعد", callback_data='product_price_menu')])
        keyboard.append([InlineKeyboardButton("❌ لفو عملیات", callback_data='cancel_request')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"✅ نام محصول: {context.user_data.get('product_name', 'نام وارد نشده')}\n"
            f"📋 دسته‌های انتخاب شده: {', '.join(context.user_data['selected_categories']) if context.user_data['selected_categories'] else 'هیچ‌کدام'}\n\n"
            "🔹 برای انتخاب یا لغو انتخاب، روی دسته کلیک کنید.\n🔹 برای بازگشت، روی دکمه بازگشت کلیک کنید.",
            reply_markup=reply_markup
        )

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with get_db_cursor() as (db_connection, db_cursor):
            # 1. دریافت callback_query
            callback_query = update.callback_query
            await callback_query.answer()

            # 3. گرفتن category_id از callback_data
            category_id = callback_query.data.split(":")[1]  # شناسه دسته‌بندی

            # 4. جستجوی شناسه محصولات مرتبط با دسته‌بندی
            sql_query = "SELECT product_id FROM product_categories WHERE category_id = %s"
            db_cursor.execute(sql_query, (category_id,))
            product_ids = db_cursor.fetchall()

            # 5. بررسی وجود محصول در دسته‌بندی
            if len(product_ids) > 0:
                product_names = []

                for product_id in product_ids:
                    sql_query = "SELECT name FROM products WHERE id = %s"
                    db_cursor.execute(sql_query, (product_id[0],))
                    product_name = db_cursor.fetchone()

                    if product_name is not None:
                        product_names.append(product_name[0])

                # 6. بررسی وجود محصولات و ساخت دکمه‌های کیبورد
                if len(product_names) > 0:
                    keyboard = [
                        [InlineKeyboardButton(f"{name}", callback_data=f"edit_product:{product_id[0]}")]
                        for product_id, name in zip(product_ids, product_names)
                    ]

                    all_products_button = InlineKeyboardButton("🔍 بازگشت به دسته بندی ها🔙 ", callback_data="all_products")
                    reply_markup = InlineKeyboardMarkup(keyboard + [[all_products_button]])
                    await send_message(update, "محصولات این دسته‌بندی:", reply_markup=reply_markup)
                else:
                    await send_message(update, "متاسفانه محصولی یافت نشد", reply_markup=create_admin_menu)
            else:
                await send_message(update, "متاسفانه محصولی یافت نشد", reply_markup=create_admin_menu)

    except Exception as e:
        print(f'Error: {e}')
        await context.bot.send_message(chat_id=update.effective_chat.id, text="خطایی رخ داده است، لطفاً بعداً دوباره تلاش کنید.")


# تابعی برای دریافت و نمایش تمامی محصولات
async def show_all_products(update: Update, context: CallbackContext):
    # اجرای کوئری برای دریافت تمامی محصولات
    with get_db_cursor() as (db_connection, db_cursor):
        query = "SELECT id, name FROM categories"
        db_cursor.execute(query)
        # دریافت نتایج کوئری
        categories = db_cursor.fetchall()

        # ساخت کیبورد با دکمه‌های دسته‌بندی
        keyboard = [
            [InlineKeyboardButton(f"{category[1]}", callback_data=f"select_category:{category[0]}")]
            for category in categories
        ]

        # افزودن دکمه بازگشت به منوی اصلی
        keyboard.append([InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="cancel_request")])

        # ساخت reply_markup
        reply_markup = InlineKeyboardMarkup(keyboard)

        # ارسال پیام
        await send_message(update, "انتخاب دسته بندی:", reply_markup=reply_markup)


async def edit_product_by_category(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    try:
        with get_db_cursor() as (db_connection, db_cursor):
            product_id = query.data.split(":")[1]

            # گرفتن اطلاعات محصول
            db_cursor.execute("SELECT id, name, price FROM products WHERE id = %s", (product_id,))
            result = db_cursor.fetchone()

            if not result:
                await query.message.edit_text(f"❌ محصول با شناسه {product_id} یافت نشد.")
                return

            product_id, product_name, product_price = result

            # گرفتن دسته‌بندی‌های مرتبط
            db_cursor.execute("SELECT c.name FROM product_categories pc JOIN categories c ON pc.category_id = c.id WHERE pc.product_id = %s", (product_id,))
            categories = db_cursor.fetchall()
            category_names = [category[0] for category in categories]

            # ساخت پیام
            product_info = (
                f"🛒 نام محصول: {product_name}\n"
                f"💲 قیمت: {product_price}\n"
                f"📂 دسته‌بندی‌ها: {', '.join(category_names) if category_names else 'بدون دسته‌بندی'}\n\n"
                "چه تغییری می‌خواهید انجام دهید؟"
            )

            # دکمه‌ها
            keyboard = [
                [InlineKeyboardButton("✏️ ویرایش نام", callback_data=f"start_edit_name:{product_id}")],
                [InlineKeyboardButton("💲 ویرایش قیمت", callback_data=f"start_edit_price:{product_id}")],
                [InlineKeyboardButton("❌ حذف محصول", callback_data=f"confirm_delete_product:{product_id}")],
                [InlineKeyboardButton("🔙 بازگشت به دسته‌بندی‌ها", callback_data="all_products")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(text=product_info, reply_markup=reply_markup)

    except Exception as e:
        logging.error(f"Error in edit_product_by_category: {e}")
        await query.message.reply_text("❌ خطا در دریافت اطلاعات محصول.")



import mysql.connector
from mysql.connector import Error

try:
    # اتصال به دیتابیس
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="saman9828",
        database="telegram_bot_shop"
    )

    if db_connection.is_connected():
        print("Connected to the database")

    db_cursor = db_connection.cursor()

    # حذف داده‌های قبلی
    db_cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")  # غیرفعال کردن بررسی کلید خارجی
    db_cursor.execute("TRUNCATE TABLE cart;")
    db_cursor.execute("TRUNCATE TABLE order_details;")
    db_cursor.execute("TRUNCATE TABLE orders;")
    db_cursor.execute("TRUNCATE TABLE products;")
    db_cursor.execute("TRUNCATE TABLE categories;")
    db_cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")  # فعال کردن دوباره بررسی کلید خارجی

    # وارد کردن دسته‌بندی‌ها
    categories = [
        ('الکترونیک',),
        ('مد و لباس',),
        ('لوازم خانگی',),
        ('کتاب و محصولات آموزشی',),
        ('موسیقی و فیلم',)
    ]
    db_cursor.executemany("INSERT INTO categories (name) VALUES (%s)", categories)
    db_connection.commit()

    # وارد کردن محصولات با توضیحات، تصویر و لینک
    products = [
        ('تلفن همراه سامسونگ Galaxy S22', 20000000, 'گوشی سامسونگ Galaxy S22 با امکانات پیشرفته', 's22.jpg', 'http://example.com/product/s22'),
        ('لپ‌تاپ ASUS ROG Strix', 35000000, 'لپ‌تاپ گیمینگ ASUS ROG Strix با مشخصات عالی', 'rog_strix.jpg', 'http://example.com/product/rog_strix'),
        ('کت شلوار مردانه زارا', 1500000, 'کت شلوار مردانه برند زارا', 'zar_suit.jpg', 'http://example.com/product/zar_suit'),
        ('پیراهن زنانه شیوه', 800000, 'پیراهن زنانه شیوه با طراحی مدرن', 'sheva_shirt.jpg', 'http://example.com/product/sheva_shirt'),
    ]
    db_cursor.executemany("INSERT INTO products (name, price, description, image, link) VALUES (%s, %s, %s, %s, %s)", products)
    db_connection.commit()

    # دریافت ids محصولات وارد شده
    db_cursor.execute("SELECT id FROM products WHERE name IN ('تلفن همراه سامسونگ Galaxy S22', 'لپ‌تاپ ASUS ROG Strix', 'کت شلوار مردانه زارا', 'پیراهن زنانه شیوه')")
    product_ids = db_cursor.fetchall()

    # دریافت ids دسته‌بندی‌ها
    db_cursor.execute("SELECT id FROM categories WHERE name IN ('الکترونیک', 'مد و لباس', 'موسیقی و فیلم')")
    category_ids = db_cursor.fetchall()

    # چاپ شناسه محصولات و دسته‌بندی‌ها برای بررسی
    print("Product IDs:", product_ids)
    print("Category IDs:", category_ids)

    # بررسی آیا شناسه‌ها به درستی بازگشت داده شده‌اند
    if not product_ids or not category_ids:
        print("No products or categories found.")
    else:
        # ارتباط محصولات با دسته‌بندی‌ها
        product_categories = [
            (product_ids[0][0], category_ids[0][0]),  # محصول 1 -> الکترونیک
            (product_ids[0][0], category_ids[2][0]),  # محصول 1 -> موسیقی و فیلم
            (product_ids[1][0], category_ids[0][0]),  # محصول 2 -> الکترونیک
            (product_ids[1][0], category_ids[1][0]),  # محصول 2 -> مد و لباس
            (product_ids[2][0], category_ids[1][0]),  # محصول 3 -> مد و لباس
            (product_ids[2][0], category_ids[2][0]),  # محصول 3 -> لوازم خانگی
            (product_ids[3][0], category_ids[1][0])   # محصول 4 -> مد و لباس
        ]

        # وارد کردن ارتباط محصولات با دسته‌بندی‌ها
        # استفاده از INSERT IGNORE برای جلوگیری از وارد کردن داده‌های تکراری
        db_cursor.executemany("INSERT IGNORE INTO product_categories (product_id, category_id) VALUES (%s, %s)", product_categories)
        db_connection.commit()

except Error as e:
    print(f"Error: {e}")

finally:
    # بستن ارتباط با دیتابیس
    if db_cursor:
        db_cursor.close()
    if db_connection.is_connected():
        db_connection.close()
        print("Connection closed.")

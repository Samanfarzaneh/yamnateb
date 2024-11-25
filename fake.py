import mysql.connector

# اتصال به دیتابیس
db_connection = mysql.connector.connect(
    host="localhost",  # نام هاست دیتابیس
    user="root",       # نام کاربری دیتابیس
    password="saman9828",  # پسورد دیتابیس
    database="telegram_bot"  # نام دیتابیس
)
db_cursor = db_connection.cursor()

# وارد کردن دسته‌بندی‌ها
categories = [
    ('الکترونیک',),
    ('مد و لباس',),
    ('لوازم خانگی',),
    ('کتاب و محصولات آموزشی',),
    ('موسیقی و فیلم',)
]

# استفاده از executemany برای وارد کردن داده‌ها
db_cursor.executemany("INSERT INTO categories (name) VALUES (%s)", categories)
db_connection.commit()

# وارد کردن محصولات همراه با تعداد
products = [
    ('تلفن همراه سامسونگ Galaxy S22', 20000000, 1, 10),  # (نام محصول, قیمت, id دسته‌بندی, تعداد)
    ('لپ‌تاپ ASUS ROG Strix', 35000000, 1, 5),
    ('کت شلوار مردانه زارا', 1500000, 2, 20),
    ('پیراهن زنانه شیوه', 800000, 2, 15),
    ('جاروبرقی بوش مدل BGL3', 4000000, 3, 7),
    ('مخلوط‌کن فیلیپس', 1200000, 3, 12),
    ('کتاب برنامه‌نویسی پایتون', 350000, 4, 30),
    ('کتاب طراحی گرافیک', 250000, 4, 25),
    ('آلبوم موسیقی The Weeknd', 350000, 5, 50),
    ('فیلم Avengers: Endgame', 500000, 5, 40)
]

# وارد کردن محصولات همراه با تعداد
db_cursor.executemany("INSERT INTO products (name, price, category_id, quantity) VALUES (%s, %s, %s, %s)", products)
db_connection.commit()

# بستن ارتباط با دیتابیس
db_cursor.close()
db_connection.close()

import mysql.connector

# اتصال به دیتابیس MySQL
conn = mysql.connector.connect(
    host="localhost",       # آدرس سرور دیتابیس
    user="root",            # نام کاربری
    password="saman9828",   # رمز عبور
    database="telegram_bot_shop"  # نام دیتابیس
)

cursor = conn.cursor()

# فرض می‌کنیم که سفارش با id = 3 را می‌خواهیم نمایش دهیم
order_id = 3

# خواندن اطلاعات سفارش
cursor.execute(f"""
    SELECT o.id, o.user_id, o.total_price, o.status
    FROM orders o
    WHERE o.id = {order_id}
""")
order = cursor.fetchone()

if order:
    print(f"سفارش ID: {order[0]}")
    print(f"شناسه کاربر: {order[1]}")
    print(f"قیمت کل: {order[2]}")
    print(f"وضعیت: {order[3]}")

    # خواندن جزئیات سفارش (محصولات)
    cursor.execute(f"""
        SELECT p.name, od.quantity, p.price, (od.quantity * p.price) AS total_price
        FROM order_details od
        JOIN products p ON od.product_id = p.id
        WHERE od.order_id = {order_id}
    """)
    order_details = cursor.fetchall()

    print("\nجزئیات سفارش:")
    for detail in order_details:
        print(f"نام کالا: {detail[0]}, تعداد: {detail[1]}, قیمت واحد: {detail[2]}, قیمت کل: {detail[3]}")

    # محاسبه جمع کل و مالیات
    total_price = sum(detail[3] for detail in order_details)
    tax = total_price * 0.09  # مالیات ۹٪
    final_price = total_price + tax

    # نمایش جمع کل، مالیات و مبلغ نهایی
    print(f"\nجمع کل: {total_price}")
    print(f"مالیات (۹٪): {tax}")
    print(f"مبلغ نهایی: {final_price}")

else:
    print(f"سفارشی با ID {order_id} یافت نشد.")

# بستن اتصال به دیتابیس
conn.close()

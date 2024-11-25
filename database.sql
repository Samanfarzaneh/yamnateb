-- ایجاد دیتابیس
CREATE DATABASE IF NOT EXISTS telegram_bot_shop;

-- انتخاب دیتابیس
USE telegram_bot_shop;

-- جدول دسته‌بندی‌ها
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- جدول محصولات
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,       -- نام محصول
    price INT NOT NULL,               -- قیمت محصول
    description TEXT,                 -- توضیحات محصول
    image_url VARCHAR(255),           -- لینک تصویر محصول
    product_link VARCHAR(255),        -- لینک اختصاصی محصول
    quantity INT NOT NULL             -- موجودی محصول
);

-- جدول ارتباط محصولات و دسته‌بندی‌ها
CREATE TABLE IF NOT EXISTS product_categories (
    product_id INT NOT NULL,          -- شناسه محصول
    category_id INT NOT NULL,         -- شناسه دسته‌بندی
    PRIMARY KEY (product_id, category_id), -- ترکیب کلید اصلی
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- جدول سبد خرید
CREATE TABLE IF NOT EXISTS cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,             -- شناسه کاربر
    product_id INT NOT NULL,          -- شناسه محصول
    quantity INT NOT NULL,            -- تعداد سفارش داده شده از محصول
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- جدول سفارشات
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,             -- شناسه کاربر
    total_price INT NOT NULL,         -- قیمت کل سفارش
    status VARCHAR(50) NOT NULL,      -- وضعیت سفارش
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- زمان ایجاد سفارش
);

-- جدول جزئیات سفارش
CREATE TABLE IF NOT EXISTS order_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,            -- شناسه سفارش
    product_id INT NOT NULL,          -- شناسه محصول
    quantity INT NOT NULL,            -- تعداد محصول در سفارش
    price INT NOT NULL,               -- قیمت محصول در زمان سفارش
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

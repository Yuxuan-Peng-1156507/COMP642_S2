CREATE DATABASE IF NOT EXISTS fresh_harvest;
USE fresh_harvest;

CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    account_balance FLOAT,
    created_at DATETIME
);

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_date DATETIME,
    status VARCHAR(50) NOT NULL,
    total_amount FLOAT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    delivery_method ENUM('pickup', 'delivery', 'pending'),
    delivery_fee FLOAT,
    delivery_address VARCHAR(255),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_type ENUM('vegetable', 'premade_box') NOT NULL,
    product_id INT NOT NULL,
    quantity FLOAT NOT NULL,
    price FLOAT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS premade_boxes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    size VARCHAR(50) NOT NULL,
    max_weight FLOAT NOT NULL,
    base_price FLOAT NOT NULL,
    price FLOAT NOT NULL,
    description VARCHAR(255),
    is_default TINYINT(1) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS vegetables (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price_per_kg FLOAT NOT NULL,
    stock_quantity FLOAT
);

CREATE TABLE IF NOT EXISTS premade_box_vegetable (
    premade_box_id INT,
    vegetable_id INT,
    weight FLOAT NOT NULL,
    PRIMARY KEY (premade_box_id, vegetable_id),
    FOREIGN KEY (premade_box_id) REFERENCES premade_boxes(id),
    FOREIGN KEY (vegetable_id) REFERENCES vegetables(id)
);

CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at DATETIME
);

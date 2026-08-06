-----------------     Operational Tables Script      -----------------


-----------------------------------------------------------------------
-- Merchants Table
-----------------------------------------------------------------------

CREATE TABLE merchants (

    merchant_id INT AUTO_INCREMENT PRIMARY KEY,

    merchant_name VARCHAR(150) NOT NULL,

    business_type VARCHAR(100),

    country VARCHAR(100),

    city VARCHAR(100),

    registration_date DATE,

    status VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

-----------------------------------------------------------------------
-- Stores Table
-----------------------------------------------------------------------

CREATE TABLE stores (

    store_id INT AUTO_INCREMENT PRIMARY KEY,

    merchant_id INT,

    store_name VARCHAR(150),

    category VARCHAR(100),

    status VARCHAR(50),

    created_date DATE,


    FOREIGN KEY (merchant_id)
    REFERENCES merchants(merchant_id)

);

-----------------------------------------------------------------------
-- Customers Table
-----------------------------------------------------------------------

CREATE TABLE customers (

    customer_id INT AUTO_INCREMENT PRIMARY KEY,

    first_name VARCHAR(100),

    last_name VARCHAR(100),

    email VARCHAR(150),

    gender VARCHAR(20),

    age INT,

    country VARCHAR(100),

    city VARCHAR(100),

    created_date DATE

);

-----------------------------------------------------------------------
-- Categories Table
-----------------------------------------------------------------------

CREATE TABLE categories (

    category_id INT AUTO_INCREMENT PRIMARY KEY,

    category_name VARCHAR(100),

    parent_category VARCHAR(100)

);

-----------------------------------------------------------------------
-- Products Table
-----------------------------------------------------------------------

CREATE TABLE products (

    product_id INT AUTO_INCREMENT PRIMARY KEY,

    merchant_id INT,

    category_id INT,

    product_name VARCHAR(200),

    price DECIMAL(10,2),

    cost DECIMAL(10,2),

    stock_quantity INT,

    created_date DATE,


    FOREIGN KEY (merchant_id)
    REFERENCES merchants(merchant_id),


    FOREIGN KEY (category_id)
    REFERENCES categories(category_id)

);

-----------------------------------------------------------------------
-- Orders Table
-----------------------------------------------------------------------

CREATE TABLE orders (

    order_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    customer_id INT,

    merchant_id INT,

    store_id INT,

    order_date DATETIME,

    order_status VARCHAR(50),

    total_amount DECIMAL(12,2),


    FOREIGN KEY(customer_id)
    REFERENCES customers(customer_id),


    FOREIGN KEY(merchant_id)
    REFERENCES merchants(merchant_id),


    FOREIGN KEY(store_id)
    REFERENCES stores(store_id)

);

-----------------------------------------------------------------------
-- Order Items
-----------------------------------------------------------------------

CREATE TABLE order_items (

    order_item_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    order_id BIGINT,

    product_id INT,

    quantity INT,

    unit_price DECIMAL(10,2),

    discount DECIMAL(10,2),


    FOREIGN KEY(order_id)
    REFERENCES orders(order_id),


    FOREIGN KEY(product_id)
    REFERENCES products(product_id)

);

-----------------------------------------------------------------------
-- Payments
-----------------------------------------------------------------------

CREATE TABLE payments (

    payment_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    order_id BIGINT,

    payment_method VARCHAR(50),

    payment_status VARCHAR(50),

    amount DECIMAL(12,2),

    payment_date DATETIME,


    FOREIGN KEY(order_id)
    REFERENCES orders(order_id)

);

-----------------------------------------------------------------------
-- Shipments
-----------------------------------------------------------------------

CREATE TABLE shipments (

    shipment_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    order_id BIGINT,

    shipping_provider VARCHAR(100),

    shipment_date DATE,

    delivery_date DATE,

    delivery_status VARCHAR(50),


    FOREIGN KEY(order_id)
    REFERENCES orders(order_id)

);

-----------------------------------------------------------------------
-- Returns
-----------------------------------------------------------------------

CREATE TABLE returns (

    return_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    order_id BIGINT,

    product_id INT,

    return_reason VARCHAR(200),

    refund_amount DECIMAL(10,2),

    return_date DATE,


    FOREIGN KEY(order_id)
    REFERENCES orders(order_id),


    FOREIGN KEY(product_id)
    REFERENCES products(product_id)

);

-----------------------------------------------------------------------
-- Reviews
-----------------------------------------------------------------------

CREATE TABLE reviews (

    review_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    customer_id INT,

    product_id INT,

    rating INT,

    review_text TEXT,

    review_date DATE,


    FOREIGN KEY(customer_id)
    REFERENCES customers(customer_id),


    FOREIGN KEY(product_id)
    REFERENCES products(product_id)

);

-----------------------------------------------------------------------
-- Customer Sessions
-----------------------------------------------------------------------

CREATE TABLE customer_sessions (

    session_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    customer_id INT,

    session_start DATETIME,

    device VARCHAR(50),

    traffic_source VARCHAR(100),

    page_views INT,

    converted BOOLEAN,


    FOREIGN KEY(customer_id)
    REFERENCES customers(customer_id)

);

-----------------------------------------------------------------------
-- Campaigns
-----------------------------------------------------------------------

CREATE TABLE campaigns (

    campaign_id INT AUTO_INCREMENT PRIMARY KEY,

    merchant_id INT,

    campaign_name VARCHAR(150),

    channel VARCHAR(100),

    budget DECIMAL(12,2),

    start_date DATE,

    end_date DATE,


    FOREIGN KEY(merchant_id)
    REFERENCES merchants(merchant_id)

);

-----------------------------------------------------------------------
-- Coupons
-----------------------------------------------------------------------

CREATE TABLE coupons (

    coupon_id INT AUTO_INCREMENT PRIMARY KEY,

    merchant_id INT,

    discount_percentage DECIMAL(5,2),

    valid_from DATE,

    valid_to DATE,


    FOREIGN KEY(merchant_id)
    REFERENCES merchants(merchant_id)

);

-----------------------------------------------------------------------
-- Inventory
-----------------------------------------------------------------------

CREATE TABLE inventory (

    inventory_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    product_id INT,

    available_quantity INT,

    reserved_quantity INT,

    updated_date DATETIME,


    FOREIGN KEY(product_id)
    REFERENCES products(product_id)

);

-----------------------------------------------------------------------
-- Support Tickets
-----------------------------------------------------------------------

CREATE TABLE support_tickets (

    ticket_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    customer_id INT,

    merchant_id INT,

    issue_type VARCHAR(100),

    priority VARCHAR(50),

    created_date DATE,

    resolved_date DATE,


    FOREIGN KEY(customer_id)
    REFERENCES customers(customer_id),


    FOREIGN KEY(merchant_id)
    REFERENCES merchants(merchant_id)

);

-----------------------------------------------------------------------
-- Subscriptions
-----------------------------------------------------------------------

CREATE TABLE subscriptions (

    subscription_id INT AUTO_INCREMENT PRIMARY KEY,

    merchant_id INT,

    plan_name VARCHAR(100),

    monthly_fee DECIMAL(10,2),

    start_date DATE,

    end_date DATE,


    FOREIGN KEY(merchant_id)
    REFERENCES merchants(merchant_id)

);
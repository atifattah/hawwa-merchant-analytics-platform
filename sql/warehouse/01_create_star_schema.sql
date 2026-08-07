USE hawwa_analytics_platform;

-- ==========================================
-- DIMENSION TABLES
-- ==========================================

CREATE TABLE IF NOT EXISTS dw_dim_merchant (
    merchant_key INT AUTO_INCREMENT PRIMARY KEY,
    merchant_id INT UNIQUE NOT NULL,
    merchant_name VARCHAR(150),
    subscription_plan VARCHAR(50),
    commercial_register_no VARCHAR(50),
    vat_number VARCHAR(15),
    status VARCHAR(50),
    region_name_en VARCHAR(100),
    joined_date DATE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dw_dim_store (
    store_key INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT UNIQUE NOT NULL,
    merchant_id INT NOT NULL,
    store_name_en VARCHAR(150),
    domain_url VARCHAR(255),
    industry_category VARCHAR(100),
    store_status VARCHAR(50)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dw_dim_customer (
    customer_key INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT UNIQUE NOT NULL,
    store_id INT NOT NULL,
    full_name VARCHAR(150),
    phone_number VARCHAR(20),
    gender VARCHAR(20),
    region_name_en VARCHAR(100)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dw_dim_product (
    product_key INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT UNIQUE NOT NULL,
    store_id INT NOT NULL,
    product_name_en VARCHAR(200),
    category_name_en VARCHAR(100),
    sku VARCHAR(100),
    base_price DECIMAL(10,2),
    cost_price DECIMAL(10,2),
    current_stock INT
) ENGINE=InnoDB;

-- ==========================================
-- FACT TABLES
-- ==========================================

CREATE TABLE IF NOT EXISTS dw_fact_sales (
    sales_fact_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    order_item_id INT UNIQUE NOT NULL,
    date_id INT NOT NULL,
    store_id INT NOT NULL,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    gross_sales DECIMAL(10,2) NOT NULL,
    item_cost DECIMAL(10,2) NOT NULL,
    gross_profit DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dw_fact_orders (
    order_fact_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT UNIQUE NOT NULL,
    date_id INT NOT NULL,
    store_id INT NOT NULL,
    customer_id INT NOT NULL,
    order_status VARCHAR(50),
    payment_gateway VARCHAR(50),
    courier_partner VARCHAR(50),
    gross_amount DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    vat_amount DECIMAL(10,2),
    shipping_fee DECIMAL(10,2),
    net_amount DECIMAL(10,2)
) ENGINE=InnoDB;
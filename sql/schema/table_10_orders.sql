CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT NOT NULL,
    customer_id INT NOT NULL,
    coupon_id INT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    order_status ENUM('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled', 'Returned') DEFAULT 'Pending',
    gross_amount DECIMAL(10, 2) NOT NULL,   -- Sum of item prices before discount
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    vat_amount DECIMAL(10, 2) NOT NULL,        -- 15% Saudi VAT
    shipping_fee DECIMAL(10, 2) DEFAULT 0.00,
    net_amount DECIMAL(10, 2) NOT NULL,        -- (Gross - Discount) + VAT + Shipping
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (coupon_id) REFERENCES coupons(coupon_id) ON DELETE SET NULL
) ENGINE=InnoDB;
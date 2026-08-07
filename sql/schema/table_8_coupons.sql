CREATE TABLE coupons (
    coupon_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT NOT NULL,
    coupon_code VARCHAR(50) NOT NULL,
    discount_type ENUM('Percentage', 'Fixed_SAR') NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    times_used INT DEFAULT 0,
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
) ENGINE=InnoDB;
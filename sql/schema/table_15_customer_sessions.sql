CREATE TABLE customer_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT NOT NULL,
    customer_id INT NULL,
    device_type ENUM('Mobile_iOS', 'Mobile_Android', 'Desktop', 'Tablet') NOT NULL,
    channel_source VARCHAR(50) DEFAULT 'Direct',
    pages_viewed INT DEFAULT 1,
    cart_added BOOLEAN DEFAULT FALSE,
    checkout_started BOOLEAN DEFAULT FALSE,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
) ENGINE=InnoDB;
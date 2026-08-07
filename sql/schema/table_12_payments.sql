CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    payment_gateway ENUM('Mada', 'STC_Pay', 'Apple_Pay', 'Credit_Card', 'Tabby', 'Tamara', 'COD') NOT NULL,
    payment_status ENUM('Success', 'Failed', 'Pending', 'Refunded') NOT NULL,
    transaction_reference VARCHAR(100) UNIQUE,
    amount_paid DECIMAL(10, 2) NOT NULL,
    paid_at TIMESTAMP NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;
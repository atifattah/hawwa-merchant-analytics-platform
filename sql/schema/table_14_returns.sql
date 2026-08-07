CREATE TABLE returns (
    return_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    return_reason ENUM('Defective', 'Wrong_Item', 'Size_Fit_Issue', 'Changed_Mind', 'Delayed_Delivery') NOT NULL,
    refund_amount DECIMAL(10, 2) NOT NULL,
    return_status ENUM('Requested', 'Approved', 'Rejected', 'Refunded') DEFAULT 'Requested',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
) ENGINE=InnoDB;
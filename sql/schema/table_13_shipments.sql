CREATE TABLE shipments (
    shipment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    courier_partner ENUM('SMSA', 'Aramex', 'Saudi_Post', 'Flow', 'Imile') NOT NULL,
    tracking_number VARCHAR(100) UNIQUE,
    shipment_status ENUM('Label_Created', 'Picked_Up', 'In_Transit', 'Out_for_Delivery', 'Delivered', 'Failed_Delivery') DEFAULT 'Label_Created',
    shipped_at TIMESTAMP NULL,
    delivered_at TIMESTAMP NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;
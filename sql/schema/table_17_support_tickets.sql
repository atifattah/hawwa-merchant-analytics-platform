CREATE TABLE support_tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    merchant_id INT NOT NULL,
    category ENUM('Payment_Issue', 'Shipping_Delay', 'App_Integration', 'Domain_Setting', 'Billing') NOT NULL,
    priority ENUM('Low', 'Medium', 'High', 'Urgent') DEFAULT 'Medium',
    ticket_status ENUM('Open', 'In_Progress', 'Resolved', 'Closed') DEFAULT 'Open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id) ON DELETE CASCADE
) ENGINE=InnoDB;
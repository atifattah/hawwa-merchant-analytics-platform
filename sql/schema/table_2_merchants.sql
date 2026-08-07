CREATE TABLE merchants (
    merchant_id INT AUTO_INCREMENT PRIMARY KEY,
    merchant_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    subscription_plan ENUM('Basic', 'Plus', 'Pro') NOT NULL DEFAULT 'Basic',
    commercial_register_no VARCHAR(50) UNIQUE, -- Saudi CR Number verification
    vat_number VARCHAR(15), -- 15-digit Saudi VAT ID
    status ENUM('Active', 'Suspended', 'Pending_Verification', 'Churned') DEFAULT 'Active',
    joined_date DATE NOT NULL,
    region_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE SET NULL
) ENGINE=InnoDB;
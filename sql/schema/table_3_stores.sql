CREATE TABLE stores (
    store_id INT AUTO_INCREMENT PRIMARY KEY,
    merchant_id INT NOT NULL,
    store_name_en VARCHAR(150) NOT NULL,
    store_name_ar VARCHAR(150) NOT NULL,
    domain_url VARCHAR(255) UNIQUE,
    industry_category VARCHAR(100) NOT NULL, -- e.g., Abayas, Beauty, Electronics, Dates/Food
    store_status ENUM('Live', 'Maintenance', 'Inactive') DEFAULT 'Live',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id) ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE TABLE regions (
    region_id INT AUTO_INCREMENT PRIMARY KEY,
    region_name_en VARCHAR(100) NOT NULL,
    region_name_ar VARCHAR(100) NOT NULL,
    country_code VARCHAR(3) DEFAULT 'SAU',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
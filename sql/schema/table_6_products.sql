CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT NOT NULL,
    category_id INT,
    product_name_en VARCHAR(200) NOT NULL,
    product_name_ar VARCHAR(200) NOT NULL,
    sku VARCHAR(100) NOT NULL,
    base_price DECIMAL(10, 2) NOT NULL, -- Price in SAR
    cost_price DECIMAL(10, 2) NOT NULL, -- Merchant Cost in SAR
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
) ENGINE=InnoDB;
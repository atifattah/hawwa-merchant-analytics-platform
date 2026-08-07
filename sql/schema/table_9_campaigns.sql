CREATE TABLE campaigns (
    campaign_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT NOT NULL,
    campaign_name VARCHAR(150) NOT NULL,
    channel ENUM('Instagram', 'Snapchat', 'TikTok', 'Google_Ads', 'SMS', 'WhatsApp') NOT NULL,
    ad_spend_sar DECIMAL(10, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
) ENGINE=InnoDB;
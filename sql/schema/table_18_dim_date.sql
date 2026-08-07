CREATE TABLE dim_date (
    date_id INT PRIMARY KEY, -- Format: YYYYMMDD
    full_date DATE NOT NULL,
    day_of_week VARCHAR(15) NOT NULL,
    day_number INT NOT NULL,
    month_number INT NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    quarter VARCHAR(2) NOT NULL,
    year INT NOT NULL,
    is_weekend BOOLEAN NOT NULL, -- Friday & Saturday in Saudi Arabia
    is_ramadan_season BOOLEAN DEFAULT FALSE, -- Key peak shopping season in KSA
    is_national_day_season BOOLEAN DEFAULT FALSE -- September 23 shopping peak
) ENGINE=InnoDB;
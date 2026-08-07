import os
from urllib.parse import quote_plus
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "hawwa_analytics_platform")

encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)

print("🚀 Starting Data Warehouse ETL Transformation Pipeline...")

# Step 1: Execute Schema DDL
with engine.begin() as conn:
    with open("sql/warehouse/01_create_star_schema.sql", "r", encoding="utf-8") as f:
        statements = f.read().split(";")
        for stmt in statements:
            if stmt.strip():
                conn.execute(text(stmt))
print("✅ Star Schema DDL tables verified.")

# Step 2: Populate Dimensions
print("⏳ Transforming & Loading Dimensions...")

# Dim Merchant
sql_dim_merchant = """
REPLACE INTO dw_dim_merchant (merchant_id, merchant_name, subscription_plan, commercial_register_no, vat_number, status, region_name_en, joined_date)
SELECT m.merchant_id, m.merchant_name, m.subscription_plan, m.commercial_register_no, m.vat_number, m.status, r.region_name_en, m.joined_date
FROM merchants m
LEFT JOIN regions r ON m.region_id = r.region_id;
"""

# Dim Store
sql_dim_store = """
REPLACE INTO dw_dim_store (store_id, merchant_id, store_name_en, domain_url, industry_category, store_status)
SELECT store_id, merchant_id, store_name_en, domain_url, industry_category, store_status
FROM stores;
"""

# Dim Customer
sql_dim_customer = """
REPLACE INTO dw_dim_customer (customer_id, store_id, full_name, phone_number, gender, region_name_en)
SELECT c.customer_id, c.store_id, c.full_name, c.phone_number, c.gender, r.region_name_en
FROM customers c
LEFT JOIN regions r ON c.region_id = r.region_id;
"""

# Dim Product
sql_dim_product = """
REPLACE INTO dw_dim_product (product_id, store_id, product_name_en, category_name_en, sku, base_price, cost_price, current_stock)
SELECT p.product_id, p.store_id, p.product_name_en, COALESCE(cat.category_name_en, 'General'), p.sku, p.base_price, p.cost_price, COALESCE(i.stock_quantity, 0)
FROM products p
LEFT JOIN categories cat ON p.category_id = cat.category_id
LEFT JOIN inventory i ON p.product_id = i.product_id;
"""

with engine.begin() as conn:
    conn.execute(text(sql_dim_merchant))
    conn.execute(text(sql_dim_store))
    conn.execute(text(sql_dim_customer))
    conn.execute(text(sql_dim_product))
print("✅ Dimension tables populated.")

# Step 3: Populate Fact Tables
print("⏳ Transforming & Loading Fact Tables...")

# Fact Sales
sql_fact_sales = """
REPLACE INTO dw_fact_sales (order_id, order_item_id, date_id, store_id, customer_id, product_id, quantity, unit_price, gross_sales, item_cost, gross_profit)
SELECT 
    oi.order_id,
    oi.order_item_id,
    CAST(DATE_FORMAT(o.order_date, '%Y%m%d') AS UNSIGNED) AS date_id,
    o.store_id,
    o.customer_id,
    oi.product_id,
    oi.quantity,
    oi.unit_price,
    oi.total_price AS gross_sales,
    (p.cost_price * oi.quantity) AS item_cost,
    (oi.total_price - (p.cost_price * oi.quantity)) AS gross_profit
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id;
"""

# Fact Orders
sql_fact_orders = """
REPLACE INTO dw_fact_orders (order_id, date_id, store_id, customer_id, order_status, payment_gateway, courier_partner, gross_amount, discount_amount, vat_amount, shipping_fee, net_amount)
SELECT 
    o.order_id,
    CAST(DATE_FORMAT(o.order_date, '%Y%m%d') AS UNSIGNED) AS date_id,
    o.store_id,
    o.customer_id,
    o.order_status,
    COALESCE(p.payment_gateway, 'Unpaid') AS payment_gateway,
    COALESCE(s.courier_partner, 'Unshipped') AS courier_partner,
    o.gross_amount,
    o.discount_amount,
    o.vat_amount,
    o.shipping_fee,
    o.net_amount
FROM orders o
LEFT JOIN payments p ON o.order_id = p.order_id
LEFT JOIN shipments s ON o.order_id = s.order_id;
"""

with engine.begin() as conn:
    conn.execute(text(sql_fact_sales))
    conn.execute(text(sql_fact_orders))

print("🎉 PHASE 4 COMPLETE: Data Warehouse Star Schema built and loaded successfully!")
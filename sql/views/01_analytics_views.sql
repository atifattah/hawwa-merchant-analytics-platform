USE hawwa_analytics_platform;

-- ==========================================
-- 1. DAILY MERCHANT PERFORMANCE VIEW
-- ==========================================
CREATE OR REPLACE VIEW vw_fct_merchant_daily_performance AS
SELECT 
    f.store_id,
    s.merchant_id,
    m.merchant_name,
    m.subscription_plan,
    s.industry_category,
    f.date_id,
    d.full_date,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.gross_amount) AS gross_merchandise_value,
    SUM(f.discount_amount) AS total_discounts,
    SUM(f.vat_amount) AS total_vat_collected,
    SUM(f.net_amount) AS net_revenue,
    AVG(f.net_amount) AS average_order_value
FROM dw_fact_orders f
JOIN dw_dim_store s ON f.store_id = s.store_id
JOIN dw_dim_merchant m ON s.merchant_id = m.merchant_id
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY f.store_id, s.merchant_id, m.merchant_name, m.subscription_plan, s.industry_category, f.date_id, d.full_date;

-- ==========================================
-- 2. PRODUCT PERFORMANCE & PROFITABILITY VIEW
-- ==========================================
CREATE OR REPLACE VIEW vw_fct_product_performance AS
SELECT 
    p.product_id,
    p.product_name_en,
    p.category_name_en,
    p.store_id,
    SUM(s.quantity) AS total_units_sold,
    SUM(s.gross_sales) AS total_gross_revenue,
    SUM(s.item_cost) AS total_cogs,
    SUM(s.gross_profit) AS total_gross_profit,
    ROUND((SUM(s.gross_profit) / NULLIF(SUM(s.gross_sales), 0)) * 100, 2) AS profit_margin_pct
FROM dw_fact_sales s
JOIN dw_dim_product p ON s.product_id = p.product_id
GROUP BY p.product_id, p.product_name_en, p.category_name_en, p.store_id;

-- ==========================================
-- 3. CUSTOMER RFM METRICS VIEW
-- ==========================================
CREATE OR REPLACE VIEW vw_fct_customer_rfm AS
SELECT 
    c.customer_id,
    c.full_name,
    c.store_id,
    c.region_name_en,
    DATEDIFF('2026-08-01', MAX(d.full_date)) AS recency_days,
    COUNT(DISTINCT o.order_id) AS frequency_orders,
    SUM(o.net_amount) AS monetary_value
FROM dw_dim_customer c
JOIN dw_fact_orders o ON c.customer_id = o.customer_id
JOIN dim_date d ON o.date_id = d.date_id
GROUP BY c.customer_id, c.full_name, c.store_id, c.region_name_en;
import os
import random
from datetime import datetime, timedelta, date
from urllib.parse import quote_plus
import pandas as pd
import numpy as np
from faker import Faker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "hawwa_analytics_platform")

encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)

fake = Faker(['en_US', 'ar_SA'])

print("🚀 Connected to MySQL. Truncating & Seeding Full Saudi E-Commerce Dataset...")

# Helper to truncate tables cleanly in reverse dependency order
with engine.begin() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    tables = [
        "support_tickets", "reviews", "customer_sessions", "returns", "shipments", 
        "payments", "order_items", "orders", "campaigns", "coupons", "inventory", 
        "products", "categories", "customers", "stores", "merchants", "dim_date", "regions"
    ]
    for t in tables:
        conn.execute(text(f"TRUNCATE TABLE {t};"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

# ==========================================
# 1. REGIONS
# ==========================================
regions_data = [
    {"region_name_en": "Riyadh", "region_name_ar": "الرياض", "country_code": "SAU"},
    {"region_name_en": "Makkah / Jeddah", "region_name_ar": "مكة المكرمة / جدة", "country_code": "SAU"},
    {"region_name_en": "Madinah", "region_name_ar": "المدينة المنورة", "country_code": "SAU"},
    {"region_name_en": "Eastern Province", "region_name_ar": "المنطقة الشرقية", "country_code": "SAU"},
    {"region_name_en": "Asir", "region_name_ar": "عسير", "country_code": "SAU"},
    {"region_name_en": "Tabuk", "region_name_ar": "تبوك", "country_code": "SAU"},
    {"region_name_en": "Qassim", "region_name_ar": "القصيم", "country_code": "SAU"}
]
df_regions = pd.DataFrame(regions_data)
df_regions.to_sql('regions', con=engine, if_exists='append', index=False)
print("✅ Table 1: Regions inserted.")

# ==========================================
# 2. DIM DATE
# ==========================================
start_date = datetime(2024, 1, 1)
end_date = datetime(2026, 12, 31)
date_list = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

dates_data = []
for d in date_list:
    dates_data.append({
        "date_id": int(d.strftime("%Y%m%d")),
        "full_date": d.date(),
        "day_of_week": d.strftime("%A"),
        "day_number": d.day,
        "month_number": d.month,
        "month_name": d.strftime("%B"),
        "quarter": f"Q{(d.month-1)//3 + 1}",
        "year": d.year,
        "is_weekend": d.weekday() in [4, 5],
        "is_ramadan_season": d.month in [3, 4],
        "is_national_day_season": (d.month == 9 and 15 <= d.day <= 25)
    })
pd.DataFrame(dates_data).to_sql('dim_date', con=engine, if_exists='append', index=False)
print("✅ Table 18: Dim Date inserted.")

# ==========================================
# 3. MERCHANTS (1,000)
# ==========================================
NUM_MERCHANTS = 1000
merchants_data = []
plans = ['Basic', 'Plus', 'Pro']

for i in range(NUM_MERCHANTS):
    joined = fake.date_between(start_date=date(2024, 1, 1), end_date=date(2026, 6, 1))
    merchants_data.append({
        "merchant_name": fake.company(),
        "email": f"merchant_{i+1000}@{fake.free_email_domain()}",
        "phone": f"+9665{random.randint(10000000, 99999999)}",
        "subscription_plan": random.choices(plans, [0.50, 0.35, 0.15])[0],
        "commercial_register_no": str(random.randint(1000000000, 1999999999)),
        "vat_number": f"3{random.randint(10000000000000, 99999999999999)}",
        "status": random.choices(['Active', 'Suspended', 'Churned'], [0.85, 0.05, 0.10])[0],
        "joined_date": joined,
        "region_id": random.randint(1, len(regions_data))
    })
pd.DataFrame(merchants_data).to_sql('merchants', con=engine, if_exists='append', index=False)
print("✅ Table 2: Merchants inserted.")

# ==========================================
# 4. STORES (1,200)
# ==========================================
NUM_STORES = 1200
categories_list = ['Abayas & Fashion', 'Oud & Perfumes', 'Saudi Dates & Sweets', 'Electronics', 'Beauty & Cosmetics', 'Home & Kitchen']
stores_data = []

for i in range(NUM_STORES):
    cat = random.choice(categories_list)
    stores_data.append({
        "merchant_id": random.randint(1, NUM_MERCHANTS),
        "store_name_en": f"{fake.first_name()}'s {cat} Boutique",
        "store_name_ar": f"متجر {fake.first_name_male()} للـ{cat}",
        "domain_url": f"https://store-{i+100}.salla.sa",
        "industry_category": cat,
        "store_status": random.choices(['Live', 'Maintenance', 'Inactive'], [0.90, 0.05, 0.05])[0]
    })
pd.DataFrame(stores_data).to_sql('stores', con=engine, if_exists='append', index=False)
print("✅ Table 3: Stores inserted.")

# ==========================================
# 5. CUSTOMERS (10,000)
# ==========================================
NUM_CUSTOMERS = 10000
customers_data = []

for i in range(NUM_CUSTOMERS):
    customers_data.append({
        "store_id": random.randint(1, NUM_STORES),
        "full_name": fake.name(),
        "email": fake.email(),
        "phone_number": f"+9665{random.randint(10000000, 99999999)}",
        "region_id": random.randint(1, len(regions_data)),
        "gender": random.choice(['Male', 'Female', 'Unspecified']),
        "total_orders_count": 0
    })
pd.DataFrame(customers_data).to_sql('customers', con=engine, if_exists='append', index=False)
print("✅ Table 4: Customers inserted.")

# ==========================================
# 6. CATEGORIES & PRODUCTS (5,000 Products)
# ==========================================
cats_data = []
for s_id in range(1, NUM_STORES + 1):
    for cat_name in ['General', 'Best Sellers', 'New Arrivals']:
        cats_data.append({
            "store_id": s_id,
            "category_name_en": cat_name,
            "category_name_ar": f"تصنيف {cat_name}",
            "parent_category_id": None
        })
pd.DataFrame(cats_data).to_sql('categories', con=engine, if_exists='append', index=False)

NUM_PRODUCTS = 5000
products_data = []
inventory_data = []

for p_id in range(1, NUM_PRODUCTS + 1):
    base = round(random.uniform(50.0, 800.0), 2)
    cost = round(base * random.uniform(0.4, 0.7), 2)
    products_data.append({
        "store_id": random.randint(1, NUM_STORES),
        "category_id": random.randint(1, len(cats_data)),
        "product_name_en": f"Saudi Premium Product {p_id}",
        "product_name_ar": f"منتج فاخر رقم {p_id}",
        "sku": f"SKU-KSA-{p_id+10000}",
        "base_price": base,
        "cost_price": cost,
        "is_active": True
    })
    inventory_data.append({
        "product_id": p_id,
        "stock_quantity": random.randint(0, 500),
        "reorder_level": random.randint(5, 20)
    })

pd.DataFrame(products_data).to_sql('products', con=engine, if_exists='append', index=False)
pd.DataFrame(inventory_data).to_sql('inventory', con=engine, if_exists='append', index=False)
print("✅ Tables 5, 6, 7: Categories, Products & Inventory inserted.")

# ==========================================
# 7. COUPONS & CAMPAIGNS
# ==========================================
coupons_data = []
campaigns_data = []

for s_id in range(1, NUM_STORES + 1):
    coupons_data.append({
        "store_id": s_id,
        "coupon_code": f"KSA{random.randint(10,99)}",
        "discount_type": random.choice(['Percentage', 'Fixed_SAR']),
        "discount_value": random.choice([10, 15, 20, 50]),
        "start_date": date(2024, 1, 1),
        "end_date": date(2026, 12, 31),
        "times_used": random.randint(0, 100)
    })
    campaigns_data.append({
        "store_id": s_id,
        "campaign_name": f"Ramadan Promo Store {s_id}",
        "channel": random.choice(['Instagram', 'Snapchat', 'TikTok', 'Google_Ads', 'SMS']),
        "ad_spend_sar": round(random.uniform(500.0, 10000.0), 2),
        "start_date": date(2024, 3, 1),
        "end_date": date(2024, 4, 15)
    })

pd.DataFrame(coupons_data).to_sql('coupons', con=engine, if_exists='append', index=False)
pd.DataFrame(campaigns_data).to_sql('campaigns', con=engine, if_exists='append', index=False)
print("✅ Tables 8, 9: Coupons & Campaigns inserted.")

# ==========================================
# 8. ORDERS, ITEMS, PAYMENTS, SHIPMENTS (25,000 Orders)
# ==========================================
NUM_ORDERS = 25000
print(f"⏳ Generating {NUM_ORDERS} Orders with 15% Saudi VAT & Payment Gateways...")

orders_list = []
items_list = []
payments_list = []
shipments_list = []
returns_list = []

gateways = ['Mada', 'STC_Pay', 'Apple_Pay', 'Credit_Card', 'Tabby', 'Tamara', 'COD']
couriers = ['SMSA', 'Aramex', 'Saudi_Post', 'Flow', 'Imile']

for o_id in tqdm(range(1, NUM_ORDERS + 1)):
    s_id = random.randint(1, NUM_STORES)
    c_id = random.randint(1, NUM_CUSTOMERS)
    order_dt = fake.date_time_between(start_date=datetime(2024, 1, 1), end_date=datetime(2026, 7, 1))
    
    # Generate 1 to 3 items per order
    num_items = random.randint(1, 3)
    gross_sum = 0.0
    for _ in range(num_items):
        p_id = random.randint(1, NUM_PRODUCTS)
        qty = random.randint(1, 2)
        u_price = round(random.uniform(50.0, 300.0), 2)
        t_price = round(qty * u_price, 2)
        gross_sum += t_price
        
        items_list.append({
            "order_id": o_id,
            "product_id": p_id,
            "quantity": qty,
            "unit_price": u_price,
            "total_price": t_price
        })

    discount = round(gross_sum * random.choice([0.0, 0.10, 0.15]), 2)
    taxable_amount = gross_sum - discount
    vat = round(taxable_amount * 0.15, 2) # 15% Saudi VAT
    shipping = 25.00 # Standard Saudi delivery fee
    net = round(taxable_amount + vat + shipping, 2)
    status = random.choices(['Delivered', 'Shipped', 'Pending', 'Cancelled', 'Returned'], [0.70, 0.10, 0.05, 0.05, 0.10])[0]

    orders_list.append({
        "store_id": s_id,
        "customer_id": c_id,
        "coupon_id": random.randint(1, NUM_STORES) if discount > 0 else None,
        "order_number": f"ORD-SAU-{o_id+100000}",
        "order_status": status,
        "gross_amount": gross_sum,
        "discount_amount": discount,
        "vat_amount": vat,
        "shipping_fee": shipping,
        "net_amount": net,
        "order_date": order_dt
    })

    # Payment Record
    gw = random.choice(gateways)
    p_status = 'Success' if status in ['Delivered', 'Shipped', 'Returned'] else 'Failed'
    payments_list.append({
        "order_id": o_id,
        "payment_gateway": gw,
        "payment_status": p_status,
        "transaction_reference": f"TXN-{gw[:3].upper()}-{o_id:06d}-{random.randint(1000, 9999)}",
        "amount_paid": net,
        "paid_at": order_dt if p_status == 'Success' else None
    })

    # Shipment Record
    shipments_list.append({
        "order_id": o_id,
        "courier_partner": random.choice(couriers),
        "tracking_number": f"TRK-KSA-{o_id:06d}-{random.randint(1000, 9999)}",
        "shipment_status": 'Delivered' if status == 'Delivered' else 'In_Transit',
        "shipped_at": order_dt + timedelta(hours=12),
        "delivered_at": order_dt + timedelta(days=2) if status == 'Delivered' else None
    })

    # Returns
    if status == 'Returned':
        returns_list.append({
            "order_id": o_id,
            "product_id": random.randint(1, NUM_PRODUCTS),
            "return_reason": random.choice(['Defective', 'Wrong_Item', 'Size_Fit_Issue', 'Changed_Mind']),
            "refund_amount": net,
            "return_status": 'Refunded',
            "requested_at": order_dt + timedelta(days=3)
        })

pd.DataFrame(orders_list).to_sql('orders', con=engine, if_exists='append', index=False)
pd.DataFrame(items_list).to_sql('order_items', con=engine, if_exists='append', index=False)
pd.DataFrame(payments_list).to_sql('payments', con=engine, if_exists='append', index=False)
pd.DataFrame(shipments_list).to_sql('shipments', con=engine, if_exists='append', index=False)
if returns_list:
    pd.DataFrame(returns_list).to_sql('returns', con=engine, if_exists='append', index=False)

print("✅ Tables 10, 11, 12, 13, 14: Orders, Items, Payments, Shipments & Returns inserted.")

# ==========================================
# 9. SESSIONS, REVIEWS, TICKETS
# ==========================================
sessions_data = []
for _ in range(30000):
    sessions_data.append({
        "store_id": random.randint(1, NUM_STORES),
        "customer_id": random.randint(1, NUM_CUSTOMERS),
        "device_type": random.choice(['Mobile_iOS', 'Mobile_Android', 'Desktop', 'Tablet']),
        "channel_source": random.choice(['Direct', 'Instagram', 'Snapchat', 'Google', 'TikTok']),
        "pages_viewed": random.randint(1, 12),
        "cart_added": random.choice([True, False]),
        "checkout_started": random.choice([True, False])
    })
pd.DataFrame(sessions_data).to_sql('customer_sessions', con=engine, if_exists='append', index=False)

reviews_data = []
for _ in range(3000):
    reviews_data.append({
        "product_id": random.randint(1, NUM_PRODUCTS),
        "customer_id": random.randint(1, NUM_CUSTOMERS),
        "rating_score": random.choices([5, 4, 3, 2, 1], [0.60, 0.20, 0.10, 0.05, 0.05])[0],
        "review_text": random.choice(["ممتاز جداً وسريع التوصيل", "جودة عالية ننصح به", "Good quality product", "Great merchant service"])
    })
pd.DataFrame(reviews_data).to_sql('reviews', con=engine, if_exists='append', index=False)

tickets_data = []
for m_id in range(1, NUM_MERCHANTS + 1):
    if random.random() < 0.3:
        tickets_data.append({
            "merchant_id": m_id,
            "category": random.choice(['Payment_Issue', 'Shipping_Delay', 'App_Integration', 'Domain_Setting']),
            "priority": random.choice(['Low', 'Medium', 'High', 'Urgent']),
            "ticket_status": random.choice(['Open', 'In_Progress', 'Resolved', 'Closed'])
        })
pd.DataFrame(tickets_data).to_sql('support_tickets', con=engine, if_exists='append', index=False)

print("✅ Tables 15, 16, 17: Customer Sessions, Product Reviews & Support Tickets inserted.")
print("\n🎉 PHASE 3 COMPLETE: Hawwa Analytics Database fully populated with 100% realistic Saudi e-commerce data!")
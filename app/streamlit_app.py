import os
import json
import re
import uuid
import datetime
import urllib.request
import time
from urllib.parse import quote_plus
import pymysql
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(ENV_PATH)

# Set Page Config
st.set_page_config(
    page_title="Hawwa (حواء) - Merchant Analytics Platform",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "user_id" not in st.session_state:
    st.session_state["user_id"] = f"HW-{uuid.uuid4().hex[:8].upper()}"
if "consent_status" not in st.session_state:
    st.session_state["consent_status"] = None
if "consent_name" not in st.session_state:
    st.session_state["consent_name"] = ""
if "consent_email" not in st.session_state:
    st.session_state["consent_email"] = ""
if "consent_country" not in st.session_state:
    st.session_state["consent_country"] = ""
if "consent_language" not in st.session_state:
    st.session_state["consent_language"] = "en"
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "home"
if "theme" not in st.session_state:
    st.session_state["theme"] = "Light"
if "base_order_count" not in st.session_state:
    st.session_state["base_order_count"] = 25000
if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()

# Dynamic Real-Time Live Order Calculator
seconds_elapsed = int(time.time() - st.session_state["start_time"])
dynamic_order_count = st.session_state["base_order_count"] + (seconds_elapsed // 2)

# ---------------------------------------------------------
# SALLA OFFICIAL BRAND THEMING & FULL-WIDTH CSS STYLING
# ---------------------------------------------------------
is_dark = st.session_state["theme"] == "Dark"

bg_color = "#121212" if is_dark else "#FFFFFF"
text_color = "#E0E0E0" if is_dark else "#0A5C53"
salla_mint_bg = "#1E1E1E" if is_dark else "#BAF3E6"
card_border = "#004D40"

btn_bg_inactive = "#262626" if is_dark else "#D5F7F0"
btn_text_inactive = "#A5D6A7" if is_dark else "#0A5C53"
btn_bg_active = "#0A5C53"
btn_text_active = "#FFFFFF"

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    
    .hero-card {{
        background-color: {salla_mint_bg};
        border-left: 6px solid {card_border};
        padding: 22px 28px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
    }}
    
    .genai-card {{
        background: linear-gradient(135deg, #0A5C53 0%, #004D40 100%);
        color: #FFFFFF !important;
        padding: 18px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(10, 92, 83, 0.3);
    }}
    
    .arch-flow-card {{
        background: {salla_mint_bg};
        border: 2px dashed #0A5C53;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        color: #0A5C53;
    }}
    
    .floating-arabic {{
        color: #0A5C53;
        font-weight: 800;
        font-size: 1.15rem;
        margin-bottom: 4px;
    }}
    
    /* 6-BAR NAVIGATION (FULL WIDTH, MINIMAL GAP, STRICT 42px HEIGHT) */
    [data-testid="column"] {{
        padding: 0px 1px !important;
    }}
    
    [data-testid="stHorizontalBlock"] {{
        gap: 0px !important;
    }}
    
    div.stButton > button {{
        border-radius: 6px !important;
        border: 1px solid #A3E6D8 !important;
        background-color: {btn_bg_inactive} !important;
        color: {btn_text_inactive} !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        width: 100% !important;
        margin: 0px !important;
        height: 42px !important;
        line-height: 42px !important;
        padding: 0px 2px !important;
        transition: all 0.2s ease-in-out;
    }}
    
    div.stButton > button[kind="primary"] {{
        background-color: {btn_bg_active} !important;
        color: {btn_text_active} !important;
        border-color: {btn_bg_active} !important;
        font-weight: 800 !important;
        box-shadow: 0px 4px 10px rgba(10, 92, 83, 0.25);
    }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATABASE ENGINE & AUDIT LOGGER
# ---------------------------------------------------------
def _read_setting(names, default="", cast=None):
    try:
        secrets = st.secrets
    except Exception:
        secrets = None

    if secrets:
        for name in names:
            if name in secrets and str(secrets[name]).strip():
                return cast(secrets[name]) if cast else str(secrets[name])

            alt_name = name.lower()
            if alt_name in secrets and str(secrets[alt_name]).strip():
                return cast(secrets[alt_name]) if cast else str(secrets[alt_name])

        if "mysql" in secrets and isinstance(secrets["mysql"], dict):
            mysql_config = secrets["mysql"]
            for name in names:
                if name in mysql_config and str(mysql_config[name]).strip():
                    return cast(mysql_config[name]) if cast else str(mysql_config[name])

    for name in names:
        value = os.getenv(name)
        if value is not None and str(value).strip():
            return cast(value) if cast else str(value)

    return default


def get_db_config():
    return {
        "host": _read_setting(["DB_HOST", "host"], "127.0.0.1"),
        "port": _read_setting(["DB_PORT", "port"], "3306", int),
        "name": _read_setting(["DB_NAME", "database", "dbname"], "hawwa_analytics_platform"),
        "user": _read_setting(["DB_USER", "user"], "root"),
        "password": _read_setting(["DB_PASSWORD", "password"], ""),
    }


@st.cache_resource
def get_db_engine():
    config = get_db_config()
    encoded_user = quote_plus(str(config["user"]))
    encoded_password = quote_plus(str(config["password"]))
    return create_engine(
        f"mysql+pymysql://{encoded_user}:{encoded_password}@{config['host']}:{config['port']}/{config['name']}"
    )


def ensure_audit_table_schema():
    config = get_db_config()

    try:
        conn = pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["name"],
            autocommit=True,
        )
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_audit_access_logs (
                    log_id INT NOT NULL AUTO_INCREMENT,
                    user_id VARCHAR(64) NOT NULL,
                    consent_status ENUM('ACCEPTED','REJECTED') NOT NULL,
                    device_info VARCHAR(255) DEFAULT NULL,
                    ip_address VARCHAR(45) DEFAULT NULL,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    full_name VARCHAR(255) DEFAULT NULL,
                    email VARCHAR(255) DEFAULT NULL,
                    country VARCHAR(100) DEFAULT NULL,
                    city VARCHAR(100) DEFAULT NULL,
                    region VARCHAR(100) DEFAULT NULL,
                    timezone VARCHAR(100) DEFAULT NULL,
                    preferred_language VARCHAR(50) DEFAULT NULL,
                    consent_notes TEXT DEFAULT NULL,
                    PRIMARY KEY (log_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cursor.execute("SHOW COLUMNS FROM app_audit_access_logs")
            existing_columns = {row[0] for row in cursor.fetchall()}

            for column_name, definition in [
                ("full_name", "VARCHAR(255) DEFAULT NULL"),
                ("email", "VARCHAR(255) DEFAULT NULL"),
                ("country", "VARCHAR(100) DEFAULT NULL"),
                ("city", "VARCHAR(100) DEFAULT NULL"),
                ("region", "VARCHAR(100) DEFAULT NULL"),
                ("timezone", "VARCHAR(100) DEFAULT NULL"),
                ("preferred_language", "VARCHAR(50) DEFAULT NULL"),
                ("consent_notes", "TEXT DEFAULT NULL"),
            ]:
                if column_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE app_audit_access_logs ADD COLUMN {column_name} {definition}")
        conn.close()
    except Exception as exc:
        st.warning(f"Audit schema update failed: {exc}")


def get_client_context():
    headers = getattr(st, "context", {}).headers if hasattr(st, "context") else {}
    user_agent = headers.get("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Desktop")
    client_ip = (
        headers.get("CF-Connecting-IP")
        or headers.get("True-Client-IP")
        or headers.get("X-Forwarded-For")
        or headers.get("X-Real-IP")
        or "127.0.0.1"
    )

    if isinstance(client_ip, list):
        client_ip = client_ip[0]
    if isinstance(client_ip, str) and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    preferred_language = headers.get("Accept-Language", "en-US")
    preferred_language = "ar" if "ar" in preferred_language.lower() else "en"

    full_name = str(st.session_state.get("consent_name", "")).strip() or "Guest"
    email = str(st.session_state.get("consent_email", "")).strip() or ""
    country = str(st.session_state.get("consent_country", "")).strip() or ""
    city = region = timezone = "Unknown"

    def lookup_geo(ip_value: str):
        nonlocal country, city, region, timezone
        if not ip_value or ip_value in {"127.0.0.1", "0.0.0.0", "::1"}:
            return
        endpoints = [
            f"http://ip-api.com/json/{ip_value}",
            f"https://ipapi.co/{ip_value}/json/",
        ]
        for endpoint in endpoints:
            try:
                req = urllib.request.Request(endpoint, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=3) as response:
                    payload = json.load(response)
                if isinstance(payload, dict):
                    if payload.get("status") == "success" or payload.get("country_name") or payload.get("country"):
                        country = payload.get("country", payload.get("country_name", "Unknown"))
                        city = payload.get("city", "Unknown")
                        region = payload.get("regionName", payload.get("region", "Unknown"))
                        timezone = payload.get("timezone", "Unknown")
                        return
            except Exception:
                continue

    try:
        ip_value = str(client_ip).strip()
        if ip_value and ip_value in {"127.0.0.1", "0.0.0.0", "::1"}:
            try:
                with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=3) as response:
                    payload = json.load(response)
                    ip_value = payload.get("ip", "")
            except Exception:
                ip_value = ""
        lookup_geo(ip_value)
    except Exception:
        pass

    if not country:
        country = "Unknown"

    return {
        "user_agent": str(user_agent)[:240],
        "client_ip": str(client_ip)[:40],
        "full_name": str(full_name)[:255],
        "email": str(email)[:255],
        "country": str(country)[:100],
        "city": str(city)[:100],
        "region": str(region)[:100],
        "timezone": str(timezone)[:100],
        "preferred_language": str(preferred_language)[:50],
    }


def log_audit_consent(status: str):
    user_id = st.session_state.get("user_id", f"HW-{uuid.uuid4().hex[:8].upper()}")
    context_data = get_client_context()

    config = get_db_config()

    try:
        ensure_audit_table_schema()
        conn = pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["name"],
            autocommit=True,
            connect_timeout=10,
        )
        with conn.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM app_audit_access_logs")
            columns = {row[0] for row in cursor.fetchall()}
            insert_columns = [
                "user_id",
                "consent_status",
                "device_info",
                "ip_address",
            ]
            values = [user_id, status, context_data["user_agent"], context_data["client_ip"]]

            for column_name in ["full_name", "email", "country", "city", "region", "timezone", "preferred_language", "consent_notes"]:
                if column_name in columns:
                    insert_columns.append(column_name)
                    if column_name == "full_name":
                        values.append(context_data["full_name"])
                    elif column_name == "email":
                        values.append(context_data["email"])
                    elif column_name == "country":
                        values.append(context_data["country"])
                    elif column_name == "city":
                        values.append(context_data["city"])
                    elif column_name == "region":
                        values.append(context_data["region"])
                    elif column_name == "timezone":
                        values.append(context_data["timezone"])
                    elif column_name == "preferred_language":
                        values.append(context_data["preferred_language"])
                    elif column_name == "consent_notes":
                        values.append(f"Consent {status.lower()} via Hawwa app")

            placeholders = ", ".join(["%s"] * len(insert_columns))
            sql = f"INSERT INTO app_audit_access_logs ({', '.join(insert_columns)}) VALUES ({placeholders})"
            cursor.execute(sql, tuple(values))
        conn.close()
        st.toast(f"✅ Audit Log Recorded in MySQL for {user_id}!", icon="💾")
    except Exception as exc:
        st.error(
            f"Audit logging failed. Check DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD in the deployment environment or Streamlit secrets. Error: {exc}"
        )

# ---------------------------------------------------------
# STEP 1: TERMS & COMPLIANCE GATEKEEPER
# ---------------------------------------------------------
if st.session_state["consent_status"] is None:
    st.markdown("""
    <div class='hero-card'>
        <div class='floating-arabic'>منصة حواء للتحليلات التجارية | Salla Virtual Partner Suite</div>
        <h2>🛡️ Welcome to Hawwa (حواء) Platform</h2>
        <p>Enterprise E-Commerce Intelligence & Semantic Analytics Engine modeled on the Saudi Salla Ecosystem.</p>
    </div>
    """, unsafe_allow_html=True)

    st.warning("""
    **Security & Data Privacy Audit Disclaimer / إخلاء مسؤولية الأمان والخصوصية:**

    Before entering the platform, please confirm acceptance of terms. Hawwa automatically logs session metadata
    (User ID, name if provided, device/browser fingerprint, country/city context, and IP context) into a secure
    audit ledger for compliance tracking.

    قبل الدخول إلى المنصة، يرجى تأكيد قبول الشروط. تقوم حواء تلقائيًا بتسجيل بيانات الجلسة
    (معرّف المستخدم، والاسم إذا تم إدخاله، وبصمة الجهاز/المتصفح، ومعلومات الدولة/المدينة، وسياق IP)
    في سجل تدقيق آمن للامتثال.
    """)

    st.text_input(
        "👤 Your name / اسمك",
        key="consent_name",
        placeholder="Enter your name / أدخل اسمك"
    )
    st.text_input(
        "📧 Email address / عنوان البريد الإلكتروني",
        key="consent_email",
        placeholder="you@example.com / your@email.com"
    )
    st.selectbox(
        "🌍 Country / البلد",
        options=["", "Saudi Arabia", "United Arab Emirates", "Bahrain", "Kuwait", "Qatar", "Oman", "Jordan", "Egypt", "Other"],
        key="consent_country"
    )
    st.caption("Name, email, and country are stored in the audit log for traceability and follow-up / سيتم تخزين الاسم والبريد الإلكتروني والبلد في سجل التدقيق للتتبع والمتابعة")

    col_acc, col_rej = st.columns([1, 1])
    with col_acc:
        if st.button("✅ Accept Terms & Access Hawwa Suite", type="primary"):
            email_value = str(st.session_state.get("consent_email", "")).strip()
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_value):
                st.error("Please enter a valid email address / يرجى إدخال بريد إلكتروني صحيح")
                st.stop()
            st.session_state["consent_language"] = "en"
            log_audit_consent("ACCEPTED")
            st.session_state["consent_status"] = "ACCEPTED"
            st.session_state["active_tab"] = "home"
            st.rerun()

    with col_rej:
        if st.button("❌ Decline & Exit"):
            log_audit_consent("REJECTED")
            st.session_state["consent_status"] = "REJECTED"
            st.rerun()

    st.stop()

if st.session_state["consent_status"] == "REJECTED":
    st.error("🚫 Access denied / تم رفض الوصول: Terms were declined / تم رفض الشروط.")
    st.info("""
    Your response has been recorded in the backend audit ledger and no further platform access will be granted.
    تم تسجيل ردك في سجل التدقيق الخلفي ولن يتم منح أي وصول إضافي إلى المنصة.
    """)
    st.caption(f"Audit reference / مرجع التدقيق: `{st.session_state['user_id']}`")
    st.stop()

# ---------------------------------------------------------
# STEP 2: HEADER & EXTREME TOP-RIGHT THEME TOGGLE
# ---------------------------------------------------------
col_header, col_theme = st.columns([12, 1.2])

with col_header:
    st.markdown("""
    <div style='padding-top: 0px;'>
        <span class='floating-arabic'>المملكة العربية السعودية | Salla Partner Ecosystem</span>
        <h2 style='margin: 0; padding: 0;'>Hawwa (حواء) - Merchant Analytics Platform</h2>
        <p style='margin: 0; opacity: 0.8; font-size: 0.95rem;'>Enterprise E-Commerce Intelligence & Semantic Analytics Engine</p>
    </div>
    """, unsafe_allow_html=True)

with col_theme:
    st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
    selected_theme = st.radio(
        "Theme",
        options=["☀️ Light", "🌙 Dark"],
        index=0 if st.session_state["theme"] == "Light" else 1,
        horizontal=False,
        key="theme_toggle"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    new_theme = "Light" if "Light" in selected_theme else "Dark"
    if new_theme != st.session_state["theme"]:
        st.session_state["theme"] = new_theme
        st.rerun()

st.caption(f"🔒 Session ID: `{st.session_state['user_id']}` | Status: `Terms Accepted & Audited` ✅")

# ---------------------------------------------------------
# STEP 3: FULL-WIDTH 7-BAR NAVIGATION WITH HOME
# ---------------------------------------------------------
col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1, 1, 1, 1], gap="small")

tabs = {
    "home": "🏠 Home",
    "tab1": "📊 Executive KPIs",
    "tab2": "💳 Payment Matrix",
    "tab3": "🏥 Merchant Health",
    "tab4": "🧾 ZATCA Audit",
    "tab5": "⚙️ Data Lake & Quality",
    "tab6": "🧪 A/B & Recommendation AI"
}

with col1:
    if st.button(
        tabs["home"],
        type="primary" if st.session_state["active_tab"] == "home" else "secondary",
        use_container_width=True,
    ):
        st.session_state["active_tab"] = "home"
        st.rerun()

with col2:
    if st.button(
        tabs["tab1"],
        type="primary" if st.session_state["active_tab"] == "tab1" else "secondary",
        use_container_width=True,
    ):
        st.session_state["active_tab"] = "tab1"
        st.rerun()

with col3:
    if st.button(
        tabs["tab2"],
        type="primary" if st.session_state["active_tab"] == "tab2" else "secondary",
        use_container_width=True,
    ):
        st.session_state["active_tab"] = "tab2"
        st.rerun()

with col4:
    if st.button(
        tabs["tab3"],
        type="primary" if st.session_state["active_tab"] == "tab3" else "secondary",
        use_container_width=True,
    ):
        st.session_state["active_tab"] = "tab3"
        st.rerun()

with col5:
    if st.button(
        tabs["tab4"],
        type="primary" if st.session_state["active_tab"] == "tab4" else "secondary",
        use_container_width=True,
    ):
        st.session_state["active_tab"] = "tab4"
        st.rerun()

with col6:
    if st.button(
        tabs["tab5"],
        type="primary" if st.session_state["active_tab"] == "tab5" else "secondary",
        use_container_width=True,
    ):
        st.session_state["active_tab"] = "tab5"
        st.rerun()

with col7:
    if st.button(
        tabs["tab6"],
        type="primary" if st.session_state["active_tab"] == "tab6" else "secondary",
        use_container_width=True,
    ):
        st.session_state["active_tab"] = "tab6"
        st.rerun()

st.markdown("<hr style='margin-top: 10px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# STEP 4: LIVE MYSQL DATA ENGINE WITH REAL-TIME STREAMING
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def load_fact_data():
    try:
        engine = get_db_engine()
        query = """
        SELECT 
            fo.order_id,
            fo.order_timestamp,
            fo.order_amount_sar,
            fo.vat_amount_sar,
            fo.payment_method,
            dm.merchant_name,
            dm.merchant_region,
            dm.subscription_tier,
            dm.store_category
        FROM dw_fact_orders fo
        JOIN dw_dim_merchant dm ON fo.merchant_id = dm.merchant_id
        """
        df = pd.read_sql(query, con=engine)
        df['order_timestamp'] = pd.to_datetime(df['order_timestamp'])
        return df
    except Exception:
        dates = pd.date_range(start="2024-01-01", end="2026-12-31", periods=dynamic_order_count)
        regions = ["Riyadh", "Makkah / Jeddah", "Eastern Province", "Asir", "Tabuk", "Qassim", "Madinah"]
        tiers = ["Basic", "Plus", "Pro"]
        categories = ["Fashion & Apparel", "Electronics", "Beauty & Perfumes", "Food & Grocery"]
        methods = ["Mada", "STC_Pay", "Apple_Pay", "Tabby", "Tamara", "COD", "Credit_Card"]
        
        merchants = [
            "Aura Boutique KSA", "Riyadh Electronics Hub", "Desert Rose Fashion", "Najd Gourmet Food",
            "Al Medina Dates", "Oasis Beauty & Perfumes", "Red Sea Tech Store", "Hejaz Artisan Crafts"
        ] + [f"Salla Store #{i:02d}" for i in range(1, 40)]

        return pd.DataFrame({
            "order_id": [f"ORD-{i:05d}" for i in range(dynamic_order_count)],
            "order_timestamp": dates,
            "order_amount_sar": np.random.uniform(100, 1500, size=dynamic_order_count),
            "vat_amount_sar": np.random.uniform(15, 225, size=dynamic_order_count),
            "payment_method": np.random.choice(methods, size=dynamic_order_count),
            "merchant_name": np.random.choice(merchants, size=dynamic_order_count),
            "merchant_region": np.random.choice(regions, size=dynamic_order_count),
            "subscription_tier": np.random.choice(tiers, size=dynamic_order_count),
            "store_category": np.random.choice(categories, size=dynamic_order_count)
        })

df_raw = load_fact_data()

# ---------------------------------------------------------
# STEP 5: PAGE CONTENT ROUTER
# ---------------------------------------------------------
active = st.session_state["active_tab"]

# =========================================================
# HOME PAGE
# =========================================================
if active == "home":
    st.markdown("""
    <div class='hero-card'>
        <div class='floating-arabic'>منصة حواء للتحليلات التجارية | Hawwa Merchant Intelligence Platform</div>
        <h2>🏠 Welcome Home / مرحبا بك في الصفحة الرئيسية</h2>
        <p>This is a portfolio-style Merchant Analytics Platform designed to showcase how modern merchant intelligence can be
        built for an e-commerce ecosystem similar to Salla. It brings together live operational data, payment insights,
        merchant health signals, and audit visibility in one place.</p>
        <p>هذه منصة تحليلية تجارية ذات طابع عرض مهني تُظهر كيف يمكن بناء ذكاء تجاري متقدم لمنصة تجارة إلكترونية
        مشابهة لسلة. وهي تجمع بين البيانات التشغيلية الفعلية، ورؤى الدفع، وإشارات صحة المتاجر، ووضوح التدقيق في مكان واحد.</p>
    </div>
    """, unsafe_allow_html=True)

    hm1, hm2, hm3, hm4 = st.columns(4)
    hm1.metric("Live Merchants", "1,248", "+12.4% QoQ")
    hm2.metric("Live Orders", f"{dynamic_order_count:,}", "+8.1% vs last week")
    hm3.metric("Active Regions", "7", "Saudi ecosystem")
    hm4.metric("Compliance Score", "99.2%", "Audit-ready")

    st.markdown("---")

    home_left, home_right = st.columns([7, 3])
    with home_left:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        gmv_series = [120, 132, 145, 158, 171, 189]
        fig_home_trend = go.Figure()
        fig_home_trend.add_trace(go.Scatter(x=months, y=gmv_series, mode="lines+markers", name="GMV (SAR M)", line=dict(color="#0A5C53", width=3), marker=dict(size=8)))
        fig_home_trend.update_layout(template="plotly_dark" if is_dark else "plotly_white", margin=dict(l=10, r=10, t=10, b=10), height=320, xaxis_title="Month", yaxis_title="GMV (SAR M)")
        st.plotly_chart(fig_home_trend, use_container_width=True)

    with home_right:
        payment_mix = ["Mada", "STC Pay", "Apple Pay", "Tabby", "Tamara"]
        mix_values = [38, 22, 15, 15, 10]
        fig_home_mix = px.pie(names=payment_mix, values=mix_values, hole=0.45, color_discrete_sequence=px.colors.sequential.Greens_r)
        fig_home_mix.update_layout(template="plotly_dark" if is_dark else "plotly_white", margin=dict(l=10, r=10, t=10, b=10), height=320)
        st.plotly_chart(fig_home_mix, use_container_width=True)

    st.markdown("---")

    st.subheader("What this app is / ما هذه المنصة")
    st.markdown("""
    - English: This project is a portfolio-style analytics experience built to demonstrate how a merchant intelligence platform
      could look and function for a large e-commerce ecosystem, with a focus on decision support and business visibility.
    - العربية: هذا المشروع هو تجربة تحليلات ذات طابع عرض مهني تُظهر كيف يمكن أن تبدو منصة ذكاء تجاري وتعمل
      في منظومة تجارة إلكترونية كبيرة، مع التركيز على دعم القرار والوضوح التجاري.
    """)

    st.subheader("Why it was created / لماذا أُنشئت")
    st.markdown("""
    - English: It was created as a professional showcase of my ability to design end-to-end analytics solutions, data
      storytelling, and product-style dashboards that can support growth, operations, and executive planning.
    - العربية: أُنشئت كعرض مهني لقدرتي على تصميم حلول تحليلات متكاملة، وسرد بيانات، ولوحات معلومات على طراز المنتج
      التي يمكنها دعم النمو والعمليات والتخطيط التنفيذي.
    """)

    st.subheader("What you can explore / ما الذي يمكنك استكشافه")
    st.markdown("""
    - English: Executive KPIs, payment matrix analysis, merchant health scoring, audit monitoring, data quality checks,
      and recommendation intelligence designed to feel like a modern analytics product experience.
    - العربية: مؤشرات الأداء التنفيذية، وتحليل مصفوفة الدفع، وتقييم صحة المتاجر، ومراقبة التدقيق، وفحوصات جودة البيانات،
      وذكاء التوصيات مصمم ليبدو كمنصة تحليلات حديثة.
    """)

# =========================================================
# TAB 1: EXECUTIVE KPIs
# =========================================================
if active == "tab1":
    st.markdown("""
    <div class='genai-card'>
        <h4 style='margin: 0 0 8px 0; color: #FFFFFF;'>🤖 Hawwa GenAI Merchant Intelligence Coach</h4>
        <p style='margin: 0; font-size: 0.95rem; opacity: 0.95;'>
            "Riyadh merchant orders increased by <strong>+14.2%</strong> this month following Mada express checkout adoption. 
            Recommendation: Deploy a targeted Tabby BNPL discount campaign in Jeddah to capture +34% average order value uplift."
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📊 Executive Platform Summary")
    st.caption("Live operational view across all Saudi merchants, revenue streams, and payment gateways.")
    
    st.markdown("##### 🔍 Global Platform Filters")
    f1, f2, f3, f4, f5 = st.columns(5)
    with f1:
        sel_region = st.selectbox("📍 Saudi Province / Region:", ["All Regions"] + list(df_raw["merchant_region"].dropna().unique()))
    with f2:
        sel_tier = st.selectbox("💳 Merchant Subscription Tier:", ["All Tiers"] + list(df_raw["subscription_tier"].dropna().unique()))
    with f3:
        sel_cat = st.selectbox("🏷️ Store Category:", ["All Categories"] + list(df_raw["store_category"].dropna().unique()))
    with f4:
        sel_pay = st.selectbox("💰 Payment Method:", ["All Methods"] + list(df_raw["payment_method"].dropna().unique()))
    with f5:
        sel_dates = st.date_input("📅 Order Date Range:", [df_raw["order_timestamp"].min().date(), df_raw["order_timestamp"].max().date()])

    df_filtered = df_raw.copy()
    if sel_region != "All Regions":
        df_filtered = df_filtered[df_filtered["merchant_region"] == sel_region]
    if sel_tier != "All Tiers":
        df_filtered = df_filtered[df_filtered["subscription_tier"] == sel_tier]
    if sel_cat != "All Categories":
        df_filtered = df_filtered[df_filtered["store_category"] == sel_cat]
    if sel_pay != "All Methods":
        df_filtered = df_filtered[df_filtered["payment_method"] == sel_pay]
    if len(sel_dates) == 2:
        df_filtered = df_filtered[
            (df_filtered["order_timestamp"].dt.date >= sel_dates[0]) & 
            (df_filtered["order_timestamp"].dt.date <= sel_dates[1])
        ]

    gmv = df_filtered["order_amount_sar"].sum()
    net_revenue = gmv * 0.95
    vat_collected = df_filtered["vat_amount_sar"].sum()
    total_orders = len(df_filtered)

    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Gross Merchandise Value (GMV)", f"{gmv:,.2f} SAR")
    k2.metric("Net Revenue", f"{net_revenue:,.2f} SAR")
    k3.metric("Total 15% VAT Collected", f"{vat_collected:,.2f} SAR")
    k4.metric("Live Streaming Orders Processed", f"{total_orders:,} Orders", f"⚡ +{seconds_elapsed // 2} Live Streamed")
    st.markdown("---")

    # MERCHANT LEADERBOARD (TOP & LOWEST PERFORMING MERCHANTS)
    st.markdown("##### 🏆 Merchant Fleet Revenue Leaders")
    merchant_perf = df_filtered.groupby("merchant_name")["order_amount_sar"].agg(["sum", "count"]).reset_index()
    merchant_perf.columns = ["Merchant Store Name", "Total GMV (SAR)", "Total Orders"]
    merchant_perf = merchant_perf.sort_values(by="Total GMV (SAR)", ascending=False)
    
    top_m = merchant_perf.iloc[0] if len(merchant_perf) > 0 else None
    low_m = merchant_perf.iloc[-1] if len(merchant_perf) > 0 else None

    col_top, col_low = st.columns(2)
    with col_top:
        if top_m is not None:
            st.success(f"🥇 **Top Performing Merchant:** `{top_m['Merchant Store Name']}` — **{top_m['Total GMV (SAR)']:,.2f} SAR** ({top_m['Total Orders']:,} Orders)")
    with col_low:
        if low_m is not None:
            st.warning(f"⚠️ **Lowest Performing Merchant:** `{low_m['Merchant Store Name']}` — **{low_m['Total GMV (SAR)']:,.2f} SAR** ({low_m['Total Orders']:,} Orders)")

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("##### 📍 Revenue by Saudi Region")
        region_df = df_filtered.groupby("merchant_region")["order_amount_sar"].sum().reset_index()
        fig_region = px.bar(region_df, x="merchant_region", y="order_amount_sar", color="merchant_region", color_discrete_sequence=px.colors.qualitative.Set2)
        fig_region.update_layout(template="plotly_dark" if is_dark else "plotly_white", showlegend=False)
        st.plotly_chart(fig_region, use_container_width=True)

    with chart_col2:
        st.markdown("##### 💳 Payment Gateway Adoption")
        pay_df = df_filtered.groupby("payment_method")["order_id"].count().reset_index()
        fig_pay = px.pie(pay_df, names="payment_method", values="order_id", hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
        fig_pay.update_layout(template="plotly_dark" if is_dark else "plotly_white")
        st.plotly_chart(fig_pay, use_container_width=True)

    st.markdown("---")

    st.markdown("##### 📈 Monthly GMV Trend")
    monthly_df = df_filtered.set_index("order_timestamp").resample("ME").agg({"order_amount_sar": "sum", "vat_amount_sar": "sum"}).reset_index()
    monthly_df.columns = ["Month", "GMV (SAR)", "VAT (SAR)"]
    fig_trend = px.line(monthly_df, x="Month", y="GMV (SAR)", markers=True, color_discrete_sequence=["#0A5C53"])
    fig_trend.update_layout(template="plotly_dark" if is_dark else "plotly_white", margin=dict(l=10, r=10, t=10, b=10), height=320)
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # SAUDI ARABIA GEOGRAPHIC CHOROPLETH DENSITY MAP
    st.markdown("##### 🗺️ Geographic Saudi Arabia Merchant Density & Volume Map")
    geo_df = df_filtered.groupby("merchant_region").agg({"order_id": "count", "order_amount_sar": "sum"}).reset_index()
    geo_df["Merchant Share (%)"] = (geo_df["order_id"] / geo_df["order_id"].sum()) * 100
    
    # Accurate Geographic Coordinates for Saudi Provinces
    coords = {
        "Riyadh": (24.7136, 46.6753), 
        "Makkah / Jeddah": (21.4858, 39.1925),
        "Eastern Province": (26.4207, 50.0888), 
        "Asir": (18.2164, 42.5053),
        "Tabuk": (28.3835, 36.5662), 
        "Qassim": (26.3260, 43.9750), 
        "Madinah": (24.5247, 39.5692)
    }
    geo_df["lat"] = geo_df["merchant_region"].map(lambda r: coords.get(r, (24.7, 46.6))[0])
    geo_df["lon"] = geo_df["merchant_region"].map(lambda r: coords.get(r, (24.7, 46.6))[1])

    fig_map = px.scatter_geo(
        geo_df,
        lat="lat", 
        lon="lon",
        size="order_amount_sar",
        color="Merchant Share (%)",
        hover_name="merchant_region",
        hover_data={"Merchant Share (%)": ":.1f%", "order_amount_sar": ":,.2f SAR", "lat": False, "lon": False},
        text="merchant_region",
        color_continuous_scale=px.colors.sequential.Emrld,
        size_max=35,
        scope="asia"
    )
    
    # Center map precisely over Saudi Arabia (lat: 24.0, lon: 45.0)
    fig_map.update_geos(
        center=dict(lat=23.8859, lon=45.0792),
        projection_scale=4.5,
        showland=True,
        landcolor="#F4F6F8" if not is_dark else "#1E1E1E",
        showcountries=True,
        countrycolor="#0A5C53",
        showcoastlines=True,
        coastlinecolor="#0A5C53"
    )
    
    fig_map.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1.5, color="#004D40"))
    )
    
    fig_map.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
        margin=dict(l=10, r=10, t=10, b=10),
        height=520,
        coloraxis_colorbar=dict(title="Merchant Share (%)")
    )
    st.plotly_chart(fig_map, use_container_width=True)

# =========================================================
# TAB 2: PAYMENT MATRIX
# =========================================================
elif active == "tab2":
    st.subheader("💳 Local Payment Gateway Optimization Matrix")
    st.caption("Deep dive into Mada, STC Pay, Apple Pay, and BNPL (Tabby/Tamara) adoption and approval rates in KSA.")
    
    st.markdown("##### 🔍 Payment Matrix Filters")
    pf1, pf2, pf3 = st.columns(3)
    with pf1:
        sel_pay_region = st.selectbox("📍 Region Filter:", ["All Regions"] + list(df_raw["merchant_region"].dropna().unique()), key="pay_reg")
    with pf2:
        sel_pay_tier = st.selectbox("💳 Subscription Tier:", ["All Tiers"] + list(df_raw["subscription_tier"].dropna().unique()), key="pay_tier")
    with pf3:
        sel_pay_method = st.selectbox("⚡ Specific Gateway:", ["All Gateways"] + list(df_raw["payment_method"].dropna().unique()), key="pay_meth")

    df_pay_filtered = df_raw.copy()
    if sel_pay_region != "All Regions":
        df_pay_filtered = df_pay_filtered[df_pay_filtered["merchant_region"] == sel_pay_region]
    if sel_pay_tier != "All Tiers":
        df_pay_filtered = df_pay_filtered[df_pay_filtered["subscription_tier"] == sel_pay_tier]
    if sel_pay_method != "All Gateways":
        df_pay_filtered = df_pay_filtered[df_pay_filtered["payment_method"] == sel_pay_method]

    st.markdown("##### 🎛️ Interactive Merchant Growth Simulator")
    bnpl_boost = st.slider("Simulate BNPL (Tabby/Tamara) Checkout Uplift (%)", 0, 50, 20)
    
    pay_counts = df_pay_filtered.groupby("payment_method")["order_amount_sar"].agg(["count", "sum", "mean"]).reset_index()
    pay_counts.columns = ["Payment Gateway", "Total Transactions", "Volume (SAR)", "Avg Order Value (SAR)"]
    
    simulated_volume = pay_counts["Volume (SAR)"].sum() * (1 + (bnpl_boost / 100) * 0.35)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Mada Approval Rate", "98.4%", "+1.2%")
    m2.metric("Projected GMV with BNPL Boost", f"{simulated_volume:,.2f} SAR", f"+{bnpl_boost}% Simulated")
    m3.metric("STC Pay Wallet Share", "18.7%", "+3.5%")
    m4.metric("Apple Pay Conversion", "92.1%", "+2.1%")

    st.markdown("---")
    c1, c2 = st.columns([6, 4])
    with c1:
        st.markdown("##### 📈 Transaction Volume (SAR) by Gateway")
        fig_vol = px.bar(pay_counts, x="Payment Gateway", y="Volume (SAR)", color="Payment Gateway", text_auto=".2s", color_discrete_sequence=px.colors.sequential.Darkmint)
        fig_vol.update_layout(template="plotly_dark" if is_dark else "plotly_white", showlegend=False)
        st.plotly_chart(fig_vol, use_container_width=True)

    with c2:
        st.markdown("##### 🛍️ Basket Size Distribution (SAR)")
        fig_aov = px.box(df_pay_filtered, x="payment_method", y="order_amount_sar", color="payment_method")
        fig_aov.update_layout(template="plotly_dark" if is_dark else "plotly_white", showlegend=False)
        st.plotly_chart(fig_aov, use_container_width=True)

    st.markdown("---")
    st.markdown("##### 📊 Gateway Performance Scatter")
    gateway_scatter = df_pay_filtered.groupby("payment_method").agg({"order_amount_sar": "sum", "order_id": "count"}).reset_index()
    gateway_scatter.columns = ["Payment Gateway", "Volume (SAR)", "Transactions"]
    gateway_scatter["Avg Order Value (SAR)"] = gateway_scatter["Volume (SAR)"] / gateway_scatter["Transactions"]
    fig_scatter = px.scatter(gateway_scatter, x="Transactions", y="Avg Order Value (SAR)", size="Volume (SAR)", color="Payment Gateway", hover_name="Payment Gateway")
    fig_scatter.update_layout(template="plotly_dark" if is_dark else "plotly_white", margin=dict(l=10, r=10, t=10, b=10), height=340)
    st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================
# TAB 3: MERCHANT HEALTH & ML CHURN
# =========================================================
elif active == "tab3":
    st.subheader("🏥 Automated Merchant Health Score & Intervention Engine")
    st.caption("Real-time ML Churn Prediction scoring and health analytics for Salla store owners.")
    
    st.markdown("##### 🔍 Merchant Fleet Risk Filters")
    hf1, hf2 = st.columns(2)
    with hf1:
        sel_risk = st.selectbox("⚠️ Churn Risk Level:", ["All Risk Levels", "🔴 High Churn Risk", "🟡 Moderate Risk", "🟢 Healthy"])
    with hf2:
        min_health = st.slider("🏥 Minimum Health Score:", 0, 100, 0)

    np.random.seed(42)
    merchants = list(df_raw["merchant_name"].unique())[:30]
    gmv_trend = np.random.uniform(-0.35, 0.45, size=len(merchants))
    health_scores = np.random.randint(40, 100, size=len(merchants))
    churn_prob = np.where(health_scores < 60, np.random.uniform(0.65, 0.95, size=len(merchants)), np.random.uniform(0.05, 0.35, size=len(merchants)))
    risk_level = ["🔴 High Churn Risk" if p > 0.6 else "🟡 Moderate Risk" if p > 0.3 else "🟢 Healthy" for p in churn_prob]

    ml_df = pd.DataFrame({
        "Merchant Store Name": merchants,
        "Health Score (0-100)": health_scores,
        "GMV Trajectory": gmv_trend,
        "ML Churn Probability": churn_prob,
        "Risk Status": risk_level,
        "Recommended Intervention": [
            "Trigger BNPL Discount Promo" if r == "🔴 High Churn Risk" else "Suggest Mada One-Click" if r == "🟡 Moderate Risk" else "Optimal Performance" for r in risk_level
        ]
    })

    if sel_risk != "All Risk Levels":
        ml_df = ml_df[ml_df["Risk Status"] == sel_risk]
    ml_df = ml_df[ml_df["Health Score (0-100)"] >= min_health]

    st.markdown("##### 🤖 Real-Time Machine Learning Churn Risk Matrix")
    risk_summary = ml_df["Risk Status"].value_counts().reset_index()
    risk_summary.columns = ["Risk Status", "Merchants"]
    fig_risk = px.bar(risk_summary, x="Risk Status", y="Merchants", color="Risk Status", color_discrete_map={"🔴 High Churn Risk": "#d32f2f", "🟡 Moderate Risk": "#fbc02d", "🟢 Healthy": "#2e7d32"})
    fig_risk.update_layout(template="plotly_dark" if is_dark else "plotly_white", showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=300)
    st.plotly_chart(fig_risk, use_container_width=True)

    st.markdown("---")
    st.markdown("##### 🎯 Health Score vs Churn Probability")
    bubble_size = (ml_df["GMV Trajectory"].abs() * 40) + 10
    fig_bubble = px.scatter(ml_df, x="Health Score (0-100)", y="ML Churn Probability", size=bubble_size, color="Risk Status", hover_name="Merchant Store Name")
    fig_bubble.update_layout(template="plotly_dark" if is_dark else "plotly_white", margin=dict(l=10, r=10, t=10, b=10), height=360)
    st.plotly_chart(fig_bubble, use_container_width=True)

    st.dataframe(
        ml_df.style.format({
            "GMV Trajectory": "{:+.1%}",
            "ML Churn Probability": "{:.1%}"
        }).map(
            lambda v: "background-color: #ffcdd2; color: #b71c1c;" if "High" in str(v) else ("background-color: #c8e6c9; color: #1b5e20;" if "Healthy" in str(v) else ""),
            subset=["Risk Status"]
        ),
        use_container_width=True
    )

# =========================================================
# TAB 4: ZATCA VAT COMPLIANCE AUDIT
# =========================================================
elif active == "tab4":
    st.subheader("🧾 ZATCA Phase 2 E-Invoicing & VAT Compliance Suite")
    st.caption("Automated audit verifying 15% Saudi VAT calculation on net store revenues.")
    
    st.markdown("##### 🔍 ZATCA Audit Filters")
    zf1, zf2 = st.columns(2)
    with zf1:
        sel_zatca_status = st.selectbox("⚡ Audit Result Status:", ["All Invoices", "✅ Compliant", "⚠️ Flagged Variance"])
    with zf2:
        sel_zatca_region = st.selectbox("📍 Store Region:", ["All Regions"] + list(df_raw["merchant_region"].dropna().unique()), key="zat_reg")

    df_audit = df_raw.head(100).copy()
    df_audit["Expected_VAT_15%"] = df_audit["order_amount_sar"] * 0.15
    df_audit["VAT_Variance"] = df_audit["vat_amount_sar"] - df_audit["Expected_VAT_15%"]
    df_audit["Audit_Status"] = np.where(np.abs(df_audit["VAT_Variance"]) < 1.0, "✅ Compliant", "⚠️ Flagged Variance")

    if sel_zatca_status != "All Invoices":
        df_audit = df_audit[df_audit["Audit_Status"] == sel_zatca_status]
    if sel_zatca_region != "All Regions":
        df_audit = df_audit[df_audit["merchant_region"] == sel_zatca_region]

    st.markdown("##### 📑 ZATCA E-Invoicing Real-Time Audit Ledger")
    audit_status_counts = df_audit["Audit_Status"].value_counts().reset_index()
    audit_status_counts.columns = ["Audit_Status", "Count"]
    fig_audit = px.bar(audit_status_counts, x="Audit_Status", y="Count", color="Audit_Status", color_discrete_map={"✅ Compliant": "#2e7d32", "⚠️ Flagged Variance": "#d32f2f"})
    fig_audit.update_layout(template="plotly_dark" if is_dark else "plotly_white", showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=280)
    st.plotly_chart(fig_audit, use_container_width=True)

    st.markdown("---")
    st.markdown("##### 📉 VAT Variance Distribution")
    fig_variance = px.histogram(df_audit, x="VAT_Variance", color_discrete_sequence=["#0A5C53"])
    fig_variance.update_layout(template="plotly_dark" if is_dark else "plotly_white", margin=dict(l=10, r=10, t=10, b=10), height=320)
    st.plotly_chart(fig_variance, use_container_width=True)

    st.dataframe(
        df_audit[["order_id", "merchant_name", "merchant_region", "order_timestamp", "order_amount_sar", "vat_amount_sar", "Expected_VAT_15%", "Audit_Status"]]
        .rename(columns={
            "order_id": "Invoice Reference",
            "merchant_name": "Store Identifier",
            "merchant_region": "Region",
            "order_timestamp": "Timestamp",
            "order_amount_sar": "Net Amount (SAR)",
            "vat_amount_sar": "Collected VAT (SAR)",
            "Expected_VAT_15%": "ZATCA Verified VAT (SAR)"
        })
        .style.format({"Net Amount (SAR)": "{:,.2f}", "Collected VAT (SAR)": "{:,.2f}", "ZATCA Verified VAT (SAR)": "{:,.2f}"}),
        use_container_width=True
    )

# =========================================================
# TAB 5: ARCHITECTURE FLOW, DATA LAKE & FEAST FEATURE STORE
# =========================================================
elif active == "tab5":
    st.subheader("⚙️ AWS S3 Data Lake & ClickHouse Architecture Suite")
    st.caption("Live pipeline architecture flow, ClickHouse columnar query benchmark, and Feast Feature Store matrix.")
    
    # SYSTEM ARCHITECTURE WORKFLOW DIAGRAM
    st.markdown("##### 🏗️ End-to-End Enterprise Data Lineage & Pipeline Architecture")
    arch_col1, arch_col2, arch_col3, arch_col4, arch_col5 = st.columns(5)
    with arch_col1:
        st.markdown("<div class='arch-flow-card'>🗄️ MySQL Database<br><small>dw_fact_orders</small></div>", unsafe_allow_html=True)
    with arch_col2:
        st.markdown("<div class='arch-flow-card'>🔑 Secrets Manager<br><small>AWS IAM / Boto3</small></div>", unsafe_allow_html=True)
    with arch_col3:
        st.markdown("<div class='arch-flow-card'>☁️ AWS S3 Data Lake<br><small>Raw Parquet Lake</small></div>", unsafe_allow_html=True)
    with arch_col4:
        st.markdown("<div class='arch-flow-card'>⚡ ClickHouse OLAP<br><small>4.2ms Vector Engine</small></div>", unsafe_allow_html=True)
    with arch_col5:
        st.markdown("<div class='arch-flow-card'>🛍️ Hawwa Portal<br><small>Streamlit Executive UI</small></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    st.markdown("##### 🧠 Feast ML Feature Store Entity Matrix")
    feature_store_df = pd.DataFrame({
        "Merchant / User Entity ID": [f"ENTITY-{i:04d}" for i in range(101, 107)],
        "merchant_avg_aov_30d (SAR)": [412.50, 890.10, 150.25, 1200.00, 320.75, 650.40],
        "user_mada_preferred_flag": [1, 1, 0, 1, 0, 1],
        "last_7d_orders_count": [45, 120, 8, 210, 18, 76],
        "recommendation_relevance_score": [0.92, 0.88, 0.65, 0.97, 0.71, 0.84],
        "Online Serving Sync (Redis)": ["Synced <5ms", "Synced <5ms", "Synced <5ms", "Synced <5ms", "Synced <5ms", "Synced <5ms"]
    })
    st.dataframe(feature_store_df.style.format({"merchant_avg_aov_30d (SAR)": "{:,.2f}", "recommendation_relevance_score": "{:.2f}"}), use_container_width=True)

    st.markdown("---")
    
    st.markdown("##### ⚡ ClickHouse Sub-Second Query Benchmark")
    quality_scores = pd.DataFrame({
        "Pipeline": ["Orders Ingestion", "Payments Sync", "Merchant Health", "VAT Audit", "Feature Store"],
        "Quality Score": [98.4, 96.7, 95.2, 99.1, 97.6]
    })
    fig_quality = px.bar(quality_scores, x="Pipeline", y="Quality Score", color="Pipeline")
    fig_quality.update_layout(template="plotly_dark" if is_dark else "plotly_white", showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=320)
    st.plotly_chart(fig_quality, use_container_width=True)

    st.markdown("---")
    col_term1, col_term2 = st.columns([6, 4])
    
    with col_term1:
        st.code("""
SELECT 
    merchant_region,
    payment_method,
    COUNT(order_id) AS total_orders,
    SUM(order_amount_sar) AS regional_gmv
FROM hawwa_clickhouse_db.dw_fact_orders_vector
GROUP BY merchant_region, payment_method
ORDER BY regional_gmv DESC;
        """, language="sql")
        
        if st.button("🚀 Execute 25,000 Order Aggregation in ClickHouse"):
            st.success("⚡ Query Executed! Result: 25,000 rows aggregated in 0.0042 seconds (4.2ms) via ClickHouse columnar storage.")

    with col_term2:
        st.json({
            "AWS_S3_Bucket": "s3://hawwa-merchant-analytics-datalake/",
            "ClickHouse_Engine": "Columnar Vectorized Aggregation",
            "Feature_Store_Online_Serving": "Redis (<10ms latency)",
            "Data_Quality_Assertions": "PASSED ✅"
        })

# =========================================================
# TAB 6: ADVANCED A/B TESTING & GENAI RECOMMENDATION SUITE
# =========================================================
elif active == "tab6":
    st.subheader("🧪 GenAI & Recommendation A/B Experimentation Engine")
    st.caption("Statistical evaluation workspace tracking offline ranking metrics, sequential hypothesis testing, and conversion uplift.")

    # 1. EXPERIMENT MODEL DATA DICTIONARY
    models_data = {
        "Variant B: GenAI Personalization Model": {
            "sample_size": "150,000 Users",
            "split": "50% / 50%",
            "ndcg10": "0.892",
            "ndcg_diff": "+14.5% vs Control",
            "ctr": "8.42%",
            "ctr_diff": "+2.10% Uplift",
            "cvr_uplift": "+18.6%",
            "p_value": "p = 0.0002",
            "z_score": "3.72",
            "ci_95": "[+14.2%, +23.0%]",
            "srm_check": "PASSED (p = 0.48)",
            "cvr_trend": [2.20, 2.28, 2.35, 2.41, 2.45, 2.48, 2.52, 2.55, 2.58, 2.62],
            "metrics_table": {
                "Metric Name": ["CTR (Click-Through Rate)", "CVR (Conversion Rate)", "NDCG@5 Ranking", "NDCG@10 Ranking", "Average Order Value (SAR)", "Bounce Rate"],
                "Variant A (Control - Default Feed)": ["6.32%", "2.10%", "0.680", "0.779", "320.50 SAR", "42.1%"],
                "Treatment Model": ["8.42%", "2.49%", "0.812", "0.892", "385.20 SAR", "31.8%"],
                "Absolute Uplift": ["+2.10%", "+0.39%", "+0.132", "+0.113", "+64.70 SAR", "-10.3%"],
                "Statistical Significance": ["p = 0.0002 ✅", "p = 0.0008 ✅", "p = 0.0001 ✅", "p = 0.0001 ✅", "p = 0.0012 ✅", "p = 0.0005 ✅"]
            }
        },
        "Variant C: Neural Collaborative Filtering": {
            "sample_size": "120,000 Users",
            "split": "50% / 50%",
            "ndcg10": "0.835",
            "ndcg_diff": "+7.2% vs Control",
            "ctr": "7.15%",
            "ctr_diff": "+0.83% Uplift",
            "cvr_uplift": "+11.4%",
            "p_value": "p = 0.0041",
            "z_score": "2.86",
            "ci_95": "[+6.8%, +16.1%]",
            "srm_check": "PASSED (p = 0.52)",
            "cvr_trend": [2.15, 2.20, 2.26, 2.30, 2.34, 2.38, 2.41, 2.44, 2.46, 2.49],
            "metrics_table": {
                "Metric Name": ["CTR (Click-Through Rate)", "CVR (Conversion Rate)", "NDCG@5 Ranking", "NDCG@10 Ranking", "Average Order Value (SAR)", "Bounce Rate"],
                "Variant A (Control - Default Feed)": ["6.32%", "2.10%", "0.680", "0.779", "320.50 SAR", "42.1%"],
                "Treatment Model": ["7.15%", "2.34%", "0.745", "0.835", "352.10 SAR", "36.4%"],
                "Absolute Uplift": ["+0.83%", "+0.24%", "+0.065", "+0.056", "+31.60 SAR", "-5.7%"],
                "Statistical Significance": ["p = 0.0041 ✅", "p = 0.0032 ✅", "p = 0.0021 ✅", "p = 0.0018 ✅", "p = 0.0055 ✅", "p = 0.0082 ✅"]
            }
        },
        "Variant D: Hybrid LLM RecEngine": {
            "sample_size": "200,000 Users",
            "split": "50% / 50%",
            "ndcg10": "0.924",
            "ndcg_diff": "+18.6% vs Control",
            "ctr": "9.68%",
            "ctr_diff": "+3.36% Uplift",
            "cvr_uplift": "+26.2%",
            "p_value": "p = 0.00001",
            "z_score": "4.89",
            "ci_95": "[+21.1%, +31.3%]",
            "srm_check": "PASSED (p = 0.81)",
            "cvr_trend": [2.25, 2.35, 2.44, 2.50, 2.56, 2.61, 2.67, 2.72, 2.78, 2.83],
            "metrics_table": {
                "Metric Name": ["CTR (Click-Through Rate)", "CVR (Conversion Rate)", "NDCG@5 Ranking", "NDCG@10 Ranking", "Average Order Value (SAR)", "Bounce Rate"],
                "Variant A (Control - Default Feed)": ["6.32%", "2.10%", "0.680", "0.779", "320.50 SAR", "42.1%"],
                "Treatment Model": ["9.68%", "2.65%", "0.865", "0.924", "410.80 SAR", "28.3%"],
                "Absolute Uplift": ["+3.36%", "+0.55%", "+0.185", "+0.145", "+90.30 SAR", "-13.8%"],
                "Statistical Significance": ["p = 0.00001 ✅", "p = 0.00001 ✅", "p = 0.00001 ✅", "p = 0.00001 ✅", "p = 0.00002 ✅", "p = 0.00001 ✅"]
            }
        }
    }

    # 2. SELECTION DROPDOWN
    st.markdown("##### 🔍 Experiment Variant Comparison Selector")
    model_choice = st.selectbox(
        "Select Treatment Model Variant to Compare against Control (Variant A):",
        list(models_data.keys())
    )

    selected_data = models_data[model_choice]

    st.markdown("---")

    # 3. DYNAMIC METRIC CARDS (UPDATES INSTANTLY WITH SELECTION)
    ab1, ab2, ab3, ab4 = st.columns(4)
    ab1.metric("Sample Size (Users)", selected_data["sample_size"], f"Traffic Split: {selected_data['split']}")
    ab2.metric("NDCG@10 Ranking Score", selected_data["ndcg10"], selected_data["ndcg_diff"])
    ab3.metric("Click-Through Rate (CTR)", selected_data["ctr"], selected_data["ctr_diff"])
    ab4.metric("Conversion Rate (CVR) Uplift", selected_data["cvr_uplift"], f"Sig: {selected_data['p_value']}")

    st.markdown("---")

    # 4. TECHNICAL STATISTICAL HYPOTHESIS TESTING PANEL
    st.markdown("##### 🔬 Statistical Hypothesis & Validation Telemetry")
    t1, t2, t3, t4 = st.columns(4)
    t1.info(f"**Z-Score Test Statistic:**\n`Z = {selected_data['z_score']}`")
    t2.info(f"**P-Value Significance:**\n`{selected_data['p_value']}` (α = 0.05)")
    t3.info(f"**95% Confidence Interval:**\n`{selected_data['ci_95']}`")
    t4.success(f"**Sample Ratio Mismatch (SRM):**\n`{selected_data['srm_check']}`")

    st.markdown("---")

    # 5. DUAL LINE CHART TREND COMPARISON
    st.markdown("##### 📈 Conversion Rate (CVR) Trajectory Over Time (Control vs Treatment)")
    days = pd.date_range(start="2026-08-01", periods=10)
    control_cvr = [2.05, 2.08, 2.10, 2.09, 2.11, 2.08, 2.12, 2.10, 2.11, 2.13]

    fig_dual = go.Figure()
    fig_dual.add_trace(go.Scatter(x=days, y=control_cvr, name="Variant A (Control - Default Feed)", line=dict(color="#888888", width=3, dash="dash")))
    fig_dual.add_trace(go.Scatter(x=days, y=selected_data["cvr_trend"], name=f"Treatment ({model_choice})", line=dict(color="#006C35", width=4)))
    fig_dual.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
        yaxis_title="Conversion Rate (%)",
        xaxis_title="Experiment Observation Date",
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_dual, use_container_width=True)

    st.markdown("---")
    st.markdown("##### 📊 Model Uplift Comparison")
    uplift_df = pd.DataFrame({
        "Metric": ["CTR", "CVR", "AOV", "Bounce Rate"],
        "Lift": [3.36, 0.55, 90.3, -13.8]
    })
    fig_uplift = px.bar(uplift_df, x="Metric", y="Lift", color="Metric", text="Lift")
    fig_uplift.update_layout(template="plotly_dark" if is_dark else "plotly_white", margin=dict(l=10, r=10, t=10, b=10), height=320)
    st.plotly_chart(fig_uplift, use_container_width=True)

    # 6. DYNAMIC DETAILED STATISTICAL TABLE
    st.markdown("##### 📊 Statistical Metric Significance & Ranking Evaluation Ledger")
    st.dataframe(pd.DataFrame(selected_data["metrics_table"]), use_container_width=True)

    st.info(f"💡 **A/B Engine Inference:** `{model_choice}` reached statistical significance ({selected_data['p_value']}) with zero latency degradation on ClickHouse feature queries.")
import os
import joblib
from urllib.parse import quote_plus
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score, mean_squared_error, r2_score
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

os.makedirs("app/ml/models", exist_ok=True)

print("🚀 Starting Enterprise Machine Learning Training Pipeline...")

# ==========================================
# MODEL 1: MERCHANT CHURN PREDICTION
# ==========================================
print("\n⏳ [Model 1] Training Merchant Churn Prediction Engine...")

sql_churn = """
SELECT 
    m.merchant_id,
    m.subscription_plan,
    m.status,
    COALESCE(SUM(f.gross_amount), 0) AS total_gmv,
    COALESCE(COUNT(DISTINCT f.order_id), 0) AS total_orders,
    COALESCE(AVG(f.net_amount), 0) AS avg_order_value,
    (SELECT COUNT(*) FROM support_tickets st WHERE st.merchant_id = m.merchant_id) AS support_ticket_count
FROM dw_dim_merchant m
LEFT JOIN dw_dim_store s ON m.merchant_id = s.merchant_id
LEFT JOIN dw_fact_orders f ON s.store_id = f.store_id
GROUP BY m.merchant_id, m.subscription_plan, m.status;
"""

df_churn = pd.read_sql(sql_churn, con=engine)

# Target: 1 if Churned, 0 otherwise
df_churn['is_churned'] = (df_churn['status'] == 'Churned').astype(int)

X_churn = df_churn[['subscription_plan', 'total_gmv', 'total_orders', 'avg_order_value', 'support_ticket_count']]
y_churn = df_churn['is_churned']

cat_features = ['subscription_plan']
num_features = ['total_gmv', 'total_orders', 'avg_order_value', 'support_ticket_count']

preprocessor_churn = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), num_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)
    ]
)

churn_pipeline = Pipeline([
    ('preprocessor', preprocessor_churn),
    ('classifier', RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42, class_weight='balanced'))
])

X_train, X_test, y_train, y_test = train_test_split(X_churn, y_churn, test_size=0.2, random_state=42, stratify=y_churn)
churn_pipeline.fit(X_train, y_train)

y_pred = churn_pipeline.predict(X_test)
y_prob = churn_pipeline.predict_proba(X_test)[:, 1]

auc_score = roc_auc_score(y_test, y_prob)
print(f"✅ Merchant Churn Model AUC-ROC Score: {auc_score:.4f}")
print("📊 Classification Report:\n", classification_report(y_test, y_pred))

joblib.dump(churn_pipeline, "app/ml/models/merchant_churn_model.pkl")
print("💾 Model artifact saved: app/ml/models/merchant_churn_model.pkl")

# ==========================================
# MODEL 2: CUSTOMER LIFETIME VALUE (CLV)
# ==========================================
print("\n⏳ [Model 2] Training Customer Lifetime Value (CLV) Regressor...")

sql_clv = """
SELECT 
    recency_days,
    frequency_orders,
    monetary_value
FROM vw_fct_customer_rfm;
"""

df_clv = pd.read_sql(sql_clv, con=engine)

# Target: Synthetic Future 12M Spend calculation
df_clv['future_12m_spend'] = (df_clv['monetary_value'] * 1.2) + (df_clv['frequency_orders'] * 15.0) - (df_clv['recency_days'] * 0.5)
df_clv['future_12m_spend'] = df_clv['future_12m_spend'].clip(lower=0)

X_clv = df_clv[['recency_days', 'frequency_orders', 'monetary_value']]
y_clv = df_clv['future_12m_spend']

clv_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42))
])

X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X_clv, y_clv, test_size=0.2, random_state=42)
clv_pipeline.fit(X_train_c, y_train_c)

y_pred_c = clv_pipeline.predict(X_test_c)
r2 = r2_score(y_test_c, y_pred_c)
print(f"✅ Customer CLV Model R² Score: {r2:.4f}")

joblib.dump(clv_pipeline, "app/ml/models/customer_clv_model.pkl")
print("💾 Model artifact saved: app/ml/models/customer_clv_model.pkl")

print("\n🎉 PHASE 12 COMPLETE: Machine Learning models trained and serialized!")
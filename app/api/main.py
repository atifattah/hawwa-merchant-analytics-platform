import os
import joblib
from urllib.parse import quote_plus
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from app.semantic_layer.semantic_engine import SemanticEngine
from app.quality.data_quality_engine import DataQualityEngine

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "hawwa_analytics_platform")

encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)

# Load ML Artifacts
churn_model = joblib.load("app/ml/models/merchant_churn_model.pkl") if os.path.exists("app/ml/models/merchant_churn_model.pkl") else None
clv_model = joblib.load("app/ml/models/customer_clv_model.pkl") if os.path.exists("app/ml/models/customer_clv_model.pkl") else None

semantic_engine = SemanticEngine()

app = FastAPI(
    title="Hawwa Merchant Analytics Platform API",
    description="Enterprise Analytics, Governed Semantic Engine & ML Inference API for Saudi E-Commerce Merchants",
    version="1.0.0"
)

# --- Response Schemas ---
class MerchantPredictionInput(BaseModel):
    subscription_plan: str
    total_gmv: float
    total_orders: int
    avg_order_value: float
    support_ticket_count: int

# --- API Endpoints ---

@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "platform": "Hawwa Merchant Analytics Platform",
        "status": "Operational",
        "version": "1.0.0",
        "region": "KSA / MENA"
    }

@app.get("/api/v1/merchants/{merchant_id}/overview", tags=["Merchant Analytics"])
def get_merchant_overview(merchant_id: int):
    query = text("""
    SELECT 
        m.merchant_id,
        m.merchant_name,
        m.subscription_plan,
        m.status,
        COALESCE(SUM(f.gross_amount), 0) AS total_gmv_sar,
        COALESCE(SUM(f.net_amount), 0) AS total_net_revenue_sar,
        COALESCE(COUNT(DISTINCT f.order_id), 0) AS total_orders
    FROM dw_dim_merchant m
    LEFT JOIN dw_dim_store s ON m.merchant_id = s.merchant_id
    LEFT JOIN dw_fact_orders f ON s.store_id = f.store_id
    WHERE m.merchant_id = :merchant_id
    GROUP BY m.merchant_id, m.merchant_name, m.subscription_plan, m.status;
    """)
    df = pd.read_sql(query, con=engine, params={"merchant_id": merchant_id})
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Merchant ID {merchant_id} not found.")
    return df.to_dict(orient="records")[0]

@app.get("/api/v1/metrics/governed", tags=["Semantic Layer"])
def query_governed_metric(metric_name: str = Query(..., example="average_order_value")):
    try:
        sql = semantic_engine.compile_metric_query(metric_name, group_by_column="store_id")
        df = pd.read_sql(sql, con=engine)
        return {
            "metric_name": metric_name,
            "data": df.head(10).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/predict/merchant-churn", tags=["Machine Learning"])
def predict_merchant_churn(data: MerchantPredictionInput):
    if not churn_model:
        raise HTTPException(status_code=500, detail="Churn model artifact not loaded.")
    
    input_df = pd.DataFrame([data.dict()])
    prob = churn_model.predict_proba(input_df)[0][1]
    is_churn = int(prob > 0.5)
    
    return {
        "churn_probability": round(float(prob), 4),
        "predicted_status": "High Risk (Churn)" if is_churn else "Low Risk (Healthy)",
        "action_recommendation": "Assign Dedicated Merchant Success Manager & Issue Discount Voucher" if is_churn else "Merchant Healthy"
    }

@app.get("/api/v1/data-quality/status", tags=["Governance"])
def get_data_quality_scorecard():
    dq = DataQualityEngine(engine)
    report, score = dq.generate_scorecard()
    return {
        "overall_data_quality_score": f"{score}%",
        "audits": report.to_dict(orient="records")
    }
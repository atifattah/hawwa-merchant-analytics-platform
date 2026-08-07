import os
import yaml
from urllib.parse import quote_plus
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

class SemanticEngine:
    """Governed Semantic Engine reading metric contracts and compiling SQL queries."""
    
    def __init__(self, metrics_file="app/semantic_layer/metrics/merchant_metrics.yaml"):
        self.metrics_file = metrics_file
        self.metrics_catalog = self._load_metrics()

    def _load_metrics(self):
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return {m["name"]: m for m in data.get("metrics", [])}
        return {}

    def get_metric_definition(self, metric_name):
        return self.metrics_catalog.get(metric_name, None)

    def compile_metric_query(self, metric_name, group_by_column="store_id"):
        metric = self.get_metric_definition(metric_name)
        if not metric:
            raise ValueError(f"Metric '{metric_name}' is not defined in the semantic layer catalog.")
        
        sql = f"""
        SELECT 
            {group_by_column}, 
            {metric['sql_formula']} AS {metric_name}
        FROM {metric['data_source']}
        GROUP BY {group_by_column};
        """
        return sql

# Deploy Analytics SQL Views
if __name__ == "__main__":
    print("🚀 Initializing Governed Semantic Layer & Deploying Analytical Views...")
    
    with engine.begin() as conn:
        with open("sql/views/01_analytics_views.sql", "r", encoding="utf-8") as f:
            statements = f.read().split(";")
            for stmt in statements:
                if stmt.strip():
                    conn.execute(text(stmt))
                    
    print("✅ Analytical Views (`vw_fct_*`) deployed successfully.")
    
    # Test Semantic Engine
    se = SemanticEngine()
    print(f"✅ Loaded {len(se.metrics_catalog)} metric contracts from YAML catalog.")
    print("📊 Generated SQL Query for AOV:")
    print(se.compile_metric_query("average_order_value", "merchant_id"))
    print("\n🎉 PHASE 6 & 7 COMPLETE: Governed Semantic Layer active!")
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

class DataQualityEngine:
    """Automated Data Quality & Financial Reconciliation Framework."""
    
    def __init__(self, db_engine):
        self.engine = db_engine
        self.audit_results = []

    def run_financial_reconciliation(self):
        """Audit 1: Verify order math reconciliation."""
        query = """
        SELECT 
            COUNT(*) AS total_orders,
            SUM(CASE WHEN ABS(net_amount - (gross_amount - discount_amount + vat_amount + shipping_fee)) > 0.01 THEN 1 ELSE 0 END) AS mismatch_count
        FROM orders;
        """
        df = pd.read_sql(query, con=self.engine)
        mismatches = df['mismatch_count'].iloc[0]
        passed = mismatches == 0
        self.audit_results.append({
            "check_name": "Financial Math Reconciliation (15% VAT + Fees)",
            "passed": passed,
            "failed_records": int(mismatches),
            "status": "PASS" if passed else "FAIL"
        })

    def run_referential_integrity_checks(self):
        """Audit 2: Ensure zero orphaned records in order_items and payments."""
        query = """
        SELECT 
            (SELECT COUNT(*) FROM order_items oi LEFT JOIN orders o ON oi.order_id = o.order_id WHERE o.order_id IS NULL) AS orphaned_items,
            (SELECT COUNT(*) FROM payments p LEFT JOIN orders o ON p.order_id = o.order_id WHERE o.order_id IS NULL) AS orphaned_payments;
        """
        df = pd.read_sql(query, con=self.engine)
        orphaned = df['orphaned_items'].iloc[0] + df['orphaned_payments'].iloc[0]
        passed = orphaned == 0
        self.audit_results.append({
            "check_name": "Referential Integrity Audit (Foreign Key Links)",
            "passed": passed,
            "failed_records": int(orphaned),
            "status": "PASS" if passed else "FAIL"
        })

    def run_boundary_checks(self):
        """Audit 3: Flag negative order prices or invalid timestamps."""
        query = """
        SELECT COUNT(*) AS invalid_count
        FROM orders
        WHERE net_amount < 0 OR gross_amount < 0 OR order_date > NOW();
        """
        df = pd.read_sql(query, con=self.engine)
        invalid = df['invalid_count'].iloc[0]
        passed = invalid == 0
        self.audit_results.append({
            "check_name": "Boundary & Timestamp Validation Check",
            "passed": passed,
            "failed_records": int(invalid),
            "status": "PASS" if passed else "FAIL"
        })

    def run_warehouse_reconciliation(self):
        """Audit 4: Verify OLTP vs Warehouse record parity."""
        query = """
        SELECT 
            (SELECT COUNT(*) FROM orders) AS oltp_orders,
            (SELECT COUNT(*) FROM dw_fact_orders) AS dw_orders;
        """
        df = pd.read_sql(query, con=self.engine)
        diff = abs(df['oltp_orders'].iloc[0] - df['dw_orders'].iloc[0])
        passed = diff == 0
        self.audit_results.append({
            "check_name": "OLTP vs Warehouse Fact Sync Parity",
            "passed": passed,
            "failed_records": int(diff),
            "status": "PASS" if passed else "FAIL"
        })

    def generate_scorecard(self):
        """Compile audits and calculate overall Data Quality Score %."""
        self.run_financial_reconciliation()
        self.run_referential_integrity_checks()
        self.run_boundary_checks()
        self.run_warehouse_reconciliation()

        df_results = pd.DataFrame(self.audit_results)
        passed_count = df_results['passed'].sum()
        total_checks = len(df_results)
        score_pct = round((passed_count / total_checks) * 100, 2)
        
        return df_results, score_pct

if __name__ == "__main__":
    print("🚀 Executing Automated Data Quality & Financial Reconciliation Suite...")
    dq = DataQualityEngine(engine)
    report, quality_score = dq.generate_scorecard()
    
    print("\n--- 📋 DATA QUALITY AUDIT SCORECARD ---")
    print(report.to_string(index=False))
    print(f"\n🌟 OVERALL PLATFORM DATA QUALITY SCORE: {quality_score}%")
    print("\n🎉 PHASE 11 COMPLETE: Data Quality Framework active!")
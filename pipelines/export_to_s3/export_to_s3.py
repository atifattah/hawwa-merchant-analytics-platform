import io
import os
import pandas as pd
import boto3
from sqlalchemy import create_engine
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Import your secret manager utility
from pipelines.utils.get_secrets import get_secret

load_dotenv()

print("🔑 Fetching cloud credentials from AWS Secrets Manager...")
try:
    # Retrieve secrets dynamically from AWS Secrets Manager
    secrets = get_secret(secret_name="hawwa/datalake/credentials", region_name="us-east-1")
    
    AWS_ACCESS_KEY_ID = secrets.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = secrets.get("AWS_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME = secrets.get("S3_BUCKET_NAME", "hawwa-merchant-analytics-datalake")
    AWS_REGION = secrets.get("AWS_REGION", "us-east-1")
    
    # Initialize S3 client with dynamic credentials
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    print("✅ Secrets loaded successfully!")
except Exception as e:
    print(f"⚠️ Could not load AWS Secrets Manager credentials: {e}")
    print("Falling back to local environment variables / default AWS profile...")
    
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "hawwa-merchant-analytics-datalake")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    s3_client = boto3.client("s3", region_name=AWS_REGION)

# Local DB Connection
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "hawwa_analytics_platform")

encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

tables = ["dw_fact_orders", "dw_dim_merchant", "dw_dim_customer", "dw_dim_store"]

print("\n🚀 Extracting datasets and uploading directly to AWS S3 Data Lake...")

for table in tables:
    df = pd.read_sql_table(table, con=engine)
    
    # Convert DataFrame to CSV in memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    s3_key = f"raw_data/{table}.csv"
    
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_key,
        Body=csv_buffer.getvalue()
    )
    print(f"✅ Successfully uploaded {table} -> s3://{S3_BUCKET_NAME}/{s3_key}")

print("\n🎉 Data Lake ingestion complete!")
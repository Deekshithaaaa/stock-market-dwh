from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timezone
import subprocess
import sys

def ingest_bronze():
    subprocess.run([sys.executable, "/Users/deekshithaurs/stock-market-dwh/ingest_bronze.py"], check=True)

def transform_silver():
    subprocess.run([sys.executable, "/Users/deekshithaurs/stock-market-dwh/transform_silver.py"], check=True)

def transform_gold():
    subprocess.run([sys.executable, "/Users/deekshithaurs/stock-market-dwh/transform_gold.py"], check=True)

with DAG(
    dag_id="stock_market_pipeline",
    start_date=datetime(2026, 6, 9, tzinfo=timezone.utc),
    schedule="@daily",
    catchup=False,
    tags=["stock", "dwh"],
) as dag:

    task_bronze = PythonOperator(
        task_id="ingest_bronze",
        python_callable=ingest_bronze,
    )

    task_silver = PythonOperator(
        task_id="transform_silver",
        python_callable=transform_silver,
    )

    task_gold = PythonOperator(
        task_id="transform_gold",
        python_callable=transform_gold,
    )

    task_bronze >> task_silver >> task_gold
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import os
import sys

# Add the scripts folder to Python path inside the container
sys.path.append('/opt/airflow/scripts')

from fetch_and_store import run_fetcher

# -------------------------------
# Default Airflow DAG Arguments
# -------------------------------
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

# -------------------------------
# DAG Definition
# -------------------------------
with DAG(
    dag_id="stock_data_pipeline",
    default_args=default_args,
    description="Fetch, parse, and store stock market data from Alpha Vantage",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
) as dag:

    # --------------------
    # TASK 1: Pipeline Start
    # --------------------
    pipeline_start = EmptyOperator(
        task_id="pipeline_start"
    )

    # --------------------
    # TASK 2: Fetch Stock Data
    # --------------------
    def fetch_task():
        return run_fetcher()

    fetch_stock_data = PythonOperator(
        task_id="fetch_stock_data",
        python_callable=fetch_task
    )

    # --------------------
    # TASK 3: Validate Data (Basic Check)
    # --------------------
    def validate_task():
        print("[INFO] Validation complete (Dummy validation).")
        return True

    validate_data = PythonOperator(
        task_id="validate_data",
        python_callable=validate_task
    )

    # --------------------
    # TASK 4: Log Completion
    # --------------------
    def log_task():
        print("[INFO] Pipeline execution completed successfully.")
        return True

    log_completion = PythonOperator(
        task_id="log_completion",
        python_callable=log_task
    )

    # --------------------
    # TASK 5: Pipeline End
    # --------------------
    pipeline_end = EmptyOperator(
        task_id="pipeline_end"
    )

    # --------------------
    # DAG TASK FLOW
    # --------------------
    pipeline_start >> fetch_stock_data >> validate_data >> log_completion >> pipeline_end

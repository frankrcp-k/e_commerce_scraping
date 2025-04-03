from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import os

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 4, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "ecommerce_price_comparison",
    default_args=default_args,
    description="Scrapes e-commerce data and uploads results to Google Drive",
    schedule_interval="0 5 * * *",
    catchup=False,
)

def run_scraper(**kwargs):
    output_dir = "output"
    filename = f"output_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    subprocess.run(["python3", "scraper/scraper.py", filepath], check=True)
    
    # Push the filename to XCom
    kwargs['ti'].xcom_push(key='output_filename', value=filepath)

def run_uploader(**kwargs):
    ti = kwargs['ti']
    filepath = ti.xcom_pull(task_ids='run_etl', key='output_filename')

    if not filepath:
        raise ValueError("No output file path received from run_scraper")

    subprocess.run(["python3", "scraper/uploader.py", filepath], check=True)

etl_task = PythonOperator(
    task_id="run_etl",
    python_callable=run_scraper,
    provide_context=True,  
    dag=dag,
)

upload_task = PythonOperator(
    task_id="run_upload",
    python_callable=run_uploader,
    provide_context=True,
    dag=dag,
)


etl_task >> upload_task

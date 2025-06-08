from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import os
from include.custom_utils.minio_utils import ensure_bucket_exists

# Get MinIO credentials from environment variables
MINIO_SPARK_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SPARK_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 5, 31),
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'stephen_curry_stats_medallion_etl',
    default_args=default_args,
    description='Medallion architecture ETL pipeline for Stephen Curry statistics',
    schedule_interval='@daily',
    catchup=False
)

# Ensure MinIO bucket exists
ensure_bucket = PythonOperator(
    task_id='ensure_bucket_exists',
    python_callable=ensure_bucket_exists,
    op_kwargs={'bucket_name': 'mybucket'},
    dag=dag
)

# Bronze ingestion task
bronze_ingestion = SparkSubmitOperator(
    task_id='bronze_ingestion',
    application='dags/bronze_ingestion_sc_stats_etl.py',
    conn_id='spark_default',
    packages="org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262,io.delta:delta-spark_2.12:3.1.0",
    conf={
        "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
        "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        "spark.hadoop.fs.s3a.endpoint": "http://minio:9000",
        "spark.hadoop.fs.s3a.access.key": MINIO_SPARK_ACCESS_KEY,
        "spark.hadoop.fs.s3a.secret.key": MINIO_SPARK_SECRET_KEY,
        "spark.hadoop.fs.s3a.path.style.access": "true",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3a.aws.credentials.provider": "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
    },
    application_args=['--output_path', 's3a://mybucket/sc_stats_db/bronze/raw_data'],
    dag=dag
)

# Bronze to Silver transformation task
bronze_to_silver = SparkSubmitOperator(
    task_id='bronze_to_silver',
    application='dags/bronze_to_silver_sc_stats_etl.py',
    conn_id='spark_default',
    packages="org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262,io.delta:delta-spark_2.12:3.1.0",
    conf={
        "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
        "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        "spark.hadoop.fs.s3a.endpoint": "http://minio:9000",
        "spark.hadoop.fs.s3a.access.key": MINIO_SPARK_ACCESS_KEY,
        "spark.hadoop.fs.s3a.secret.key": MINIO_SPARK_SECRET_KEY,
        "spark.hadoop.fs.s3a.path.style.access": "true",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3a.aws.credentials.provider": "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
    },
    application_args=['--output_path', 's3a://mybucket/sc_stats_db/silver/transformed_data'],
    dag=dag
)

# Silver to Gold transformation task
silver_to_gold = SparkSubmitOperator(
    task_id='silver_to_gold',
    application='dags/silver_to_gold_sc_summary_etl.py',
    conn_id='spark_default',
    packages="org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262,io.delta:delta-spark_2.12:3.1.0",
    conf={
        "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
        "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        "spark.hadoop.fs.s3a.endpoint": "http://minio:9000",
        "spark.hadoop.fs.s3a.access.key": MINIO_SPARK_ACCESS_KEY,
        "spark.hadoop.fs.s3a.secret.key": MINIO_SPARK_SECRET_KEY,
        "spark.hadoop.fs.s3a.path.style.access": "true",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3a.aws.credentials.provider": "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
    },
    application_args=['--output_path', 's3a://mybucket/sc_stats_db/gold/summary_data'],
    dag=dag
)

# Set task dependencies
ensure_bucket >> bronze_ingestion >> bronze_to_silver >> silver_to_gold
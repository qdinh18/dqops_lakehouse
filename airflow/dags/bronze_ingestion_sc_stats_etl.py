from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType, BinaryType
import argparse

def main(output_path_arg):
    # Create Spark session with MinIO S3A configs
    spark = (SparkSession.builder
        .appName("BronzeIngestion")
        .config("hive.metastore.uris", "thrift://hive-metastore:9083")
        .enableHiveSupport()
        .getOrCreate())

    print("Bronze Ingestion: Spark session created.")

    # Define schema explicitly
    schema = StructType([
        StructField("transaction_id",         LongType(),     False),
        StructField("transaction_timestamp",  StringType(),False),
        StructField("quantity",               LongType(),  False),
        StructField("unit_price",             DoubleType(),   False),
        StructField("total_amount",           DoubleType(),   False),
        StructField("payment_method",         StringType(),   True),

        StructField("customer_id",            LongType(),     False),
        StructField("customer_name",          StringType(),   True),
        StructField("customer_gender",        StringType(),   True),
        StructField("customer_dob",           StringType(),     True),
        StructField("customer_email",         StringType(),   True),
        StructField("customer_phone",         LongType(),   True),
        StructField("customer_city",          StringType(),   True),
        StructField("customer_state",         StringType(),   True),

        StructField("store_id",               LongType(),  False),
        StructField("store_name",             StringType(),   True),
        StructField("store_city",             StringType(),   True),
        StructField("store_state",            StringType(),   True),

        StructField("product_id",             LongType(),  False),
        StructField("product_name",           StringType(),   True),
        StructField("product_category",       StringType(),   True),
        StructField("product_subcategory",    StringType(),   True)
    ])

    # Load data
    local_parquet_path = "/opt/airflow/data/raw_data.parquet"

    try:
        df = spark.read.schema(schema).parquet(local_parquet_path)
        print(f"Successfully loaded customers data from: {local_parquet_path}")
    except Exception as e:
        print(f"Error loading parquet file: {e}")
        spark.stop()
        raise

    try:
        # Create database if it doesn't exist
        spark.sql("CREATE DATABASE IF NOT EXISTS retail_sales_db")

        # Write data to Minio and register in Hive Metastore
        spark.sql("DROP TABLE IF EXISTS retail_sales_db.raw_data")
        
        (df.write.format("delta")
            .mode("overwrite")
            .option("path", output_path_arg)
            .saveAsTable("retail_sales_db.raw_data"))
            
        print(f"Successfully wrote and registered table retail_sales_db.raw_data at {output_path_arg}")

    except Exception as e:
        print(f"Error writing data to Minio/Hive: {e}")
        spark.stop()
        raise

    print("Bronze ingestion job completed successfully.")
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("--output_path", required=True, help="...")
    args = parser.parse_args()

    main(args.output_path)

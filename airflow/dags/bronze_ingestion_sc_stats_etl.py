from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, LongType
import argparse

def main(output_path_arg):
    # Create Spark session with MinIO S3A configs
    spark = (SparkSession.builder
        .appName("BronzeIngestionStephenCurryStats")
        .config("hive.metastore.uris", "thrift://hive-metastore:9083")
        .enableHiveSupport()
        .getOrCreate())

    print("Bronze Ingestion: Spark session created.")

    # Define schema explicitly
    schema = StructType([
        StructField("Season_year", StringType(), True),
        StructField("Season_div", StringType(), True),
        StructField("Date", StringType(), True),
        StructField("OPP", StringType(), True),
        StructField("Result", StringType(), True),
        StructField("T_Score", LongType(), True),
        StructField("O_Score", LongType(), True),
        StructField("MIN", DoubleType(), True),
        StructField("FG", StringType(), True),
        StructField("FGM", LongType(), True),
        StructField("FGA", LongType(), True),
        StructField("FG_Percentage", DoubleType(), True),
        StructField("3PT", StringType(), True),
        StructField("3PTM", LongType(), True),
        StructField("3PTA", LongType(), True),
        StructField("3P_Percentage", DoubleType(), True),
        StructField("FT", StringType(), True),
        StructField("FTM", LongType(), True),
        StructField("FTA", LongType(), True),
        StructField("FT_Percentage", DoubleType(), True),
        StructField("REB", LongType(), True),
        StructField("AST", LongType(), True),
        StructField("BLK", LongType(), True),
        StructField("STL", LongType(), True),
        StructField("PF", LongType(), True),
        StructField("TO", LongType(), True),
        StructField("PTS", LongType(), True),
    ])

    # Load data
    local_parquet_path = "/opt/airflow/data/Stephen Curry Stats.parquet"

    try:
        df = spark.read.schema(schema).parquet(local_parquet_path)
        print(f"Successfully loaded Stephen Curry stats from: {local_parquet_path}")
    except Exception as e:
        print(f"Error loading parquet file: {e}")
        spark.stop()
        raise

    try:
        # Create database if it doesn't exist
        spark.sql("CREATE DATABASE IF NOT EXISTS sc_stats_db")

        # Write data to Minio and register in Hive Metastore
        (df.write.format("delta")
            .mode("overwrite")
            .option("path", output_path_arg)
            .saveAsTable("sc_stats_db.bronze_raw_data"))
            
        print(f"Successfully wrote and registered table sc_stats_db.bronze_raw_data at {output_path_arg}")

    except Exception as e:
        print(f"Error writing data to Minio/Hive: {e}")
        spark.stop()
        raise

    print("Bronze ingestion job completed successfully.")
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PySpark Bronze Ingestion Job for Stephen Curry Stats")
    parser.add_argument("--output_path", required=True, help="S3A output path for Bronze data (e.g., s3a://bucket/bronze/sc_stats/)")
    args = parser.parse_args()

    main(args.output_path)

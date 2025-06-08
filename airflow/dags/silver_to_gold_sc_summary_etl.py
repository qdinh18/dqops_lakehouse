from pyspark.sql import SparkSession
from pyspark.sql.functions import current_date
import argparse

def main(output_path_arg):
    # Create Spark session
    spark = (SparkSession.builder
        .appName("SilverToGoldStephenCurryStats")
        .config("hive.metastore.uris", "thrift://hive-metastore:9083")
        .enableHiveSupport()
        .getOrCreate())

    print("Silver to Gold: Spark session created.")

    try:
        # Read from silver table using the catalog
        silver_df = spark.table("sc_stats_db.silver_transformed_data")
        print("Successfully read from table sc_stats_db.silver_transformed_data")

        # Add processing date column
        gold_df = silver_df.withColumn("processing_date", current_date())

        # Write to gold table using the catalog
        print("Writing data to Gold layer")
        (gold_df.write.format("delta")
            .mode("overwrite")
            .option("path", output_path_arg)
            .saveAsTable("sc_stats_db.gold_summary_data"))

        print(f"Successfully wrote and registered table sc_stats_db.gold_summary_data at {output_path_arg}")

    except Exception as e:
        print(f"Error in silver to gold transformation: {e}")
        spark.stop()
        raise

    print("Silver to Gold transformation completed successfully.")
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PySpark Silver to Gold ETL Job")
    parser.add_argument("--output_path", required=True, help="S3A output path for Gold data")
    args = parser.parse_args()
    main(args.output_path) 
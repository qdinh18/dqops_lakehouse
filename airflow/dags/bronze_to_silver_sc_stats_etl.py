from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, when, regexp_replace
import argparse

def main(output_path_arg):
    # Create Spark session
    spark = (SparkSession.builder
        .appName("BronzeToSilverStephenCurryStats")
        .config("hive.metastore.uris", "thrift://hive-metastore:9083")
        .enableHiveSupport()
        .getOrCreate())

    print("Bronze to Silver: Spark session created.")

    try:
        # Read from bronze table using the catalog
        bronze_df = spark.table("sc_stats_db.bronze_raw_data")
        print("Successfully read from table sc_stats_db.bronze_raw_data")

        # Apply transformations
        silver_df = (bronze_df
            # Convert Date to proper date format
            .withColumn("Date", to_date(col("Date"), "MM/dd/yyyy"))
            # Clean up Result column (W/L only)
            .withColumn("Result", regexp_replace(col("Result"), "[^WL]", ""))
            # Convert percentage columns to proper decimals
            .withColumn("FG_Percentage", col("FG_Percentage") / 100)
            .withColumn("3P_Percentage", col("3P_Percentage") / 100)
            .withColumn("FT_Percentage", col("FT_Percentage") / 100)
            # Add game outcome columns
            .withColumn("Point_Difference", col("T_Score") - col("O_Score"))
        )

        # Write to silver table using the catalog
        print("Writing data to Silver layer")
        (silver_df.write.format("delta")
            .mode("overwrite")
            .option("path", output_path_arg)
            .saveAsTable("sc_stats_db.silver_transformed_data"))
        
        print(f"Successfully wrote and registered table sc_stats_db.silver_transformed_data at {output_path_arg}")

    except Exception as e:
        print(f"Error in bronze to silver transformation: {e}")
        spark.stop()
        raise

    print("Bronze to Silver transformation completed successfully.")
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PySpark Bronze to Silver ETL Job")
    parser.add_argument("--output_path", required=True, help="S3A output path for Silver data")
    args = parser.parse_args()
    main(args.output_path) 
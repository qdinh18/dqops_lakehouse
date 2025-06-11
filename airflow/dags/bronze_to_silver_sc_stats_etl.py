from pyspark.sql import SparkSession
from pyspark.sql import functions as f
from pyspark.sql.types import TimestampType, DateType, StringType, IntegerType
import argparse

def main(dim_customer_path, dim_store_path, dim_product_path, fact_sales_path):
    # Create Spark session
    spark = (SparkSession.builder
        .appName("BronzeToSilver")
        .config("hive.metastore.uris", "thrift://hive-metastore:9083")
        .enableHiveSupport()
        .getOrCreate())

    print("Bronze to Silver: Spark session created.")

    try:
        # Read from bronze table using the catalog
        bronze_df = spark.table("retail_sales_db.raw_data")
        print("Successfully read from table retail_sales_db.raw_data")

        # Apply transformations
        silver_df = (bronze_df
            # Convert Date to proper date format
            .withColumn("transaction_timestamp", f.to_timestamp("transaction_timestamp", "yyyy-MM-dd HH:mm:ss"))
            .withColumn("quantity", f.col('quantity').cast(IntegerType()))
            .withColumn("customer_dob", f.col("customer_dob").cast(DateType()))
            .withColumn("customer_phone", f.concat(f.lit('+'), f.col("customer_phone").cast(StringType())))
        )
        dim_customer = silver_df.select('customer_id', 'customer_name', 'customer_gender',
                                        'customer_dob', 'customer_email', 'customer_phone',
                                        'customer_city', 'customer_state')
        
        dim_store = silver_df.select('store_id', 'store_name', 'store_city', 'store_state')

        dim_product = silver_df.select('product_id', 'product_name', 'product_category', 'product_subcategory')

        fact_sales = silver_df.select('transaction_id', 'transaction_timestamp', 'quantity', 'unit_price',
                                      'total_amount', 'payment_method', 'customer_id', 'store_id', 'product_id')
        # Write to silver table using the catalog
        print("Writing data to Silver layer")

        spark.sql("DROP TABLE IF EXISTS retail_sales_db.dim_customer")
        (dim_customer.write.format("delta")
        .mode("overwrite")
        .option("path", dim_customer_path)
        .saveAsTable("retail_sales_db.dim_customer"))
        
        spark.sql("DROP TABLE IF EXISTS retail_sales_db.dim_store")
        (dim_store.write.format("delta")
        .mode("overwrite")
        .option("path", dim_store_path)
        .saveAsTable("retail_sales_db.dim_store"))

        spark.sql("DROP TABLE IF EXISTS retail_sales_db.dim_product")
        (dim_product.write.format("delta")
        .mode("overwrite")
        .option("path", dim_product_path)
        .saveAsTable("retail_sales_db.dim_product"))

        spark.sql("DROP TABLE IF EXISTS retail_sales_db.fact_sales")
        (fact_sales.write.format("delta")
        .mode("overwrite")
        .option("path", fact_sales_path)
        .saveAsTable("retail_sales_db.fact_sales"))
        
        # print(f"Successfully wrote and registered table retail_sales_db.silver_transformed_data at {output_path_arg}")

    except Exception as e:
        print(f"Error in bronze to silver transformation: {e}")
        spark.stop()
        raise

    print("Bronze to Silver transformation completed successfully.")
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PySpark Bronze to Silver ETL Job")
    parser.add_argument("--dim_customer_output_path", required=True, help="S3A output path for Silver data")
    parser.add_argument("--dim_store_output_path", required=True, help="S3A output path for Silver data")
    parser.add_argument("--dim_product_output_path", required=True, help="S3A output path for Silver data")
    parser.add_argument("--fact_sales_output_path", required=True, help="S3A output path for Silver data")
    args = parser.parse_args()
    main(args.dim_customer_output_path,
        args.dim_store_output_path,
        args.dim_product_output_path,
        args.fact_sales_output_path)
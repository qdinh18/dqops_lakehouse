from pyspark.sql import SparkSession, functions as f
import argparse


def main(output_path):

    spark = (
        SparkSession.builder
        .appName("SilverToGold_Aggregated")
        .config("hive.metastore.uris", "thrift://hive-metastore:9083")
        .enableHiveSupport()
        .getOrCreate()
    )
    print("Silver → Gold: Spark session created.")

    try:

        fact_sales  = spark.table("retail_sales_db.fact_sales").limit(10000)
        dim_customer = spark.table("retail_sales_db.dim_customer").limit(10000)
        dim_store    = spark.table("retail_sales_db.dim_store").limit(10000)
        dim_product  = spark.table("retail_sales_db.dim_product").limit(10000)


        sales_enriched = (
            fact_sales.alias("f")
            .join(f.broadcast(dim_customer.alias("c")), "customer_id", "inner")
            .join(f.broadcast(dim_store.alias("s")), "store_id", "inner")
            .join(f.broadcast(dim_product.alias("p")), "product_id", "inner")
            .withColumn("transaction_date", f.to_date("transaction_timestamp"))
        )

        gold_df = (
            sales_enriched
            .groupBy(
                "transaction_date",
                "s.store_id",  "s.store_name",         
                "p.product_category"                   
            )
            .agg(
                f.sum("total_amount").alias("total_sales"),
                f.sum("quantity").alias("units_sold"),
                f.countDistinct("transaction_id").alias("num_transactions")
            )
            .withColumn("processing_date", f.current_date())
        )

        print("Writing aggregated data to Gold layer …")

        # wrting ..
        (gold_df.write
         .format("delta")
         .mode("overwrite")         
         .option("path", output_path)
         .option('overwriteSchema', 'true')
         .saveAsTable("retail_sales_db.gold_sales_summary"))

        print(f"Done, retail_sales_db.gold_sales_summary saved to {output_path}")

    except Exception as e:
        print(f"Error in Silver to Gold aggregation: {e}")
        raise

    finally:
        spark.stop()
        print("Spark session stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PySpark Silver to Gold ETL Job (join dim & aggregate)")
    parser.add_argument("--output_path", required=True)
    args = parser.parse_args()
    main(args.output_path)

# DQOps Lakehouse

This project implements a modern data lakehouse architecture using Docker for containerization. It demonstrates a full data lifecycle, from ingestion and processing to data quality monitoring and business intelligence.

## Architecture

The architecture is designed to be scalable, modular, and robust, leveraging open-source technologies.

<img width="1020" alt="Screenshot 2025-06-23 at 12 31 46" src="https://github.com/user-attachments/assets/2c8a1c55-0044-4515-b7dd-c48444aacfb8" />


The main components of the architecture are:

*   **Infrastructure (Docker):** The entire platform is containerized using Docker and managed with Docker Compose, ensuring portability and ease of deployment.
*   **Orchestration and Monitoring (Apache Airflow):** Airflow is used to schedule, orchestrate, and monitor the data pipelines. This includes ingestion, ETL jobs, and data quality checks.
*   **Object Storage (MinIO & Delta Lake):** MinIO provides an S3-compatible object storage solution. Delta Lake is used on top of MinIO to bring reliability, performance, and ACID transactions to the data lake. The storage is organized into three layers (Medallion Architecture):
    *   **Bronze:** Raw, unprocessed data ingested from source systems.
    *   **Silver:** Cleaned, validated, and enriched data.
    *   **Gold:** Aggregated data, ready for analytics and business intelligence.
*   **Compute Engine (Apache Spark):** Spark is used for large-scale data processing. It runs in a cluster mode with a master and worker nodes. It processes data from MinIO and executes ETL transformations.
*   **Metadata Management (Hive Metastore):** Hive Metastore stores the schema and metadata of the tables in the data lake, allowing Spark and other tools to have a centralized schema repository.
*   **Data Quality (DQOps):** DQOps is integrated to ensure data quality across the lakehouse. It connects to the Spark Thrift Server to retrieve schemas and run data quality checks using SQL.
*   **Query Engine (Spark Thrift Server):** The Spark Thrift Server provides a JDBC/ODBC interface to the data stored in the lakehouse, allowing BI tools to query the data using standard SQL.
*   **Analytics & BI (Apache Superset):** Superset is a modern data exploration and visualization platform. It connects to the Spark Thrift Server to query the gold layer data and build interactive dashboards.

## Data Flow

1.  **Ingestion:** Data is ingested from various sources into the Bronze layer in MinIO. This process is orchestrated by an Airflow DAG.
2.  **ETL Processing:** Airflow triggers Spark jobs to perform transformations:
    *   **Bronze to Silver:** Raw data is cleaned, deduplicated, and transformed.
    *   **Silver to Gold:** Silver data is aggregated and modeled to create business-level tables.
3.  **Data Quality:** DQOps continuously monitors the data in the lakehouse. It runs predefined checks and rules to detect anomalies, schema changes, and other data quality issues.
4.  **Analytics:** Business users and data analysts can explore the curated data in the Gold layer using Apache Superset, creating reports and dashboards to derive insights.

## Technology Stack

*   **Orchestration:** Apache Airflow
*   **Containerization:** Docker, Docker Compose
*   **Object Storage:** MinIO
*   **Data Lakehouse Format:** Delta Lake
*   **Compute Engine:** Apache Spark
*   **Metadata Store:** Hive Metastore
*   **Data Quality:** DQOps
*   **BI & Analytics:** Apache Superset

## How to Run

To start the platform, you can use the docker-compose files.

1.  **Start the main services (Spark, MinIO, Hive Metastore, etc.):**
    ```bash
    docker-compose up -d
    ```

2.  **Start Airflow services:**
    ```bash
    docker-compose -f docker-compose-airflow.yaml up -d
    ```

Please refer to the `docker-compose.yaml` and `docker-compose-airflow.yaml` for details on the services and their configurations.

## Project Structure

```
├── airflow/            # Airflow DAGs, plugins, and configurations
├── dqops_userhome/     # DQOps user home with checks, rules, and sources
├── hive/               # Hive Metastore configuration and Dockerfile
├── spark/              # Spark configuration and Dockerfile
├── superset/           # Superset configuration and Dockerfile
├── docker-compose.yaml # Main services for the data platform
├── docker-compose-airflow.yaml # Services for Airflow
└── README.md
```

# Apache Iceberg Hands-On Tutorial

A comprehensive guide to working with Apache Iceberg tables using free, open-source tools on macOS. This tutorial covers setting up Iceberg with Spark and MinIO, then demonstrates how to connect to Firebolt.io for production workloads.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [Part 1: Iceberg with Spark and MinIO](#part-1-iceberg-with-spark-and-minio)
- [Part 2: Iceberg with Firebolt](#part-2-iceberg-with-firebolt)
- [Operations Guide](#operations-guide)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)

## Overview

This hands-on tutorial demonstrates:
- Setting up Apache Iceberg tables using Docker, Spark, and MinIO
- Working with NYC Yellow Taxi trip data
- Performing CRUD operations (INSERT, DELETE, SELECT)
- Migrating from Spark to Firebolt.io for production workloads

## Prerequisites

- macOS (tested on macOS 13+)
- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)
- Python 3.8+ installed
- Git installed
- At least 8GB RAM available for Docker containers
- 10GB free disk space for data

## Architecture

```
┌─────────────────┐
│   JupyterLab    │
│   (Port 8888)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐  ┌──▼────┐
│ Spark │  │ MinIO │
│       │  │(S3 API)│
└───┬───┘  └───┬───┘
    │          │
    └────┬─────┘
         │
    ┌────▼────┐
    │  Docker │
    │ Network │
    └─────────┘
```

## Setup Instructions

### Step 1: Clone and Navigate to Project Directory

```bash
# Create project directory
mkdir iceberg-hands-on
cd iceberg-hands-on

# Create necessary directories
mkdir -p data notebooks scripts
```

### Step 2: Create Docker Compose Configuration

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  minio:
    image: minio/minio:latest
    container_name: minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  spark:
    image: apache/spark-py:latest
    container_name: spark
    ports:
      - "8888:8888"
      - "4040:4040"
    environment:
      - SPARK_MODE=master
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
      - AWS_ACCESS_KEY_ID=minioadmin
      - AWS_SECRET_ACCESS_KEY=minioadmin
      - AWS_ENDPOINT=http://minio:9000
    volumes:
      - ./notebooks:/home/spark/notebooks
      - ./data:/home/spark/data
      - ./scripts:/home/spark/scripts
    depends_on:
      minio:
        condition: service_healthy
    command: >
      bash -c "
      pip install jupyterlab pyspark pyiceberg minio boto3 pandas pyarrow &&
      jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''
      "

volumes:
  minio_data:
```

### Step 3: Create Requirements File

Create `requirements.txt`:

```txt
pyspark==3.5.0
pyiceberg==0.7.1
minio==7.2.0
boto3==1.34.0
pandas==2.1.4
pyarrow==14.0.1
jupyterlab==4.0.11
requests==2.31.0
```

### Step 4: Start Docker Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 5: Access Services

- **JupyterLab**: http://localhost:8888
- **MinIO Console**: http://localhost:9001 (login: minioadmin/minioadmin)
- **Spark UI**: http://localhost:4040 (when Spark job is running)

## Part 1: Iceberg with Spark and MinIO

### Step 1: Download NYC Yellow Taxi Data

Create a script `scripts/download_nyc_taxi_data.py`:

```python
import requests
import os
from pathlib import Path

def download_nyc_taxi_data():
    """Download NYC Yellow Taxi trip data for January 2023"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # NYC Taxi data URL (January 2023)
    url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
    output_file = data_dir / "yellow_tripdata_2023-01.parquet"
    
    if output_file.exists():
        print(f"File already exists: {output_file}")
        return str(output_file)
    
    print(f"Downloading NYC Taxi data from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end='', flush=True)
    
    print(f"\nDownload complete: {output_file}")
    print(f"File size: {output_file.stat().st_size / (1024*1024):.2f} MB")
    return str(output_file)

if __name__ == "__main__":
    download_nyc_taxi_data()
```

Run it:

```bash
# From host machine
python scripts/download_nyc_taxi_data.py

# Or from inside Spark container
docker exec -it spark python /home/spark/scripts/download_nyc_taxi_data.py
```

### Step 2: Configure MinIO for S3 Compatibility

Create a notebook `notebooks/01_setup_iceberg_spark.ipynb`:

```python
# Cell 1: Import libraries
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as spark_sum
import os

# Cell 2: Configure Spark with Iceberg and MinIO
spark = SparkSession.builder \
    .appName("IcebergHandsOn") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
    .config("spark.sql.catalog.spark_catalog.type", "hive") \
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.local.type", "hadoop") \
    .config("spark.sql.catalog.local.warehouse", "s3a://iceberg-warehouse/") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.2,org.apache.hadoop:hadoop-aws:3.3.4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print("Spark session created successfully!")

# Cell 3: Create MinIO bucket (using boto3)
import boto3
from botocore.client import Config

s3_client = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    config=Config(signature_version='s3v4')
)

bucket_name = 'iceberg-warehouse'
try:
    s3_client.create_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' created successfully!")
except Exception as e:
    if 'BucketAlreadyOwnedByYou' in str(e) or 'BucketAlreadyExists' in str(e):
        print(f"Bucket '{bucket_name}' already exists.")
    else:
        print(f"Error creating bucket: {e}")

# Cell 4: Read NYC Taxi data
df = spark.read.parquet("/home/spark/data/yellow_tripdata_2023-01.parquet")
print(f"Total records: {df.count()}")
print(f"Schema:")
df.printSchema()
df.show(5)

# Cell 5: Create Iceberg table
spark.sql("""
CREATE TABLE IF NOT EXISTS local.db.nyc_taxi_trips (
    vendor_id INT,
    tpep_pickup_datetime TIMESTAMP,
    tpep_dropoff_datetime TIMESTAMP,
    passenger_count DOUBLE,
    trip_distance DOUBLE,
    rate_code_id DOUBLE,
    store_and_fwd_flag STRING,
    pulocation_id INT,
    dolocation_id INT,
    payment_type INT,
    fare_amount DOUBLE,
    extra DOUBLE,
    mta_tax DOUBLE,
    tip_amount DOUBLE,
    tolls_amount DOUBLE,
    improvement_surcharge DOUBLE,
    total_amount DOUBLE,
    congestion_surcharge DOUBLE,
    airport_fee DOUBLE
) USING ICEBERG
TBLPROPERTIES (
    'write.format.default' = 'parquet',
    'write.parquet.compression-codec' = 'snappy'
)
""")

print("Iceberg table created successfully!")

# Cell 6: Insert initial data
spark.sql("""
INSERT INTO local.db.nyc_taxi_trips
SELECT 
    vendorID as vendor_id,
    tpepPickupDateTime as tpep_pickup_datetime,
    tpepDropoffDateTime as tpep_dropoff_datetime,
    passengerCount as passenger_count,
    tripDistance as trip_distance,
    rateCodeID as rate_code_id,
    storeAndFwdFlag as store_and_fwd_flag,
    PULocationID as pulocation_id,
    DOLocationID as dolocation_id,
    paymentType as payment_type,
    fareAmount as fare_amount,
    extra,
    mtaTax as mta_tax,
    tipAmount as tip_amount,
    tollsAmount as tolls_amount,
    improvementSurcharge as improvement_surcharge,
    totalAmount as total_amount,
    congestionSurcharge as congestion_surcharge,
    airportFee as airport_fee
FROM parquet.`/home/spark/data/yellow_tripdata_2023-01.parquet`
LIMIT 10000
""")

print("Data inserted successfully!")

# Cell 7: Query the table
result = spark.sql("SELECT COUNT(*) as total_trips FROM local.db.nyc_taxi_trips")
result.show()

result = spark.sql("""
    SELECT 
        DATE(tpep_pickup_datetime) as trip_date,
        COUNT(*) as trips,
        SUM(total_amount) as total_revenue
    FROM local.db.nyc_taxi_trips
    GROUP BY DATE(tpep_pickup_datetime)
    ORDER BY trip_date
    LIMIT 10
""")
result.show()
```

### Step 3: Test Operations

Create `notebooks/02_iceberg_operations.ipynb`:

```python
# Cell 1: Setup (same as previous notebook)
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("IcebergOperations") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.local.type", "hadoop") \
    .config("spark.sql.catalog.local.warehouse", "s3a://iceberg-warehouse/") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.2,org.apache.hadoop:hadoop-aws:3.3.4") \
    .getOrCreate()

# Cell 2: SELECT Operations
print("=== SELECT Operations ===")

# Basic select
spark.sql("SELECT COUNT(*) as total FROM local.db.nyc_taxi_trips").show()

# Filtered select
spark.sql("""
    SELECT 
        vendor_id,
        COUNT(*) as trips,
        AVG(total_amount) as avg_fare
    FROM local.db.nyc_taxi_trips
    WHERE total_amount > 50
    GROUP BY vendor_id
""").show()

# Time-based queries
spark.sql("""
    SELECT 
        HOUR(tpep_pickup_datetime) as hour,
        COUNT(*) as trips
    FROM local.db.nyc_taxi_trips
    GROUP BY HOUR(tpep_pickup_datetime)
    ORDER BY hour
""").show()

# Cell 3: INSERT Operations
print("\n=== INSERT Operations ===")

# Insert new records
spark.sql("""
    INSERT INTO local.db.nyc_taxi_trips
    SELECT 
        vendor_id,
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        passenger_count,
        trip_distance,
        rate_code_id,
        store_and_fwd_flag,
        pulocation_id,
        dolocation_id,
        payment_type,
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        improvement_surcharge,
        total_amount,
        congestion_surcharge,
        airport_fee
    FROM local.db.nyc_taxi_trips
    WHERE total_amount > 100
    LIMIT 100
""")

print("Inserted 100 new records")
spark.sql("SELECT COUNT(*) as total_after_insert FROM local.db.nyc_taxi_trips").show()

# Cell 4: DELETE Operations
print("\n=== DELETE Operations ===")

# Count before delete
before_count = spark.sql("SELECT COUNT(*) as cnt FROM local.db.nyc_taxi_trips").collect()[0]['cnt']
print(f"Records before delete: {before_count}")

# Delete records with condition
spark.sql("""
    DELETE FROM local.db.nyc_taxi_trips
    WHERE total_amount < 5
""")

# Count after delete
after_count = spark.sql("SELECT COUNT(*) as cnt FROM local.db.nyc_taxi_trips").collect()[0]['cnt']
print(f"Records after delete: {after_count}")
print(f"Deleted: {before_count - after_count} records")

# Cell 5: UPDATE Operations (using MERGE)
print("\n=== UPDATE Operations (MERGE) ===")

# Create a temporary table with updates
spark.sql("""
    CREATE OR REPLACE TEMPORARY VIEW updates AS
    SELECT 
        vendor_id,
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        passenger_count,
        trip_distance,
        rate_code_id,
        store_and_fwd_flag,
        pulocation_id,
        dolocation_id,
        payment_type,
        fare_amount * 1.1 as fare_amount,  -- 10% increase
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        improvement_surcharge,
        total_amount * 1.1 as total_amount,  -- 10% increase
        congestion_surcharge,
        airport_fee
    FROM local.db.nyc_taxi_trips
    WHERE total_amount BETWEEN 20 AND 30
    LIMIT 50
""")

# Merge updates
spark.sql("""
    MERGE INTO local.db.nyc_taxi_trips AS target
    USING updates AS source
    ON target.vendor_id = source.vendor_id 
       AND target.tpep_pickup_datetime = source.tpep_pickup_datetime
    WHEN MATCHED THEN
        UPDATE SET 
            fare_amount = source.fare_amount,
            total_amount = source.total_amount
""")

print("Merge operation completed")

# Cell 6: Table Metadata and History
print("\n=== Table Metadata ===")

# Show table properties
spark.sql("SHOW TBLPROPERTIES local.db.nyc_taxi_trips").show(50)

# Show table history (snapshots)
spark.sql("SELECT * FROM local.db.nyc_taxi_trips.history").show(truncate=False)

# Show files in the table
spark.sql("SELECT * FROM local.db.nyc_taxi_trips.files").show(5, truncate=False)

# Cell 7: Time Travel Query
print("\n=== Time Travel Query ===")

# Get snapshot ID from history
history = spark.sql("SELECT snapshot_id, timestamp_ms FROM local.db.nyc_taxi_trips.history ORDER BY timestamp_ms DESC LIMIT 5")
history.show()

# Query table at a specific snapshot (example - use actual snapshot_id from above)
# spark.sql("SELECT COUNT(*) FROM local.db.nyc_taxi_trips VERSION AS OF <snapshot_id>").show()
```

## Part 2: Iceberg with Firebolt

### Prerequisites for Firebolt

1. **Firebolt Account**: Sign up at https://www.firebolt.io
2. **Firebolt Engine**: Create an engine in your Firebolt account
3. **Firebolt Credentials**: Obtain your account name, username, and password
4. **S3 Bucket**: Use your own S3 bucket or continue using MinIO (if Firebolt supports custom endpoints)

### Step 1: Install Firebolt Python SDK

```bash
pip install firebolt-sdk
```

### Step 2: Create Firebolt Connection Script

Create `scripts/firebolt_setup.py`:

```python
from firebolt.db import connect
import pandas as pd
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table

# Firebolt connection parameters
FIREBOLT_ACCOUNT = "your-account-name"
FIREBOLT_USERNAME = "your-username"
FIREBOLT_PASSWORD = "your-password"
FIREBOLT_DATABASE = "your-database"
FIREBOLT_ENGINE = "your-engine-name"

def create_firebolt_connection():
    """Create connection to Firebolt"""
    connection = connect(
        account_name=FIREBOLT_ACCOUNT,
        username=FIREBOLT_USERNAME,
        password=FIREBOLT_PASSWORD,
        database=FIREBOLT_DATABASE,
        engine_name=FIREBOLT_ENGINE
    )
    return connection

def setup_iceberg_catalog_firebolt():
    """Setup Iceberg catalog pointing to S3/MinIO"""
    catalog = load_catalog(
        "firebolt_catalog",
        **{
            "type": "rest",
            "uri": "http://localhost:8181",  # Iceberg REST catalog endpoint
            "s3.endpoint": "http://minio:9000",
            "s3.access-key-id": "minioadmin",
            "s3.secret-access-key": "minioadmin",
            "warehouse": "s3://iceberg-warehouse/"
        }
    )
    return catalog
```

### Step 3: Create Firebolt Iceberg Notebook

Create `notebooks/03_iceberg_firebolt.ipynb`:

```python
# Cell 1: Import libraries
from firebolt.db import connect
import pandas as pd
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table
import boto3
from botocore.client import Config

# Cell 2: Configure Firebolt connection
FIREBOLT_ACCOUNT = "your-account-name"  # Replace with your account
FIREBOLT_USERNAME = "your-username"     # Replace with your username
FIREBOLT_PASSWORD = "your-password"     # Replace with your password
FIREBOLT_DATABASE = "your-database"     # Replace with your database
FIREBOLT_ENGINE = "your-engine-name"    # Replace with your engine

# Cell 3: Connect to Firebolt
conn = connect(
    account_name=FIREBOLT_ACCOUNT,
    username=FIREBOLT_USERNAME,
    password=FIREBOLT_PASSWORD,
    database=FIREBOLT_DATABASE,
    engine_name=FIREBOLT_ENGINE
)

print("Connected to Firebolt successfully!")

# Cell 4: Setup S3/MinIO access for Firebolt
# Note: Firebolt needs access to your S3 bucket where Iceberg tables are stored
# Configure S3 credentials in Firebolt account settings or use IAM roles

# Cell 5: Create external table in Firebolt pointing to Iceberg
create_external_table_sql = """
CREATE EXTERNAL TABLE IF NOT EXISTS nyc_taxi_trips_iceberg (
    vendor_id INT,
    tpep_pickup_datetime TIMESTAMP,
    tpep_dropoff_datetime TIMESTAMP,
    passenger_count DOUBLE,
    trip_distance DOUBLE,
    rate_code_id DOUBLE,
    store_and_fwd_flag TEXT,
    pulocation_id INT,
    dolocation_id INT,
    payment_type INT,
    fare_amount DOUBLE,
    extra DOUBLE,
    mta_tax DOUBLE,
    tip_amount DOUBLE,
    tolls_amount DOUBLE,
    improvement_surcharge DOUBLE,
    total_amount DOUBLE,
    congestion_surcharge DOUBLE,
    airport_fee DOUBLE
)
EXTERNAL LOCATION = 's3://your-bucket/iceberg-warehouse/db/nyc_taxi_trips/'
FILE_FORMAT = (TYPE = PARQUET)
"""

# Execute via Firebolt connection
cursor = conn.cursor()
# cursor.execute(create_external_table_sql)  # Uncomment when ready
print("External table created (or would be created)")

# Cell 6: Query Iceberg table via Firebolt
query = """
SELECT 
    COUNT(*) as total_trips,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_fare
FROM nyc_taxi_trips_iceberg
"""

# cursor.execute(query)
# result = cursor.fetchall()
# print(result)

# Cell 7: Advanced queries
analytics_query = """
SELECT 
    DATE_TRUNC('day', tpep_pickup_datetime) as trip_date,
    COUNT(*) as trips,
    SUM(total_amount) as revenue,
    AVG(trip_distance) as avg_distance
FROM nyc_taxi_trips_iceberg
GROUP BY DATE_TRUNC('day', tpep_pickup_datetime)
ORDER BY trip_date
LIMIT 10
"""

# cursor.execute(analytics_query)
# df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
# print(df)

# Cell 8: Using PyIceberg directly with Firebolt S3
# Alternative approach: Use PyIceberg to read data, then load into Firebolt

from pyiceberg.catalog import load_catalog

# Load Iceberg catalog
catalog = load_catalog(
    "local",
    **{
        "type": "filesystem",
        "warehouse": "s3://iceberg-warehouse/",
        "s3.endpoint": "http://minio:9000",
        "s3.access-key-id": "minioadmin",
        "s3.secret-access-key": "minioadmin",
    }
)

# Load table
table = catalog.load_table("db.nyc_taxi_trips")

# Scan and convert to pandas
df = table.scan().to_pandas()
print(f"Loaded {len(df)} rows from Iceberg table")

# Load into Firebolt (if needed)
# df.to_sql('nyc_taxi_trips_firebolt', conn, if_exists='replace', index=False)
```

### Step 4: Firebolt-Specific Operations

Create `notebooks/04_firebolt_operations.ipynb`:

```python
# Cell 1: Setup Firebolt connection
from firebolt.db import connect
import pandas as pd

conn = connect(
    account_name="your-account-name",
    username="your-username",
    password="your-password",
    database="your-database",
    engine_name="your-engine-name"
)

cursor = conn.cursor()

# Cell 2: SELECT Operations
print("=== SELECT Operations ===")

select_query = """
SELECT 
    vendor_id,
    COUNT(*) as trip_count,
    AVG(total_amount) as avg_fare,
    MAX(total_amount) as max_fare
FROM nyc_taxi_trips_iceberg
GROUP BY vendor_id
ORDER BY trip_count DESC
"""

cursor.execute(select_query)
results = cursor.fetchall()
df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
print(df)

# Cell 3: Time-based Analytics
print("\n=== Time-based Analytics ===")

time_query = """
SELECT 
    EXTRACT(HOUR FROM tpep_pickup_datetime) as hour_of_day,
    COUNT(*) as trips,
    AVG(total_amount) as avg_fare,
    AVG(trip_distance) as avg_distance
FROM nyc_taxi_trips_iceberg
GROUP BY EXTRACT(HOUR FROM tpep_pickup_datetime)
ORDER BY hour_of_day
"""

cursor.execute(time_query)
df_time = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
print(df_time)

# Cell 4: Filtered Queries
print("\n=== Filtered Queries ===")

filtered_query = """
SELECT 
    pulocation_id,
    dolocation_id,
    COUNT(*) as route_count,
    AVG(total_amount) as avg_fare
FROM nyc_taxi_trips_iceberg
WHERE total_amount > 50
  AND trip_distance > 5
GROUP BY pulocation_id, dolocation_id
ORDER BY route_count DESC
LIMIT 10
"""

cursor.execute(filtered_query)
df_filtered = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
print(df_filtered)

# Cell 5: Window Functions
print("\n=== Window Functions ===")

window_query = """
SELECT 
    tpep_pickup_datetime,
    total_amount,
    AVG(total_amount) OVER (
        PARTITION BY DATE(tpep_pickup_datetime)
        ORDER BY tpep_pickup_datetime
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7_trips
FROM nyc_taxi_trips_iceberg
WHERE DATE(tpep_pickup_datetime) = '2023-01-15'
ORDER BY tpep_pickup_datetime
LIMIT 20
"""

cursor.execute(window_query)
df_window = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
print(df_window)

# Note: For INSERT/DELETE operations on Iceberg tables via Firebolt,
# you would typically:
# 1. Use PyIceberg or Spark to modify the Iceberg table
# 2. Firebolt will automatically see the changes when querying the external table
# 3. Or use Firebolt's native tables for write operations and sync with Iceberg
```

## Operations Guide

### SELECT Operations

```python
# Basic count
spark.sql("SELECT COUNT(*) FROM local.db.nyc_taxi_trips").show()

# Aggregations
spark.sql("""
    SELECT 
        vendor_id,
        COUNT(*) as trips,
        SUM(total_amount) as revenue
    FROM local.db.nyc_taxi_trips
    GROUP BY vendor_id
""").show()

# Time-based queries
spark.sql("""
    SELECT 
        DATE(tpep_pickup_datetime) as date,
        COUNT(*) as trips
    FROM local.db.nyc_taxi_trips
    GROUP BY DATE(tpep_pickup_datetime)
    ORDER BY date
""").show()
```

### INSERT Operations

```python
# Insert from another table
spark.sql("""
    INSERT INTO local.db.nyc_taxi_trips
    SELECT * FROM source_table
    WHERE condition
""")

# Insert specific columns
spark.sql("""
    INSERT INTO local.db.nyc_taxi_trips (vendor_id, total_amount, ...)
    VALUES (1, 25.50, ...)
""")
```

### DELETE Operations

```python
# Delete with condition
spark.sql("""
    DELETE FROM local.db.nyc_taxi_trips
    WHERE total_amount < 0
""")

# Delete all records (use with caution!)
spark.sql("DELETE FROM local.db.nyc_taxi_trips")
```

### UPDATE Operations (via MERGE)

```python
# Merge/Update
spark.sql("""
    MERGE INTO local.db.nyc_taxi_trips AS target
    USING updates_table AS source
    ON target.id = source.id
    WHEN MATCHED THEN
        UPDATE SET total_amount = source.new_amount
""")
```

## Troubleshooting

### Issue: MinIO connection errors

**Solution**: Check that MinIO is running and accessible:
```bash
docker-compose ps
curl http://localhost:9000/minio/health/live
```

### Issue: Spark can't find Iceberg JARs

**Solution**: Ensure the correct Iceberg version is specified:
```python
.config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.2")
```

### Issue: S3A connection failures

**Solution**: Verify MinIO credentials and endpoint:
```python
.config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
.config("spark.hadoop.fs.s3a.access.key", "minioadmin")
.config("spark.hadoop.fs.s3a.secret.key", "minioadmin")
```

### Issue: Firebolt connection timeout

**Solution**: 
- Verify your Firebolt engine is running
- Check network connectivity
- Verify credentials are correct

### Issue: Large data downloads

**Solution**: Use a smaller sample or download in chunks:
```python
# Download only first N rows
df = spark.read.parquet("path/to/data.parquet").limit(10000)
```

## Resources

- [Apache Iceberg Documentation](https://iceberg.apache.org/)
- [Firebolt Documentation](https://docs.firebolt.io/)
- [NYC Taxi Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- [Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- [MinIO Documentation](https://min.io/docs/)

## Next Steps

1. **Optimize Performance**: Experiment with partitioning and sorting
2. **Schema Evolution**: Try adding/removing columns
3. **Time Travel**: Explore historical snapshots
4. **Compaction**: Learn about optimizing small files
5. **Production Setup**: Deploy to cloud infrastructure

## License

This tutorial is provided as-is for educational purposes.

## Contributing

Feel free to submit issues or pull requests to improve this tutorial!


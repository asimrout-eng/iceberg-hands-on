# This is a Python script version of the notebook
# Copy the code blocks into Jupyter notebook cells

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
df = spark.read.parquet("/home/spark/data/yellow_tripdata_2025-10.parquet")
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
FROM parquet.`/home/spark/data/yellow_tripdata_2025-10.parquet`
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


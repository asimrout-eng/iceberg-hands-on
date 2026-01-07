# This is a Python script version of the notebook
# Copy the code blocks into Jupyter notebook cells

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


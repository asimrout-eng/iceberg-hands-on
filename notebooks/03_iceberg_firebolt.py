# This is a Python script version of the notebook
# Copy the code blocks into Jupyter notebook cells

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


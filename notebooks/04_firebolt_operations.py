# This is a Python script version of the notebook
# Copy the code blocks into Jupyter notebook cells

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


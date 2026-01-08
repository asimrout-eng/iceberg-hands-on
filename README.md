# Apache Iceberg Hands-On Tutorial

A comprehensive guide to working with Apache Iceberg tables using free, open-source tools on macOS. This tutorial covers setting up Iceberg with Spark and MinIO, then demonstrates how to connect to Firebolt.io for production workloads.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Part 1: Iceberg with Spark and MinIO](#part-1-iceberg-with-spark-and-minio)
- [Part 2: Iceberg with Firebolt](#part-2-iceberg-with-firebolt)
- [Operations Guide](#operations-guide)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)

## Overview

This hands-on tutorial demonstrates:
- Setting up Apache Iceberg tables using Docker, Spark, and MinIO
- Working with NYC Yellow Taxi trip data
- Performing CRUD operations (INSERT, DELETE, SELECT, UPDATE)
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

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd iceberg-hands-on

# Run the setup script
./setup.sh
```

The setup script will:
- Create necessary directories
- Download NYC Taxi sample data
- Start Docker services (MinIO and Spark)
- Verify services are running

### Option 2: Manual Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd iceberg-hands-on

# Create necessary directories
mkdir -p data notebooks scripts jars

# Download sample data (default: October & November 2025)
python3 scripts/download_nyc_taxi_data.py

# Or download specific months
python3 scripts/download_nyc_taxi_data.py 2025 10 11

# Start all services (MinIO and Spark with JupyterLab)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access Services

- **JupyterLab**: http://localhost:8888
- **MinIO Console**: http://localhost:9001 (login: minioadmin/minioadmin)
- **Spark UI**: http://localhost:4040 (when Spark job is running)

## How Docker Installation Works

### Quick Overview

When you run `docker-compose up -d`:

1. **MinIO Container**:
   - Docker downloads the `minio/minio:latest` image (if not already present)
   - Creates a container and starts MinIO server
   - MinIO is ready in ~30 seconds
   - **No installation needed** - it's pre-built in the image

2. **Spark Container** (includes JupyterLab):
   - Docker downloads the `apache/spark-py:latest` image (if not already present) - **~1.5GB, takes 5-10 minutes first time**
   - Waits for MinIO to be healthy
   - Runs setup command that:
     - Installs JupyterLab and Python packages via `pip` (2-5 minutes first time)
     - Downloads Iceberg JAR files (1-2 minutes)
     - Starts JupyterLab server
   - JupyterLab is ready when you see it running on port 8888

**Key Point**: Nothing is installed on your Mac! Everything runs in isolated Docker containers.

**First run time**: 8-17 minutes (downloads and installations)  
**Subsequent runs**: ~40 seconds (everything is cached)

### 4. Run Tutorial Notebooks

Open JupyterLab and navigate through the notebooks in order:
1. `01_setup_iceberg_spark.ipynb` - Initial setup and table creation
2. `02_iceberg_operations.ipynb` - CRUD operations
3. `03_iceberg_firebolt.ipynb` - Firebolt integration
4. `04_firebolt_operations.ipynb` - Firebolt-specific operations

## Part 1: Iceberg with Spark and MinIO

### Step 1: Download NYC Yellow Taxi Data

The enhanced data download script supports downloading any year/month combination. The script is flexible and can download multiple months at once.

#### Default Download (October & November 2025)

By default, the script downloads October and November 2025 data:

```bash
# From your host machine
python3 scripts/download_nyc_taxi_data.py
```

Or from inside the Spark container:

```bash
docker exec -it spark python /home/spark/scripts/download_nyc_taxi_data.py
```

#### Download Specific Months

You can specify custom year and months:

```bash
# Download specific months (year month1 month2 ...)
python3 scripts/download_nyc_taxi_data.py 2025 10 11

# Download different year
python3 scripts/download_nyc_taxi_data.py 2023 1 2 3

# Download single month
python3 scripts/download_nyc_taxi_data.py 2024 6
```

#### Data Source

The data is downloaded from the official [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) page. The script downloads Parquet format files which are optimized for analytics.

**Available Data Types:**
- `yellow` - Yellow Taxi trips (default)
- `green` - Green Taxi trips
- `fhv` - For-Hire Vehicle trips
- `fhvhv` - High Volume For-Hire Vehicle trips

**Note:** The script currently downloads Yellow Taxi data by default. To download other types, modify the `data_type` parameter in the script.

#### Download Location

Files are saved to the `data/` directory:
- `data/yellow_tripdata_YYYY-MM.parquet`

**File Sizes:** Each monthly file is typically 60-80 MB, so ensure you have sufficient disk space.

### Step 2: Create Your First Iceberg Table

Open JupyterLab and create a new notebook. See the detailed instructions in `ICEBERG_HANDSON_README.md` for complete code examples.

Key steps:
1. Configure Spark with Iceberg extensions
2. Set up MinIO S3-compatible storage
3. Create Iceberg table schema
4. Load data into the table

### Step 3: Test Operations

Test various operations:
- **SELECT**: Query data with filters, aggregations, and joins
- **INSERT**: Add new records to the table
- **DELETE**: Remove records based on conditions
- **UPDATE**: Modify existing records using MERGE

## Part 2: Iceberg with Firebolt

### Prerequisites for Firebolt

1. **Firebolt Account**: Sign up at https://www.firebolt.io
2. **Firebolt Engine**: Create an engine in your Firebolt account
3. **Firebolt Credentials**: Obtain your account name, username, and password
4. **S3 Bucket**: Configure access to your S3 bucket (or MinIO) from Firebolt

### Step 1: Install Firebolt SDK

```bash
pip install firebolt-sdk
```

### Step 2: Configure Firebolt Connection

Update `scripts/firebolt_setup.py` with your Firebolt credentials:

```python
FIREBOLT_ACCOUNT = "your-account-name"
FIREBOLT_USERNAME = "your-username"
FIREBOLT_PASSWORD = "your-password"
FIREBOLT_DATABASE = "your-database"
FIREBOLT_ENGINE = "your-engine-name"
```

### Step 3: Connect to Firebolt

Use the notebooks in the `notebooks/` directory to:
1. Connect to Firebolt
2. Create external tables pointing to Iceberg data
3. Query Iceberg tables through Firebolt
4. Perform analytics operations

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
```

### INSERT Operations

```python
# Insert from another table
spark.sql("""
    INSERT INTO local.db.nyc_taxi_trips
    SELECT * FROM source_table
    WHERE condition
""")
```

### DELETE Operations

```python
# Delete with condition
spark.sql("""
    DELETE FROM local.db.nyc_taxi_trips
    WHERE total_amount < 0
""")
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

**Solution**: Ensure the correct Iceberg version is specified in your Spark configuration. The docker-compose file includes the necessary packages.

### Issue: S3A connection failures

**Solution**: Verify MinIO credentials and endpoint match your configuration.

### Issue: Firebolt connection timeout

**Solution**: 
- Verify your Firebolt engine is running
- Check network connectivity
- Verify credentials are correct

### Issue: Large data downloads

**Solution**: Use a smaller sample or download in chunks. The tutorial uses a subset of data for faster processing.

## Resources

- [Git Workflow Guide](GIT_WORKFLOW.md) - How to push files to GitHub
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

# Docker Installation Explained - MinIO & JupyterLab

This document explains **exactly** how MinIO and JupyterLab get installed and run using Docker. No prior Docker knowledge required!

## Table of Contents

1. [What is Docker?](#what-is-docker)
2. [What Happens When You Run `docker-compose up`](#what-happens-when-you-run-docker-compose-up)
3. [MinIO Installation Explained](#minio-installation-explained)
4. [JupyterLab Installation Explained](#jupyterlab-installation-explained)
5. [How Containers Communicate](#how-containers-communicate)
6. [Step-by-Step Installation Process](#step-by-step-installation-process)
7. [Visual Walkthrough](#visual-walkthrough)

---

## What is Docker?

Think of Docker like this:
- **Docker Image** = A pre-built software package (like a recipe)
- **Docker Container** = A running instance of that software (like a meal cooked from the recipe)
- **Docker Compose** = A tool that runs multiple containers together

**Key Point**: Docker **doesn't install** software on your Mac. Instead, it runs software in **isolated containers** that share your Mac's resources.

---

## What Happens When You Run `docker-compose up`

When you run `docker-compose up -d`, here's what happens:

### Step 1: Docker Reads `docker-compose.yml`

Docker reads the configuration file and sees two services:
1. **MinIO** - Object storage (S3-compatible)
2. **Spark** - Big data processing (which includes JupyterLab)

### Step 2: Docker Downloads Images (First Time Only)

If you don't have the images locally, Docker downloads them:

```bash
# MinIO Image
docker pull minio/minio:latest
# Downloads ~70MB - This is the MinIO server software

# Spark Image  
docker pull apache/spark-py:latest
# Downloads ~1.5GB - This includes Spark + Python + Jupyter
```

**Note**: These downloads happen automatically. You don't need to run these commands manually.

### Step 3: Docker Creates Containers

Docker creates two containers from these images and configures them according to `docker-compose.yml`.

---

## MinIO Installation Explained

### What is MinIO?

MinIO is an **object storage server** that provides an S3-compatible API. Think of it as a local version of Amazon S3.

### How MinIO Gets "Installed"

MinIO **doesn't get installed** on your Mac. Instead:

1. **Docker downloads the MinIO image** (if not already present)
   - Image contains: MinIO server binary, configuration files
   - Location: Stored in Docker's image cache

2. **Docker creates a container** from that image
   - The container is like a lightweight virtual machine
   - It runs MinIO server inside this isolated environment

3. **MinIO starts automatically** when the container starts
   - Command: `server /data --console-address ":9001"`
   - This tells MinIO to:
     - Store data in `/data` (inside the container)
     - Run web console on port 9001

### MinIO Configuration Breakdown

```yaml
minio:
  image: minio/minio:latest          # Which image to use
  container_name: minio              # Name of the container
  ports:
    - "9000:9000"                    # API port (host:container)
    - "9001:9001"                    # Web console port
  environment:
    MINIO_ROOT_USER: minioadmin      # Admin username
    MINIO_ROOT_PASSWORD: minioadmin  # Admin password
  command: server /data --console-address ":9001"  # How to start MinIO
  volumes:
    - minio_data:/data               # Persistent storage
```

**What each part means:**

- **`image: minio/minio:latest`**: Use the official MinIO image
- **`ports: "9000:9000"`**: Map container port 9000 to your Mac's port 9000
  - This means: `http://localhost:9000` on your Mac = MinIO API inside container
- **`environment`**: Sets environment variables (like username/password)
- **`volumes: minio_data:/data`**: Creates persistent storage
  - Data stored in `/data` inside container
  - Docker manages this volume (survives container restarts)

### MinIO Data Storage

```
Your Mac                    Docker Container
─────────────────          ─────────────────
                            ┌──────────────┐
                            │   MinIO      │
                            │   Server     │
                            │              │
                            │  /data       │ ← MinIO stores files here
                            └──────┬───────┘
                                   │
                            ┌──────▼──────┐
                            │ Docker      │
                            │ Volume      │
                            │ minio_data  │ ← Persistent storage
                            └─────────────┘
```

**Important**: The data is stored in a Docker volume, not directly on your Mac's filesystem. This means:
- Data persists even if you stop/restart the container
- Data is isolated from other containers
- You can see it with: `docker volume ls`

---

## JupyterLab Installation Explained

### What is JupyterLab?

JupyterLab is a web-based interactive development environment. It runs in your browser but executes code in the Spark container.

### How JupyterLab Gets "Installed"

JupyterLab installation happens **inside the Spark container** when it starts:

1. **Docker starts the Spark container** from `apache/spark-py:latest` image
   - This image already has Python and Spark pre-installed
   - But JupyterLab is NOT pre-installed

2. **The container runs a setup command** (defined in `docker-compose.yml`):

```bash
bash -c "
  pip install jupyterlab pyspark pyiceberg minio boto3 pandas pyarrow requests &&
  mkdir -p /opt/spark/jars &&
  cd /opt/spark/jars &&
  wget -q https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.4.2/iceberg-spark-runtime-3.5_2.12-1.4.2.jar &&
  wget -q https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar &&
  wget -q https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar &&
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''
"
```

### Step-by-Step: What This Command Does

#### Step 1: Install Python Packages
```bash
pip install jupyterlab pyspark pyiceberg minio boto3 pandas pyarrow requests
```

**What happens:**
- `pip` (Python package installer) downloads and installs packages
- Packages are installed **inside the container**, not on your Mac
- This takes 2-5 minutes the first time

**Packages installed:**
- `jupyterlab` - The web interface you'll use
- `pyspark` - Python API for Spark
- `pyiceberg` - Python library for Iceberg
- `minio` - Python client for MinIO
- `boto3` - AWS SDK (works with MinIO)
- `pandas` - Data manipulation
- `pyarrow` - Parquet file support
- `requests` - HTTP library

#### Step 2: Create JARs Directory
```bash
mkdir -p /opt/spark/jars
```

Creates directory for Java libraries (JARs) needed by Spark.

#### Step 3: Download Iceberg JARs
```bash
cd /opt/spark/jars
wget -q https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.4.2/iceberg-spark-runtime-3.5_2.12-1.4.2.jar
wget -q https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar
wget -q https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar
```

**What happens:**
- Downloads Java libraries needed for Iceberg and S3 connectivity
- These are stored in `/opt/spark/jars` inside the container
- Spark automatically loads JARs from this directory

#### Step 4: Start JupyterLab
```bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''
```

**What each flag means:**
- `--ip=0.0.0.0` - Listen on all network interfaces (allows access from your Mac)
- `--port=8888` - Run on port 8888
- `--no-browser` - Don't try to open browser (we're in a container)
- `--allow-root` - Allow running as root user (needed in container)
- `--NotebookApp.token=''` - No authentication token (for simplicity)
- `--NotebookApp.password=''` - No password (for simplicity)

**Security Note**: In production, you should use authentication!

### JupyterLab Configuration Breakdown

```yaml
spark:
  image: apache/spark-py:latest      # Base image with Spark + Python
  container_name: spark
  ports:
    - "8888:8888"                    # JupyterLab web interface
    - "4040:4040"                    # Spark UI (for monitoring jobs)
  environment:
    - SPARK_MODE=master               # Run Spark in master mode
    - MINIO_ACCESS_KEY=minioadmin     # MinIO credentials
    - MINIO_SECRET_KEY=minioadmin
  volumes:
    - ./notebooks:/home/spark/notebooks  # Your notebooks folder
    - ./data:/home/spark/data            # Your data folder
    - ./scripts:/home/spark/scripts      # Your scripts folder
  depends_on:
    minio:
      condition: service_healthy      # Wait for MinIO to be ready
  command: >                          # What to run when container starts
    bash -c "pip install ... && jupyter lab ..."
```

**Key Points:**

- **`volumes`**: Maps folders from your Mac to the container
  - `./notebooks:/home/spark/notebooks` means:
    - `./notebooks` on your Mac = `/home/spark/notebooks` in container
    - Changes in either location are synced!

- **`depends_on`**: Spark waits for MinIO to be healthy before starting
  - This ensures MinIO is ready when Spark tries to connect

---

## How Containers Communicate

Containers can talk to each other using **service names** as hostnames:

```
┌─────────────┐         ┌─────────────┐
│   Spark     │────────▶│   MinIO     │
│  Container  │         │  Container  │
│             │         │             │
│ Connects to:│         │ Listens on: │
│ minio:9000  │         │   :9000     │
└─────────────┘         └─────────────┘
```

**Example:**
- From Spark container, you can access MinIO at: `http://minio:9000`
- From your Mac, you access MinIO at: `http://localhost:9000`
- From your Mac, you access JupyterLab at: `http://localhost:8888`

**Why `minio:9000` works:**
- Docker Compose creates a network
- Each service name becomes a hostname
- `minio` resolves to the MinIO container's IP address

---

## Step-by-Step Installation Process

### When You Run `docker-compose up -d`

Here's the exact sequence:

#### Phase 1: MinIO Container

1. **Docker checks**: Do I have `minio/minio:latest` image?
   - **No**: Downloads it (~70MB)
   - **Yes**: Uses existing image

2. **Docker creates container** named `minio`

3. **Docker creates volume** `minio_data` for persistent storage

4. **Docker maps ports**:
   - Container port 9000 → Mac port 9000
   - Container port 9001 → Mac port 9001

5. **Docker sets environment variables**:
   - `MINIO_ROOT_USER=minioadmin`
   - `MINIO_ROOT_PASSWORD=minioadmin`

6. **Docker starts MinIO** with command: `server /data --console-address ":9001"`

7. **MinIO starts** and begins health checks

8. **Health check passes** (after ~10 seconds)

#### Phase 2: Spark Container (Waits for MinIO)

1. **Docker checks**: Do I have `apache/spark-py:latest` image?
   - **No**: Downloads it (~1.5GB) - **This takes 5-10 minutes!**
   - **Yes**: Uses existing image

2. **Docker waits** for MinIO health check to pass

3. **Docker creates container** named `spark`

4. **Docker maps ports**:
   - Container port 8888 → Mac port 8888
   - Container port 4040 → Mac port 4040

5. **Docker mounts volumes**:
   - `./notebooks` → `/home/spark/notebooks`
   - `./data` → `/home/spark/data`
   - `./scripts` → `/home/spark/scripts`

6. **Docker sets environment variables** (MinIO credentials)

7. **Docker runs the setup command**:
   ```bash
   pip install jupyterlab pyspark pyiceberg minio boto3 pandas pyarrow requests
   ```
   - **This takes 2-5 minutes the first time**
   - Packages are cached, so subsequent starts are faster

8. **Downloads Iceberg JARs**:
   - Downloads 3 JAR files (~50MB total)
   - **Takes 1-2 minutes**

9. **Starts JupyterLab**:
   - JupyterLab server starts
   - Listens on port 8888
   - **Ready to use!**

### Total Time (First Run)

- MinIO: ~30 seconds
- Spark image download: 5-10 minutes (one-time)
- Package installation: 2-5 minutes (one-time)
- JAR downloads: 1-2 minutes (one-time)
- **Total: 8-17 minutes first time**

### Subsequent Runs

- MinIO: ~10 seconds
- Spark: ~30 seconds (packages already installed)
- **Total: ~40 seconds**

---

## Visual Walkthrough

### Before `docker-compose up`

```
Your Mac
├── iceberg-hands-on/
│   ├── docker-compose.yml
│   ├── notebooks/
│   ├── data/
│   └── scripts/
└── Docker Desktop (running)
```

### After `docker-compose up` (First Time)

```
Your Mac
├── iceberg-hands-on/
│   ├── docker-compose.yml
│   ├── notebooks/  ← Mapped to container
│   ├── data/       ← Mapped to container
│   └── scripts/     ← Mapped to container
│
└── Docker Desktop
    ├── Images (downloaded)
    │   ├── minio/minio:latest (~70MB)
    │   └── apache/spark-py:latest (~1.5GB)
    │
    ├── Containers (running)
    │   ├── minio
    │   │   ├── MinIO Server running
    │   │   ├── Port 9000 (API)
    │   │   ├── Port 9001 (Console)
    │   │   └── Volume: minio_data
    │   │
    │   └── spark
    │       ├── Python + Spark installed
    │       ├── JupyterLab installed (via pip)
    │       ├── Iceberg JARs downloaded
    │       ├── Port 8888 (JupyterLab)
    │       ├── Port 4040 (Spark UI)
    │       └── Volumes: notebooks, data, scripts
    │
    └── Network
        └── iceberg-hands-on_default
            ├── minio (hostname)
            └── spark (hostname)
```

### What You See in Your Browser

**JupyterLab** (`http://localhost:8888`):
```
┌─────────────────────────────────────┐
│  JupyterLab                         │
│  ┌─────────┐  ┌─────────┐          │
│  │ File    │  │ Running │          │
│  │ Browser │  │ Kernels │          │
│  └─────────┘  └─────────┘          │
│                                     │
│  notebooks/                         │
│  ├── 01_setup_iceberg_spark.py     │
│  ├── 02_iceberg_operations.py       │
│  └── ...                            │
└─────────────────────────────────────┘
```

**MinIO Console** (`http://localhost:9001`):
```
┌─────────────────────────────────────┐
│  MinIO Console                      │
│  Login: minioadmin / minioadmin    │
│                                     │
│  Buckets:                           │
│  └── iceberg-warehouse              │
│                                     │
│  [Create Bucket] [Upload]           │
└─────────────────────────────────────┘
```

---

## Common Questions

### Q: Where is MinIO actually installed?

**A**: MinIO isn't "installed" on your Mac. It runs inside a Docker container. The MinIO binary is inside the `minio/minio:latest` Docker image.

### Q: Where is JupyterLab actually installed?

**A**: JupyterLab is installed **inside the Spark container** when it starts, using `pip install`. It's not on your Mac - it's in the container's Python environment.

### Q: Do I need to install Python/Spark/MinIO on my Mac?

**A**: **No!** Everything runs in Docker containers. You only need:
- Docker Desktop installed
- That's it!

### Q: What happens if I delete the containers?

**A**: 
- **MinIO data**: Preserved (stored in Docker volume `minio_data`)
- **JupyterLab**: Will be reinstalled next time (packages re-downloaded)
- **Your notebooks**: Preserved (stored in `./notebooks` on your Mac)

### Q: How do I update JupyterLab or packages?

**A**: Stop containers, modify `docker-compose.yml` to add new packages, then restart:
```bash
docker-compose down
docker-compose up -d
```

### Q: Can I access these from another computer?

**A**: Yes, if you're on the same network:
- Use your Mac's IP address instead of `localhost`
- Example: `http://192.168.1.100:8888`

---

## Troubleshooting Installation

### Problem: "Image not found"

**Solution**: Docker will automatically download it. Wait for the download to complete.

### Problem: "Port already in use"

**Solution**: Another application is using port 8888 or 9000. Either:
- Stop the other application
- Change ports in `docker-compose.yml`

### Problem: "pip install takes forever"

**Solution**: This is normal the first time (2-5 minutes). Subsequent starts are faster because packages are cached.

### Problem: "Container keeps restarting"

**Solution**: Check logs:
```bash
docker-compose logs spark
docker-compose logs minio
```

---

## Summary

1. **MinIO**: Pre-built Docker image. Just runs when container starts.
2. **JupyterLab**: Installed via `pip` inside Spark container on first start.
3. **Everything is isolated**: Runs in containers, not on your Mac.
4. **Data persists**: Using Docker volumes and folder mappings.
5. **First run is slow**: Downloads and installations take time.
6. **Subsequent runs are fast**: Everything is cached.

The beauty of Docker: **You don't install anything on your Mac** - it all runs in isolated containers!


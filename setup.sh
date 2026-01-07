#!/bin/bash

# Apache Iceberg Hands-On Setup Script
# This script sets up the environment for the Iceberg tutorial

set -e

echo "🚀 Setting up Apache Iceberg Hands-On Tutorial"
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data notebooks scripts jars

# Check if data file exists
if [ ! -f "data/yellow_tripdata_2023-01.parquet" ]; then
    echo "📥 Downloading NYC Taxi data..."
    python3 scripts/download_nyc_taxi_data.py || {
        echo "⚠️  Warning: Could not download data. You can download it manually later."
    }
else
    echo "✅ NYC Taxi data already exists"
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check MinIO health
echo "🔍 Checking MinIO..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        echo "✅ MinIO is ready"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠️  Warning: MinIO may not be ready yet. Check with: docker-compose logs minio"
fi

# Check JupyterLab
echo "🔍 Checking JupyterLab..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8888 > /dev/null 2>&1; then
        echo "✅ JupyterLab is ready"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠️  Warning: JupyterLab may not be ready yet. Check with: docker-compose logs spark"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Open JupyterLab: http://localhost:8888"
echo "   2. Open MinIO Console: http://localhost:9001 (login: minioadmin/minioadmin)"
echo "   3. Follow the tutorial in the README.md file"
echo ""
echo "📚 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart services: docker-compose restart"
echo ""


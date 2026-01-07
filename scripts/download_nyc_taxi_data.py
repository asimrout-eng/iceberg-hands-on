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


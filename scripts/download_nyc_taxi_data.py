import requests
import os
from pathlib import Path

def download_nyc_taxi_data(year=2023, month=1, data_type="yellow"):
    """
    Download NYC Yellow Taxi trip data
    
    Args:
        year: Year (e.g., 2023, 2025)
        month: Month (1-12)
        data_type: Type of data - "yellow", "green", "fhv", or "fhvhv"
    
    Returns:
        Path to downloaded file
    """
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Format month with leading zero
    month_str = f"{month:02d}"
    
    # Build filename
    filename = f"{data_type}_tripdata_{year}-{month_str}.parquet"
    output_file = data_dir / filename
    
    # Build URL (URL-encoded underscores)
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{data_type}_tripdata_{year}-{month_str}.parquet"
    
    if output_file.exists():
        print(f"File already exists: {output_file}")
        return str(output_file)
    
    print(f"Downloading NYC {data_type.title()} Taxi data from {url}...")
    try:
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
    except requests.exceptions.HTTPError as e:
        print(f"\nError downloading: {e}")
        print(f"URL: {url}")
        if e.response.status_code == 404:
            print("File not found. The data may not be available yet.")
        return None
    except Exception as e:
        print(f"\nError: {e}")
        return None

def download_multiple_months(year, months, data_type="yellow"):
    """
    Download multiple months of data
    
    Args:
        year: Year (e.g., 2025)
        months: List of months (e.g., [10, 11])
        data_type: Type of data - "yellow", "green", "fhv", or "fhvhv"
    """
    print(f"Downloading {data_type.title()} Taxi data for {year}, months: {months}")
    print("=" * 60)
    
    for month in months:
        print(f"\n--- Downloading {year}-{month:02d} ---")
        download_nyc_taxi_data(year=year, month=month, data_type=data_type)
        print()

if __name__ == "__main__":
    import sys
    
    # Default: Download October and November 2025
    if len(sys.argv) == 1:
        print("Downloading October and November 2025 Yellow Taxi data...")
        download_multiple_months(year=2025, months=[10, 11], data_type="yellow")
    else:
        # Allow custom usage: python download_nyc_taxi_data.py <year> <month1> <month2> ...
        # Example: python download_nyc_taxi_data.py 2025 10 11
        year = int(sys.argv[1])
        months = [int(m) for m in sys.argv[2:]]
        download_multiple_months(year=year, months=months)

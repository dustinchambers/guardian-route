#!/usr/bin/env python3
"""
Download Denver Crime Data from Open Data Catalog

Downloads crime CSV from Denver Open Data and caches it locally.
Checks if file exists and is recent (< 7 days) before re-downloading.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests
from tqdm import tqdm

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CRIME_CSV_PATH = DATA_RAW_DIR / "crime_raw.csv"

# Data source
DENVER_CRIME_URL = "https://www.denvergov.org/media/gis/DataCatalog/crime/csv/crime.csv"
CACHE_DAYS = 7


def should_download():
    """Check if we need to download data."""
    if not CRIME_CSV_PATH.exists():
        print("Crime data file not found. Will download.")
        return True

    # Check file age
    file_modified = datetime.fromtimestamp(CRIME_CSV_PATH.stat().st_mtime)
    age_days = (datetime.now() - file_modified).days

    if age_days >= CACHE_DAYS:
        print(f"Crime data file is {age_days} days old (threshold: {CACHE_DAYS} days). Will re-download.")
        return True

    print(f"Crime data file is {age_days} days old. Using cached version.")
    return False


def download_crime_data():
    """Download crime data with progress bar."""
    print(f"\nDownloading Denver crime data from:")
    print(f"{DENVER_CRIME_URL}\n")

    try:
        # Stream download with progress bar
        response = requests.get(DENVER_CRIME_URL, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(CRIME_CSV_PATH, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"\nDownload complete: {CRIME_CSV_PATH}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\nError downloading data: {e}")
        return False


def get_data_stats():
    """Display statistics about downloaded data."""
    if not CRIME_CSV_PATH.exists():
        return

    import pandas as pd

    print("\n" + "="*60)
    print("DATA STATISTICS")
    print("="*60)

    try:
        # Read header and sample
        df = pd.read_csv(CRIME_CSV_PATH, nrows=5)
        print(f"\nFile size: {CRIME_CSV_PATH.stat().st_size / (1024*1024):.1f} MB")

        # Count total rows (efficient)
        total_rows = sum(1 for _ in open(CRIME_CSV_PATH)) - 1  # Subtract header
        print(f"Total records: {total_rows:,}")

        print(f"\nAvailable columns ({len(df.columns)}):")
        for col in df.columns:
            print(f"  - {col}")

        # Load full data for more stats
        print("\nLoading full dataset for statistics...")
        df_full = pd.read_csv(CRIME_CSV_PATH)

        # Date range
        if 'FIRST_OCCURRENCE_DATE' in df_full.columns:
            df_full['FIRST_OCCURRENCE_DATE'] = pd.to_datetime(df_full['FIRST_OCCURRENCE_DATE'], errors='coerce')
            min_date = df_full['FIRST_OCCURRENCE_DATE'].min()
            max_date = df_full['FIRST_OCCURRENCE_DATE'].max()
            print(f"\nDate range: {min_date.date()} to {max_date.date()}")

        # Offense categories
        if 'OFFENSE_CATEGORY_ID' in df_full.columns:
            print(f"\nTop 10 offense categories:")
            top_offenses = df_full['OFFENSE_CATEGORY_ID'].value_counts().head(10)
            for offense, count in top_offenses.items():
                print(f"  {offense}: {count:,}")

        # Valid coordinates
        if 'GEO_LON' in df_full.columns and 'GEO_LAT' in df_full.columns:
            valid_coords = ((df_full['GEO_LON'] != 0) & (df_full['GEO_LAT'] != 0)).sum()
            print(f"\nRecords with valid coordinates: {valid_coords:,} ({valid_coords/len(df_full)*100:.1f}%)")

    except Exception as e:
        print(f"\nError reading data: {e}")


def main():
    """Main execution."""
    print("="*60)
    print("DENVER CRIME DATA DOWNLOADER")
    print("="*60)

    # Ensure data directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Check if download needed
    if should_download():
        if not download_crime_data():
            sys.exit(1)

    # Display statistics
    get_data_stats()

    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"\nData location: {CRIME_CSV_PATH}")
    print("\nNext step: Run scripts/02_create_spatial_grid.py")


if __name__ == "__main__":
    main()

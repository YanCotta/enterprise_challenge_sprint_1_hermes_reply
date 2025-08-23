#!/usr/bin/env python3
"""Export sensor_readings to a CSV for ML workflows."""

import argparse
import os
import csv
from datetime import timezone
import psycopg2
import pandas as pd


def get_db_url() -> str:
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://smart_user:strong_password@localhost:5432/smart_maintenance_db",
    )
    return db_url.replace("postgresql+asyncpg", "postgresql")


def get_last_exported_timestamp(csv_path: str) -> str:
    """
    Get the most recent timestamp from the existing CSV file.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Most recent timestamp as string, or None if file doesn't exist or is empty
    """
    if not os.path.exists(csv_path):
        return None
    
    try:
        # Read the CSV file and find the maximum timestamp
        df = pd.read_csv(csv_path)
        if df.empty or 'timestamp' not in df.columns:
            return None
        
        # Get the maximum timestamp and return it as string
        max_timestamp = df['timestamp'].max()
        return max_timestamp
    except Exception as e:
        print(f"Warning: Could not read existing CSV file: {e}")
        return None


def export_sensor_data(out_path: str, incremental: bool = False):
    """
    Export sensor data to CSV file.
    
    Args:
        out_path: Output path for the CSV file
        incremental: If True, append new data since last export
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    conn = psycopg2.connect(get_db_url())
    cur = conn.cursor()
    
    # Determine if this is truly incremental
    last_timestamp = None
    file_exists = os.path.exists(out_path)
    write_header = True
    
    if incremental:
        last_timestamp = get_last_exported_timestamp(out_path)
        if last_timestamp is not None and file_exists:
            # We have existing data, so append mode
            write_header = False
            print(f"Incremental export: Adding data newer than {last_timestamp}")
        else:
            # No existing data or can't read it, perform full export
            print("No existing data found. Performing full export.")
            incremental = False
    
    # Build the SQL query
    base_query = """
        SELECT sensor_id, sensor_type, value, unit, timestamp, quality
        FROM sensor_readings
    """
    
    if incremental and last_timestamp:
        # Filter for records newer than the last exported timestamp
        query = base_query + """
            WHERE timestamp > %s
            ORDER BY sensor_id, timestamp
        """
        cur.execute(query, (last_timestamp,))
    else:
        # Full export
        query = base_query + """
            ORDER BY sensor_id, timestamp
        """
        cur.execute(query)
    
    # Determine file mode
    file_mode = "a" if (incremental and not write_header) else "w"
    
    with open(out_path, file_mode, newline="") as f:
        writer = csv.writer(f)
        
        # Write header only for new files or full exports
        if write_header:
            writer.writerow([
                "sensor_id",
                "sensor_type", 
                "value",
                "unit",
                "timestamp",
                "quality",
            ])
        
        # Write data rows
        row_count = 0
        for row in cur:
            # Ensure ISO timestamp
            r = list(row)
            if hasattr(r[4], "isoformat"):
                r[4] = r[4].astimezone(timezone.utc).isoformat()
            writer.writerow(r)
            row_count += 1
    
    cur.close()
    conn.close()
    
    mode_str = "incremental" if (incremental and last_timestamp) else "full"
    print(f"Exported {row_count} rows ({mode_str} export) to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Export sensor readings to CSV")
    parser.add_argument(
        "--incremental", 
        action="store_true",
        help="Perform incremental export (append new data since last export)"
    )
    parser.add_argument(
        "--output", 
        default="data/sensor_data.csv",
        help="Output CSV file path (default: data/sensor_data.csv)"
    )
    
    args = parser.parse_args()
    
    # Use environment variable if not specified via command line
    out_path = os.getenv("OUT", args.output)
    
    export_sensor_data(out_path, args.incremental)


if __name__ == "__main__":
    main()

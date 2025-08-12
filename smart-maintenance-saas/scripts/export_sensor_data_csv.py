#!/usr/bin/env python3
"""Export sensor_readings to a CSV for ML workflows."""

import os
import csv
from datetime import timezone
import psycopg2


def get_db_url() -> str:
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://smart_user:strong_password@localhost:5432/smart_maintenance_db",
    )
    return db_url.replace("postgresql+asyncpg", "postgresql")


def main():
    out_path = os.getenv("OUT", "data/sensor_data.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    conn = psycopg2.connect(get_db_url())
    cur = conn.cursor()

    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "sensor_id",
                "sensor_type",
                "value",
                "unit",
                "timestamp",
                "quality",
            ]
        )
        cur.execute(
            """
            SELECT sensor_id, sensor_type, value, unit, timestamp, quality
            FROM sensor_readings
            ORDER BY sensor_id, timestamp
            """
        )
        for row in cur:
            # Ensure ISO timestamp
            r = list(row)
            if hasattr(r[4], "isoformat"):
                r[4] = r[4].astimezone(timezone.utc).isoformat()
            writer.writerow(r)

    cur.close()
    conn.close()
    print(f"Exported CSV to {out_path}")


if __name__ == "__main__":
    main()

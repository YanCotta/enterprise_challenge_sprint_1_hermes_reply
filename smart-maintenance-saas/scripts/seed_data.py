#!/usr/bin/env python3
"""Seed sensors and time-series readings into TimescaleDB.

Aligns with finalized ERD: sensors table and sensor_readings with PK (timestamp, sensor_id).
"""

import argparse
import os
import random
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.extras import execute_values


SENSOR_TYPES = [
	("temperature", "C"),
	("vibration", "mm/s"),
	("pressure", "kPa"),
	("humidity", "%"),
	("voltage", "V"),
]


def get_db_url() -> str:
	db_url = os.getenv(
		"DATABASE_URL",
		"postgresql://smart_user:strong_password@localhost:5432/smart_maintenance_db",
	)
	# Convert async URL if provided
	return db_url.replace("postgresql+asyncpg", "postgresql")


def ensure_sensors(conn, num_sensors: int) -> list[tuple[str, str, str]]:
	"""Insert sensors if not exist and return list of (sensor_id, type, location)."""
	cur = conn.cursor()

	sensors = []
	for i in range(1, num_sensors + 1):
		sensor_id = f"sensor-{i:03d}"
		stype, unit = random.choice(SENSOR_TYPES)
		location = f"Line-{random.randint(1,5)}-Station-{random.randint(1,10)}"
		sensors.append((sensor_id, stype, location))

	# Create sensors table entries (upsert on sensor_id)
	execute_values(
		cur,
		"""
		INSERT INTO sensors (sensor_id, type, location, status)
		VALUES %s
		ON CONFLICT (sensor_id) DO UPDATE
		  SET type = EXCLUDED.type,
			  location = EXCLUDED.location,
			  updated_at = now();
		""",
		tuple((sid, stype, loc, "active") for sid, stype, loc in sensors),
	)
	conn.commit()
	cur.close()
	return sensors


def seed_readings(
	conn,
	sensors: list[tuple[str, str, str]],
	readings_per_sensor: int,
	start_time: datetime,
	step_seconds: int,
):
	cur = conn.cursor()

	# Generate data per sensor
	all_rows = []
	for sensor_id, stype, _loc in sensors:
		unit = next(u for t, u in SENSOR_TYPES if t == stype)
		base = random.uniform(20.0, 80.0)
		for i in range(readings_per_sensor):
			ts = start_time + timedelta(seconds=i * step_seconds)
			# Simple synthetic pattern + noise
			value = base + 10.0 * random.random() * (1 if i % 50 != 0 else -1)
			quality = max(0.0, min(1.0, random.normalvariate(0.98, 0.02)))
			meta = {"firmware": "1.0", "unit": unit}
			all_rows.append(
				(
					sensor_id,
					stype,
					float(f"{value:.3f}"),
					unit,
					ts,
					float(f"{quality:.3f}"),
					meta,
				)
			)

	# Bulk insert with execute_values
	execute_values(
		cur,
		"""
		INSERT INTO sensor_readings
			(sensor_id, sensor_type, value, unit, timestamp, quality, sensor_metadata)
		VALUES %s
		ON CONFLICT DO NOTHING
		""",
		all_rows,
		page_size=10000,
	)
	conn.commit()
	cur.close()


def main():
	parser = argparse.ArgumentParser(description="Seed sensors and readings data")
	parser.add_argument("--sensors", type=int, default=10, help="Number of sensors")
	parser.add_argument(
		"--readings", type=int, default=500, help="Readings per sensor"
	)
	parser.add_argument(
		"--step", type=int, default=60, help="Seconds between readings"
	)
	parser.add_argument(
		"--start-minutes-ago",
		type=int,
		default=500,
		help="Start this many minutes ago",
	)

	args = parser.parse_args()

	db_url = get_db_url()
	conn = psycopg2.connect(db_url)

	# Ensure sensors exist
	sensors = ensure_sensors(conn, args.sensors)

	# Start time
	start_time = datetime.now(timezone.utc) - timedelta(minutes=args.start_minutes_ago)

	seed_readings(conn, sensors, args.readings, start_time, args.step)

	conn.close()
	print(
		f"Seeded {args.sensors} sensors and ~{args.sensors * args.readings} readings."
	)


if __name__ == "__main__":
	main()

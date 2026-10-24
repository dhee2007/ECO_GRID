
import csv
import sqlite3
import json
from pathlib import Path

DATA_DIR = Path("data")
DB_FILE = DATA_DIR / "offline_buffer.db"
SERVER_FILE = DATA_DIR / "synced_readings.csv"
SOURCE_FILE = DATA_DIR / "fused_readings.csv"

DATA_DIR.mkdir(exist_ok=True)


def connect():
    return sqlite3.connect(DB_FILE)


def initialize_database():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                event_id TEXT PRIMARY KEY,
                building_id TEXT NOT NULL,
                date TEXT NOT NULL,
                payload TEXT NOT NULL,
                synced INTEGER NOT NULL DEFAULT 0
            )
        """)


def load_sample_readings(limit=10):
    with open(
        SOURCE_FILE,
        newline="",
        encoding="utf-8-sig"
    ) as file:
        rows = list(csv.DictReader(file))

    return rows[:limit]


def buffer_readings(rows):
    added = 0

    with connect() as conn:
        for row in rows:
            event_id = (
                row["building_id"] + "_"
                + row["date"]
            )

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO readings
                (event_id, building_id, date, payload, synced)
                VALUES (?, ?, ?, ?, 0)
                """,
                (
                    event_id,
                    row["building_id"],
                    row["date"],
                    json.dumps(row)
                )
            )

            added += cursor.rowcount

    return added


def pending_count():
    with connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM readings WHERE synced = 0"
        ).fetchone()[0]


def synchronize():
    with connect() as conn:
        pending = conn.execute(
            """
            SELECT event_id, payload
            FROM readings
            WHERE synced = 0
            ORDER BY event_id
            """
        ).fetchall()

        # This CSV represents a simulated central server.
        existing = {}

        if SERVER_FILE.exists():
            with open(
                SERVER_FILE,
                newline="",
                encoding="utf-8"
            ) as file:
                for row in csv.DictReader(file):
                    existing[row["event_id"]] = row

        for event_id, payload in pending:
            row = json.loads(payload)
            existing[event_id] = {
                "event_id": event_id,
                **row
            }

        if existing:
            fieldnames = list(
                next(iter(existing.values())).keys()
            )

            with open(
                SERVER_FILE,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=fieldnames
                )
                writer.writeheader()
                writer.writerows(existing.values())

        # Mark readings as synced after writing server CSV.
        for event_id, payload in pending:
            conn.execute(
                """
                UPDATE readings
                SET synced = 1
                WHERE event_id = ?
                """,
                (event_id,)
            )

    return len(pending)


# --------------------------------
# DEMONSTRATION
# --------------------------------

initialize_database()

print("\n===== ECOGRID OFFLINE SYNC =====")

print("\n1. Simulating network outage...")

sample = load_sample_readings(limit=10)

added = buffer_readings(sample)

print("New readings buffered:", added)
print("Pending readings:", pending_count())

print("\n2. Simulating network reconnection...")

synced = synchronize()

print("Readings synchronized:", synced)
print("Pending after sync:", pending_count())

print("\n3. Checking duplicate protection...")

duplicates_added = buffer_readings(sample)

print("Duplicate records inserted:", duplicates_added)

print("\nSaved local database:", DB_FILE)
print("Saved simulated server data:", SERVER_FILE)

print("\nOffline synchronization completed!")

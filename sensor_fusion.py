
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DATA = Path("data")
OUTPUT = DATA / "fused_readings.csv"
REPORT = Path("models/sensor_fusion_report.json")

TIME_FORMAT = "%Y-%m-%d %H:%M"

# Load CSV records
def read_csv(filename):
    with open(
        DATA / filename,
        newline="",
        encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


hourly = read_csv("hourly_streams.csv")
daily = read_csv("daily_summary.csv")
manual = read_csv("manual_logs.csv")
buildings = read_csv("buildings.csv")

# Resolve building names to IDs
building_map = {}

for row in buildings:
    building_id = row.get("building_id", "").strip()

    if not building_id:
        continue

    building_map[building_id.lower()] = building_id

    for field in ("building_name", "name", "short_name"):
        name = row.get(field, "").strip()

        if name:
            building_map[name.lower()] = building_id


def resolve_building(value):
    value = value.strip()
    return building_map.get(value.lower(), value)


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


# Daily reference values
daily_reference = {}

for row in daily:
    key = (
        row["building_id"],
        row["date"]
    )
    daily_reference[key] = row


# Group manual readings by building and day
manual_grouped = defaultdict(list)

for row in manual:
    try:
        date = datetime.strptime(
            row["logged_at"], TIME_FORMAT
        ).date().isoformat()
    except ValueError:
        continue

    building = resolve_building(row["building"])
    stream = row["stream"].strip().lower()
    value = number(row["value"])
    unit = row["unit"].strip().lower()

    if value is None:
        continue

    # Convert kL to litres
    if stream == "water" and unit == "kl":
        value *= 1000

    # Convert electricity units to kWh
    if stream == "electricity" and unit in ("units", "kwh"):
        pass

    manual_grouped[
        (building, date, stream)
    ].append(value)


# Group hourly readings by building and day
hourly_grouped = defaultdict(list)

delayed_readings = 0
missing_readings = 0

for row in hourly:
    try:
        event_time = datetime.strptime(
            row["timestamp"], TIME_FORMAT
        )
        received_time = datetime.strptime(
            row["received_at"], TIME_FORMAT
        )
    except ValueError:
        continue

    if received_time - event_time > timedelta(hours=2):
        delayed_readings += 1

    key = (
        row["building_id"],
        event_time.date().isoformat()
    )

    hourly_grouped[key].append(row)


# Build fused daily records
results = []

conflicts = 0
fallbacks = 0

for key, reference in sorted(daily_reference.items()):

    building, date = key
    readings = hourly_grouped.get(key, [])

    output = {
        "date": date,
        "building_id": building,
        "hourly_records": len(readings)
    }

    for stream, column in [
        ("electricity", "electricity_kwh"),
        ("water", "water_litres")
    ]:

        values = [
            number(row.get(column))
            for row in readings
        ]

        valid_values = [
            value for value in values
            if value is not None and value >= 0
        ]

        sensor_total = (
            sum(valid_values)
            if valid_values else None
        )

        reference_value = number(
            reference.get(column)
        )

        manual_values = manual_grouped.get(
            (building, date, stream), []
        )

        # Manual readings may be snapshots or
        # cumulative meter readings, not daily totals.
        # Keep them as supporting evidence.
        manual_value = (
            manual_values[-1]
            if manual_values else None
        )

        if sensor_total is not None and len(readings) >= 18:
            fused_value = sensor_total
            source = "hourly_meter"
            confidence = "high"

        elif reference_value is not None:
            fused_value = reference_value
            source = "daily_reference_fallback"
            confidence = "medium"
            fallbacks += 1

        elif sensor_total is not None:
            fused_value = sensor_total
            source = "partial_hourly_meter"
            confidence = "low"

        else:
            fused_value = None
            source = "missing"
            confidence = "none"
            missing_readings += 1

        # Compare daily reference against sensor sum
        conflict = False

        if (
            sensor_total is not None
            and reference_value is not None
            and reference_value > 0
        ):
            difference = abs(
                sensor_total - reference_value
            ) / reference_value

            if difference > 0.20:
                conflict = True
                conflicts += 1
                confidence = "low"

        output[f"{stream}_fused"] = (
            round(fused_value, 2)
            if fused_value is not None else ""
        )

        output[f"{stream}_source"] = source
        output[f"{stream}_confidence"] = confidence
        output[f"{stream}_conflict"] = conflict

        output[f"{stream}_manual_observation"] = (
            manual_value
            if manual_value is not None else ""
        )

    # Waste comes from daily waste measurements
    waste_columns = [
        "wet_organic_kg",
        "dry_recyclable_kg",
        "ewaste_kg",
        "hazardous_kg"
    ]

    waste_values = [
        number(reference.get(column))
        for column in waste_columns
    ]

    output["waste_generated_kg"] = round(
        sum(v for v in waste_values if v is not None),
        2
    )

    output["waste_source"] = "daily_summary"

    results.append(output)


# Save fused dataset
if results:
    with open(
        OUTPUT, "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys())
        )

        writer.writeheader()
        writer.writerows(results)


report = {
    "hourly_input_records": len(hourly),
    "manual_input_records": len(manual),
    "daily_reference_records": len(daily),
    "fused_daily_records": len(results),
    "delayed_hourly_records": delayed_readings,
    "reference_fallbacks": fallbacks,
    "conflicting_measurements": conflicts,
    "fully_missing_streams": missing_readings
}

REPORT.parent.mkdir(exist_ok=True)

with open(REPORT, "w", encoding="utf-8") as file:
    json.dump(report, file, indent=4)

print("\n===== ECOGRID SENSOR FUSION =====")

for key, value in report.items():
    print(f"{key}: {value}")

print("\nSaved:", OUTPUT)
print("Saved:", REPORT)
print("\nSensor fusion completed!")

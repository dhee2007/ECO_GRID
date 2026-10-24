
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TRAIN_FILE = ROOT / "data/waste_events_train.csv"
TEST_FILE = ROOT / "data/waste_events_test.csv"
OUTPUT_FILE = ROOT / "data/waste_events_test_cleaned.csv"
REPORT_FILE = ROOT / "models/missing_sensor_report.json"

FEATURES = [
    "weight_g",
    "moisture_pct",
    "metal_signal",
    "transparency",
    "acoustic_hardness"
]


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def valid_number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def median(values):
    values = sorted(values)
    n = len(values)

    if n == 0:
        raise ValueError("Cannot calculate median of empty list.")

    middle = n // 2

    if n % 2:
        return values[middle]

    return (values[middle - 1] + values[middle]) / 2


def main():
    train_rows = read_csv(TRAIN_FILE)
    test_rows = read_csv(TEST_FILE)

    # Calculate replacement values from training data only
    medians = {}

    for feature in FEATURES:
        values = [
            valid_number(row.get(feature))
            for row in train_rows
        ]

        values = [v for v in values if v is not None]

        medians[feature] = median(values)

    cleaned_rows = []
    missing_counts = defaultdict(int)
    recovered_events = 0

    for row in test_rows:
        cleaned = dict(row)
        repaired = False

        for feature in FEATURES:
            value = valid_number(row.get(feature))

            if value is None:
                cleaned[feature] = str(medians[feature])
                missing_counts[feature] += 1
                repaired = True

        cleaned["sensor_quality"] = (
            "imputed" if repaired else "original"
        )

        if repaired:
            recovered_events += 1

        cleaned_rows.append(cleaned)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(cleaned_rows[0].keys())
        )

        writer.writeheader()
        writer.writerows(cleaned_rows)

    report = {
        "total_test_events": len(test_rows),
        "events_with_missing_values": recovered_events,
        "original_complete_events": (
            len(test_rows) - recovered_events
        ),
        "missing_values_by_feature": dict(missing_counts),
        "training_medians": medians,
        "method": "Training-set median imputation",
        "note": (
            "Missing numeric sensor values are replaced "
            "with medians calculated from training records. "
            "Imputed events are flagged and predictions "
            "should be treated as lower confidence."
        )
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n===== ECOGRID SENSOR RECOVERY =====")
    print("Total test events:", len(test_rows))
    print("Events requiring recovery:", recovered_events)
    print("Complete original events:", len(test_rows) - recovered_events)

    print("\nMissing values by sensor:")
    for feature in FEATURES:
        print(feature, ":", missing_counts[feature])

    print("\nCleaned dataset:", OUTPUT_FILE)
    print("Report:", REPORT_FILE)
    print("\nSensor recovery completed!")


if __name__ == "__main__":
    main()

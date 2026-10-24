
import csv
import json
import math
import time
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent

TRAIN_FILE = ROOT / "data/waste_events_train.csv"
TEST_FILE = ROOT / "data/waste_events_test_cleaned.csv"
REPORT_FILE = ROOT / "models/edge_simulation_report.json"

FEATURES = [
    "weight_g",
    "moisture_pct",
    "metal_signal",
    "transparency",
    "acoustic_hardness"
]

K = 7
MAX_EVENTS = 200
TARGET_LATENCY_MS = 2000


def numeric(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def main():
    train_rows = read_csv(TRAIN_FILE)
    test_rows = read_csv(TEST_FILE)

    training = []

    for row in train_rows:
        values = [numeric(row.get(f)) for f in FEATURES]

        if all(value is not None for value in values):
            training.append((values, row["category"]))

    if not training:
        raise ValueError("No valid training records found.")

    minimums = [
        min(values[i] for values, _ in training)
        for i in range(len(FEATURES))
    ]

    maximums = [
        max(values[i] for values, _ in training)
        for i in range(len(FEATURES))
    ]

    def normalize(values):
        return [
            (values[i] - minimums[i]) /
            (maximums[i] - minimums[i])
            if maximums[i] != minimums[i]
            else 0.0
            for i in range(len(FEATURES))
        ]

    training = [
        (normalize(values), label)
        for values, label in training
    ]

    def classify(values):
        scaled = normalize(values)
        distances = []

        for train_values, label in training:
            distance = math.sqrt(sum(
                (a - b) ** 2
                for a, b in zip(scaled, train_values)
            ))
            distances.append((distance, label))

        nearest = sorted(
            distances,
            key=lambda item: item[0]
        )[:K]

        votes = Counter()

        for distance, label in nearest:
            votes[label] += 1 / (distance + 1e-9)

        return votes.most_common(1)[0][0]

    timings = []
    categories = Counter()
    skipped = 0

    for row in test_rows[:MAX_EVENTS]:
        values = [numeric(row.get(f)) for f in FEATURES]

        if any(value is None for value in values):
            skipped += 1
            continue

        start = time.perf_counter()
        category = classify(values)
        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        timings.append(elapsed_ms)
        categories[category] += 1

    ordered_timings = sorted(timings)

    mean_ms = (
        sum(timings) / len(timings)
        if timings else 0
    )

    p95_index = (
        math.ceil(0.95 * len(ordered_timings)) - 1
        if ordered_timings else 0
    )

    p95_ms = (
        ordered_timings[p95_index]
        if ordered_timings else 0
    )

    max_ms = max(timings, default=0)

    report = {
        "device": "development_laptop",
        "simulation_type": "sequential_event_inference",
        "events_processed": len(timings),
        "events_skipped": skipped,
        "mean_latency_ms": round(mean_ms, 3),
        "p95_latency_ms": round(p95_ms, 3),
        "max_latency_ms": round(max_ms, 3),
        "target_latency_ms": TARGET_LATENCY_MS,
        "all_events_under_target": (
            len(timings) > 0
            and max_ms < TARGET_LATENCY_MS
        ),
        "category_counts": dict(categories),
        "note": (
            "Laptop-based inference simulation. "
            "Not a benchmark on actual edge hardware. "
            "Training preparation time is excluded."
        )
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n===== ECOGRID EDGE SIMULATION =====")
    print("Events processed:", len(timings))
    print("Events skipped:", skipped)
    print("Mean latency:", round(mean_ms, 3), "ms")
    print("P95 latency:", round(p95_ms, 3), "ms")
    print("Maximum latency:", round(max_ms, 3), "ms")
    print(
        "Under 2-second target:",
        report["all_events_under_target"]
    )
    print("Report saved:", REPORT_FILE)
    print("\nEdge simulation completed!")


if __name__ == "__main__":
    main()


import csv
import json
import math
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN_FILE = ROOT / "data/waste_events_train.csv"
TEST_FILE = ROOT / "data/waste_events_test.csv"
REPORT_FILE = ROOT / "models/optimized_test_report.json"

FEATURES = [
    "weight_g",
    "moisture_pct",
    "metal_signal",
    "transparency",
    "acoustic_hardness"
]

def load_data(path):
    records = []

    with open(path, newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            try:
                x = [float(row[f]) for f in FEATURES]
                y = row["category"].strip()

                if y and all(math.isfinite(v) for v in x):
                    records.append((x, y))
            except (ValueError, KeyError):
                continue

    return records


def scale(x, minimums, maximums):
    return [
        (v - lo) / (hi - lo) if hi > lo else 0.0
        for v, lo, hi in zip(x, minimums, maximums)
    ]


def predict(query, training, k=7):
    distances = []

    for features, label in training:
        distance = sum(
            (a - b) ** 2
            for a, b in zip(query, features)
        )
        distances.append((distance, label))

    distances.sort(key=lambda item: item[0])

    votes = defaultdict(float)

    for distance, label in distances[:k]:
        votes[label] += 1.0 / (math.sqrt(distance) + 1e-6)

    return max(sorted(votes), key=lambda label: votes[label])


def main():
    training = load_data(TRAIN_FILE)
    testing = load_data(TEST_FILE)

    if not training or not testing:
        raise ValueError("Training or test dataset is empty.")

    minimums = [
        min(x[i] for x, _ in training)
        for i in range(len(FEATURES))
    ]

    maximums = [
        max(x[i] for x, _ in training)
        for i in range(len(FEATURES))
    ]

    scaled_training = [
        (scale(x, minimums, maximums), y)
        for x, y in training
    ]

    correct = 0
    times_ms = []
    per_class = defaultdict(lambda: [0, 0])

    for x, actual in testing:
        query = scale(x, minimums, maximums)

        start = time.perf_counter()
        predicted = predict(query, scaled_training)
        elapsed_ms = (time.perf_counter() - start) * 1000

        times_ms.append(elapsed_ms)

        per_class[actual][1] += 1

        if predicted == actual:
            correct += 1
            per_class[actual][0] += 1

    accuracy = 100 * correct / len(testing)

    report = {
        "model": "Weighted KNN",
        "k": 7,
        "training_samples": len(training),
        "test_samples": len(testing),
        "test_accuracy_pct": round(accuracy, 2),
        "mean_prediction_ms": round(
            sum(times_ms) / len(times_ms), 3
        ),
        "maximum_prediction_ms": round(max(times_ms), 3),
        "per_class_recall_pct": {
            label: round(100 * counts[0] / counts[1], 2)
            for label, counts in sorted(per_class.items())
        }
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n===== OPTIMIZED MODEL TEST =====")
    print("Training samples:", len(training))
    print("Test samples:", len(testing))
    print("Independent test accuracy:", round(accuracy, 2), "%")
    print("Mean prediction time:", report["mean_prediction_ms"], "ms")
    print("Maximum prediction time:", report["maximum_prediction_ms"], "ms")

    print("\nPer-category recall:")
    for label, recall in report["per_class_recall_pct"].items():
        print(f"  {label}: {recall}%")

    print("\nReport saved:", REPORT_FILE)
    print("Dashboard model remains unchanged.")


if __name__ == "__main__":
    main()

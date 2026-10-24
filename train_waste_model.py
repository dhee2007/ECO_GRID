
import csv
import json
import math
import random
from collections import Counter
from pathlib import Path

DATA_FILE = Path("data/waste_events_train.csv")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

MODEL_FILE = MODEL_DIR / "waste_classifier.json"
REPORT_FILE = MODEL_DIR / "waste_model_report.json"

FEATURES = [
    "weight_g",
    "moisture_pct",
    "metal_signal",
    "transparency",
    "acoustic_hardness"
]

LABEL = "category"

print("\n===== ECOGRID WASTE CLASSIFIER =====")

# Read dataset
rows = []
skipped = 0

with open(DATA_FILE, newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    missing = [
        name for name in FEATURES + [LABEL]
        if name not in (reader.fieldnames or [])
    ]

    if missing:
        raise ValueError(
            "Missing dataset columns: " + ", ".join(missing)
        )

    for row in reader:
        try:
            features = [
                float(row[name]) for name in FEATURES
            ]
            category = row[LABEL].strip()

            if not category:
                skipped += 1
                continue

            if not all(math.isfinite(x) for x in features):
                skipped += 1
                continue

            rows.append((features, category))

        except (ValueError, TypeError, KeyError):
            skipped += 1

print("Valid records:", len(rows))
print("Skipped records:", skipped)

if len(rows) < 20:
    raise ValueError("Not enough valid training records.")

# Stratified split: 80% training, 20% testing
groups = {}

for features, category in rows:
    groups.setdefault(category, []).append(
        (features, category)
    )

random_generator = random.Random(42)
train = []
test = []

for category, items in sorted(groups.items()):
    random_generator.shuffle(items)

    if len(items) < 2:
        raise ValueError(
            f"Not enough records for category: {category}"
        )

    test_count = max(1, round(len(items) * 0.20))
    test.extend(items[:test_count])
    train.extend(items[test_count:])

print("Categories:", sorted(groups))
print("Training records:", len(train))
print("Testing records:", len(test))

# Calculate scaling parameters using training data only
minimums = []
maximums = []

for column in range(len(FEATURES)):
    values = [
        features[column]
        for features, category in train
    ]
    minimums.append(min(values))
    maximums.append(max(values))

def normalize(values):
    result = []

    for i, value in enumerate(values):
        spread = maximums[i] - minimums[i]

        if spread == 0:
            result.append(0.0)
        else:
            result.append(
                (value - minimums[i]) / spread
            )

    return result

training_data = [
    (normalize(features), category)
    for features, category in train
]

# Pure Python KNN classifier
def predict(features, k=5):
    point = normalize(features)
    distances = []

    for train_features, category in training_data:
        distance = sum(
            (a - b) ** 2
            for a, b in zip(point, train_features)
        )
        distances.append((distance, category))

    nearest = sorted(
        distances,
        key=lambda item: item[0]
    )[:k]

    votes = Counter(
        category for distance, category in nearest
    )

    # Deterministic tie-breaking
    return sorted(
        votes,
        key=lambda category: (
            -votes[category],
            category
        )
    )[0]

# Evaluate on held-out test records
print("\nTesting classifier...")

correct = 0
results = {}

for features, actual in test:
    predicted = predict(features)

    if predicted == actual:
        correct += 1

    results.setdefault(
        actual, {"correct": 0, "total": 0}
    )

    results[actual]["total"] += 1

    if predicted == actual:
        results[actual]["correct"] += 1

accuracy = correct / len(test)

print("\n===== CLASSIFICATION RESULTS =====")
print(f"Accuracy: {accuracy * 100:.2f}%")

print("\nCategory-wise recall:")

for category, result in sorted(results.items()):
    recall = (
        result["correct"] / result["total"]
    ) * 100

    print(
        f"{category}: {recall:.2f}% "
        f"({result['correct']}/{result['total']})"
    )

# Save model data
# Retrain on all labelled records for deployment
all_minimums = [
    min(features[i] for features, label in rows)
    for i in range(len(FEATURES))
]
all_maximums = [
    max(features[i] for features, label in rows)
    for i in range(len(FEATURES))
]

model_data = {
    "model_type": "Pure Python KNN",
    "k": 5,
    "features": FEATURES,
    "categories": sorted(groups),
    "minimums": all_minimums,
    "maximums": all_maximums,
    "training_data": [
        {"features": features, "category": category}
        for features, category in rows
    ]
}

with open(MODEL_FILE, "w", encoding="utf-8") as file:
    json.dump(model_data, file)

report = {
    "model": "Pure Python KNN",
    "accuracy_percent": round(accuracy * 100, 2),
    "training_records": len(train),
    "testing_records": len(test),
    "category_results": results,
    "evaluation_method": "Stratified 80/20 holdout"
}

with open(REPORT_FILE, "w", encoding="utf-8") as file:
    json.dump(report, file, indent=4)

print("\nModel saved:", MODEL_FILE)
print("Report saved:", REPORT_FILE)

if accuracy > 0.85:
    print("\nPASS: Accuracy is above 85%.")
else:
    print("\nAccuracy target not reached yet.")

print("\nTraining and evaluation completed!")

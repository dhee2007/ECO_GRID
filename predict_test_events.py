
import csv
import json
import math
import time

from collections import defaultdict
from pathlib import Path

# ==========================================
# ECOGRID AI - WASTE CLASSIFICATION
# WITH MISSING SENSOR DATA RECOVERY
# ==========================================

ROOT = Path(__file__).resolve().parent.parent

TRAIN_FILE = ROOT / "data/waste_events_train.csv"

# Use cleaned test dataset
TEST_FILE = ROOT / "data/waste_events_test_cleaned.csv"

OUTPUT_FILE = ROOT / "data/waste_test_predictions.csv"

REPORT_FILE = ROOT / "models/waste_prediction_report.json"

FEATURES = [
    "weight_g",
    "moisture_pct",
    "metal_signal",
    "transparency",
    "acoustic_hardness"
]

K = 7


# ==========================================
# STEP 1 - READ DATASET
# ==========================================

def load_rows(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    with open(
        path,
        newline="",
        encoding="utf-8-sig"
    ) as file:

        return list(csv.DictReader(file))


# ==========================================
# STEP 2 - EXTRACT SENSOR FEATURES
# ==========================================

def extract_features(row):

    try:
        values = [
            float(row[feature])
            for feature in FEATURES
        ]

        if all(
            math.isfinite(value)
            for value in values
        ):
            return values

    except (ValueError, KeyError, TypeError):
        pass

    return None


# ==========================================
# STEP 3 - FEATURE SCALING
# ==========================================

def scale_features(values, minimums, maximums):

    scaled = []

    for value, minimum, maximum in zip(
        values,
        minimums,
        maximums
    ):

        if maximum > minimum:
            scaled_value = (
                (value - minimum)
                / (maximum - minimum)
            )
        else:
            scaled_value = 0.0

        scaled.append(scaled_value)

    return scaled


# ==========================================
# STEP 4 - WEIGHTED KNN PREDICTION
# ==========================================

def predict_waste(query, training):

    distances = []

    for features, category in training:

        distance_squared = sum(
            (a - b) ** 2
            for a, b in zip(query, features)
        )

        distances.append(
            (distance_squared, category)
        )

    distances.sort(
        key=lambda item: item[0]
    )

    votes = defaultdict(float)

    for distance_squared, category in distances[:K]:

        distance = math.sqrt(distance_squared)

        weight = 1.0 / (distance + 1e-6)

        votes[category] += weight

    prediction = max(
        sorted(votes),
        key=lambda category: votes[category]
    )

    return prediction


# ==========================================
# STEP 5 - MAIN PROGRAM
# ==========================================

def main():

    print("\n======================================")
    print(" ECOGRID AI - WASTE PREDICTION")
    print("======================================")

    training_rows = load_rows(TRAIN_FILE)
    test_rows = load_rows(TEST_FILE)

    training = []

    for row in training_rows:

        features = extract_features(row)

        category = row.get(
            "category", ""
        ).strip()

        if features is not None and category:

            training.append(
                (features, category)
            )

    if len(training) < K:
        raise ValueError(
            "Not enough valid training records."
        )

    print("\nTraining records:", len(training))
    print("Test records:", len(test_rows))

    # ======================================
    # CALCULATE SCALING VALUES
    # ======================================

    minimums = []

    maximums = []

    for index in range(len(FEATURES)):

        values = [
            features[index]
            for features, category in training
        ]

        minimums.append(min(values))
        maximums.append(max(values))

    scaled_training = []

    for features, category in training:

        scaled_features = scale_features(
            features,
            minimums,
            maximums
        )

        scaled_training.append(
            (scaled_features, category)
        )

    # ======================================
    # PREDICT TEST EVENTS
    # ======================================

    predictions = []

    category_counts = defaultdict(int)

    prediction_times = []

    quality_counts = defaultdict(int)

    skipped = 0

    for index, row in enumerate(
        test_rows,
        start=1
    ):

        features = extract_features(row)

        if features is None:

            skipped += 1
            continue

        scaled_query = scale_features(
            features,
            minimums,
            maximums
        )

        start = time.perf_counter()

        predicted_category = predict_waste(
            scaled_query,
            scaled_training
        )

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        prediction_times.append(elapsed_ms)

        category_counts[
            predicted_category
        ] += 1

        # Identify recovered sensor readings
        sensor_quality = row.get(
            "sensor_quality", "original"
        )

        if sensor_quality == "imputed":

            prediction_quality = "lower_confidence"

        else:

            prediction_quality = "normal"

        quality_counts[
            prediction_quality
        ] += 1

        predictions.append({
            **row,
            "predicted_category": predicted_category,
            "prediction_quality": prediction_quality
        })

        if index % 400 == 0:

            print(
                f"Processed {index}/{len(test_rows)} events..."
            )

    if not predictions:
        raise ValueError(
            "No valid test events available."
        )

    # ======================================
    # SAVE PREDICTIONS
    # ======================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(
                predictions[0].keys()
            )
        )

        writer.writeheader()

        writer.writerows(predictions)

    # ======================================
    # SAVE PERFORMANCE REPORT
    # ======================================

    mean_time = (
        sum(prediction_times)
        / len(prediction_times)
    )

    maximum_time = max(prediction_times)

    report = {
        "model": "Weighted KNN",
        "k": K,
        "training_records": len(training),
        "test_records": len(test_rows),
        "predictions_generated": len(predictions),
        "skipped_records": skipped,
        "mean_prediction_ms": round(
            mean_time, 3
        ),
        "maximum_prediction_ms": round(
            maximum_time, 3
        ),
        "predicted_category_counts": dict(
            category_counts
        ),
        "prediction_quality_counts": dict(
            quality_counts
        ),
        "accuracy": None,
        "note": (
            "Test dataset contains no ground-truth "
            "category labels, so accuracy cannot "
            "be calculated. Missing sensor values "
            "were replaced using training medians. "
            "Imputed events are marked lower_confidence. "
            "Latency is measured on the development "
            "laptop, not on edge hardware."
        )
    }

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )

    # ======================================
    # DISPLAY RESULTS
    # ======================================

    print("\n========== RESULTS ==========")

    print(
        "Predictions generated:",
        len(predictions)
    )

    print(
        "Skipped records:",
        skipped
    )

    print(
        "Mean prediction time:",
        round(mean_time, 3),
        "ms"
    )

    print(
        "Maximum prediction time:",
        round(maximum_time, 3),
        "ms"
    )

    print("\nPredicted waste categories:")

    for category, count in sorted(
        category_counts.items()
    ):

        print(
            f"{category}: {count}"
        )

    print("\nPrediction quality:")

    for quality, count in sorted(
        quality_counts.items()
    ):

        print(
            f"{quality}: {count}"
        )

    print("\nPredictions saved:", OUTPUT_FILE)

    print("Report saved:", REPORT_FILE)

    print("\nPrediction completed!")


if __name__ == "__main__":
    main()

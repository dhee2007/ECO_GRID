
import csv
import json
import math
import random
import time

from pathlib import Path
from collections import defaultdict

# ==========================================
# ECOGRID - FAST KNN MODEL OPTIMIZATION
# ==========================================

FEATURES = [
    "weight_g",
    "moisture_pct",
    "metal_signal",
    "transparency",
    "acoustic_hardness"
]

LABEL = "category"

DATA_FILE = Path("data/waste_events_train.csv")
REPORT_FILE = Path("models/waste_optimization_report.json")

RANDOM_SEED = 42
VALIDATION_FRACTION = 0.20

K_VALUES = [1, 3, 5, 7, 9, 11, 15]

random.seed(RANDOM_SEED)


# ==========================================
# STEP 1 - LOAD DATA
# ==========================================

def load_data():

    with open(
        DATA_FILE,
        newline="",
        encoding="utf-8-sig"
    ) as file:

        rows = list(csv.DictReader(file))

    data = []

    for row in rows:

        try:
            features = [
                float(row[column])
                for column in FEATURES
            ]

            category = row[LABEL].strip()

            if (
                category
                and all(
                    math.isfinite(value)
                    for value in features
                )
            ):
                data.append(
                    (features, category)
                )

        except (ValueError, KeyError):
            continue

    return data


# ==========================================
# STEP 2 - STRATIFIED DATA SPLIT
# ==========================================

def stratified_split(data):

    grouped = defaultdict(list)

    for features, category in data:
        grouped[category].append(
            (features, category)
        )

    training = []
    validation = []

    rng = random.Random(RANDOM_SEED)

    for category in sorted(grouped):

        samples = grouped[category]

        rng.shuffle(samples)

        validation_count = max(
            1,
            int(
                len(samples)
                * VALIDATION_FRACTION
            )
        )

        validation.extend(
            samples[:validation_count]
        )

        training.extend(
            samples[validation_count:]
        )

    return training, validation


# ==========================================
# STEP 3 - FEATURE SCALING
# ==========================================

def get_scaling_limits(training):

    minimums = []
    maximums = []

    for index in range(len(FEATURES)):

        values = [
            features[index]
            for features, category in training
        ]

        minimums.append(min(values))
        maximums.append(max(values))

    return minimums, maximums


def scale_features(features, minimums, maximums):

    scaled = []

    for value, minimum, maximum in zip(
        features,
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
# STEP 4 - DISTANCE CALCULATION
# ==========================================

def calculate_distance(first, second):

    return math.sqrt(
        sum(
            (a - b) ** 2
            for a, b in zip(first, second)
        )
    )


# ==========================================
# STEP 5 - PREDICT FROM NEAREST NEIGHBORS
# ==========================================

def predict_from_neighbors(neighbors, k, weighted):

    votes = defaultdict(float)

    for distance, category in neighbors[:k]:

        if weighted:
            vote = 1.0 / (distance + 1e-6)
        else:
            vote = 1.0

        votes[category] += vote

    # Alphabetical tie-breaking makes results reproducible
    prediction = max(
        sorted(votes),
        key=lambda category: votes[category]
    )

    return prediction


# ==========================================
# STEP 6 - OPTIMIZE ALL CONFIGURATIONS
# ==========================================

def optimize(training, validation):

    configurations = [
        (k, weighted)
        for k in K_VALUES
        for weighted in [False, True]
    ]

    correct_counts = {
        config: 0
        for config in configurations
    }

    max_k = max(K_VALUES)

    print("\nTesting KNN configurations...\n")

    start = time.perf_counter()

    for index, (query, actual) in enumerate(
        validation,
        start=1
    ):

        distances = []

        # Calculate distances only once
        for features, category in training:

            distance = calculate_distance(
                query,
                features
            )

            distances.append(
                (distance, category)
            )

        # Sort once for every configuration
        distances.sort(
            key=lambda item: item[0]
        )

        nearest = distances[:max_k]

        # Test all K values and voting methods
        for k, weighted in configurations:

            prediction = predict_from_neighbors(
                nearest,
                k,
                weighted
            )

            if prediction == actual:
                correct_counts[
                    (k, weighted)
                ] += 1

        if index % 200 == 0:
            print(
                f"Processed {index}/{len(validation)} "
                "validation samples..."
            )

    elapsed = time.perf_counter() - start

    results = []

    for k, weighted in configurations:

        accuracy = (
            100
            * correct_counts[(k, weighted)]
            / len(validation)
        )

        results.append({
            "k": k,
            "weighted": weighted,
            "accuracy_pct": round(accuracy, 2)
        })

        print(
            f"k={k:2} | "
            f"weighted={weighted} | "
            f"accuracy={accuracy:.2f}%"
        )

    return results, elapsed


# ==========================================
# STEP 7 - MAIN PROGRAM
# ==========================================

def main():

    print("\n====================================")
    print(" ECOGRID AI - MODEL OPTIMIZATION")
    print("====================================")

    data = load_data()

    if len(data) < 20:
        raise ValueError(
            "Not enough training records."
        )

    training, validation = stratified_split(data)

    if not training or not validation:
        raise ValueError(
            "Training or validation split is empty."
        )

    print("\nTotal samples:", len(data))
    print("Training samples:", len(training))
    print("Validation samples:", len(validation))

    minimums, maximums = get_scaling_limits(
        training
    )

    scaled_training = [
        (
            scale_features(
                features,
                minimums,
                maximums
            ),
            category
        )
        for features, category in training
    ]

    scaled_validation = [
        (
            scale_features(
                features,
                minimums,
                maximums
            ),
            category
        )
        for features, category in validation
    ]

    results, elapsed = optimize(
        scaled_training,
        scaled_validation
    )

    best = max(
        results,
        key=lambda result: result["accuracy_pct"]
    )

    average_time_ms = (
        elapsed * 1000
        / len(scaled_validation)
    )

    print("\n====================================")
    print(" BEST VALIDATION CONFIGURATION")
    print("====================================")

    print("Best K:", best["k"])
    print("Weighted voting:", best["weighted"])
    print(
        "Validation accuracy:",
        best["accuracy_pct"],
        "%"
    )

    print(
        "Average optimization time per sample:",
        round(average_time_ms, 3),
        "ms"
    )

    print(
        "Total optimization time:",
        round(elapsed, 2),
        "seconds"
    )

    # Save optimization report
    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report = {
        "total_samples": len(data),
        "training_samples": len(training),
        "validation_samples": len(validation),
        "best_configuration": best,
        "average_optimization_time_ms": round(
            average_time_ms, 3
        ),
        "total_optimization_seconds": round(
            elapsed, 2
        ),
        "all_results": results,
        "notes": (
            "Accuracy is from a validation split "
            "used for model selection. "
            "An independent test is still required. "
            "Timing includes distance calculations "
            "and evaluation of all configurations; "
            "it is not a dedicated edge-device benchmark."
        )
    }

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

    print("\nReport saved:", REPORT_FILE)

    print(
        "Existing dashboard classifier "
        "has not been modified."
    )

    print("\nOptimization completed!")


if __name__ == "__main__":
    main()

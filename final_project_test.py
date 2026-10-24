
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "data/buildings.csv",
    "data/daily_summary.csv",
    "data/hourly_streams.csv",
    "data/manual_logs.csv",
    "data/fused_readings.csv",
    "data/waste_test_predictions.csv",
    "data/advanced_forecasts.csv",
    "data/circular_recommendations.csv",
    "data/ecopoints_leaderboard.csv",
    "data/scalability_simulation.csv",
    "models/waste_classifier.json",
    "models/waste_optimization_report.json",
    "models/waste_prediction_report.json",
    "models/missing_sensor_report.json",
    "models/sensor_fusion_report.json",
    "models/forecast_evaluation.json",
    "models/circular_optimizer_report.json",
    "models/scalability_report.json",
    "models/edge_simulation_report.json",
    "dashboard/app.py"
]


def read_csv(relative_path):
    with open(
        ROOT / relative_path,
        newline="",
        encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


def read_json(relative_path):
    with open(
        ROOT / relative_path,
        encoding="utf-8"
    ) as file:
        return json.load(file)


def check(condition, description):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {description}")
    return bool(condition)


def main():
    print("\n===== ECOGRID FINAL PROJECT TEST =====")

    results = []

    for filename in REQUIRED_FILES:
        exists = (ROOT / filename).is_file()

        results.append(
            check(exists, f"File exists: {filename}")
        )

    if not all(results):
        print("\nSome required files are missing.")
        print("Fix missing files before continuing.")
        return

    predictions = read_csv(
        "data/waste_test_predictions.csv"
    )

    forecasts = read_csv(
        "data/advanced_forecasts.csv"
    )

    recommendations = read_csv(
        "data/circular_recommendations.csv"
    )

    leaderboard = read_csv(
        "data/ecopoints_leaderboard.csv"
    )

    scalability = read_json(
        "models/scalability_report.json"
    )

    edge = read_json(
        "models/edge_simulation_report.json"
    )

    results.append(
        check(
            len(predictions) == 1601,
            "All 1601 waste events predicted"
        )
    )

    results.append(
        check(
            len(forecasts) == 192,
            "192 forecast records generated"
        )
    )

    results.append(
        check(
            len(recommendations) == 24,
            "24 circular recommendations generated"
        )
    )

    results.append(
        check(
            len(leaderboard) == 8,
            "EcoPoints leaderboard contains 8 buildings"
        )
    )

    results.append(
        check(
            scalability.get("simulated_buildings") == 30,
            "30-building simulation completed"
        )
    )

    results.append(
        check(
            scalability.get("total_sensor_records", 0) > 0,
            "Scalability sensor records generated"
        )
    )

    results.append(
        check(
            edge.get("events_processed") == 200,
            "200 edge events processed"
        )
    )

    results.append(
        check(
            edge.get("all_events_under_target") is True,
            "Laptop inference below 2 seconds"
        )
    )

    print("\n===================================")
    print("Checks passed:", sum(results))
    print("Total checks:", len(results))

    if all(results):
        print("RESULT: ALL AUTOMATED CHECKS PASSED")
    else:
        print("RESULT: SOME CHECKS FAILED")

    print("===================================")


if __name__ == "__main__":
    main()

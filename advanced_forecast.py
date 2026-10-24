
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data/hourly_streams.csv"
OUTPUT = ROOT / "data/advanced_forecasts.csv"
REPORT = ROOT / "models/forecast_evaluation.json"

HORIZONS = [6, 12]


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def parse_time(value):
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def predict(history, target):
    # Use the same hour on previous days.
    same_hour = [
        value
        for timestamp, value in history.items()
        if timestamp.hour == target.hour
        and timestamp < target
    ]

    if same_hour:
        return sum(same_hour[-7:]) / len(same_hour[-7:])

    # Fallback to the latest available readings.
    recent = [
        value
        for timestamp, value in history.items()
        if timestamp < target
    ]

    if recent:
        return sum(recent[-6:]) / len(recent[-6:])

    return None


def main():
    data = defaultdict(lambda: defaultdict(dict))

    with open(INPUT, newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            timestamp = parse_time(row["timestamp"])
            building = row["building_id"]

            if timestamp is None:
                continue

            timestamp = timestamp.replace(
                minute=0, second=0, microsecond=0
            )

            for resource in ("electricity_kwh", "water_litres"):
                value = number(row.get(resource))
                if value is not None and value >= 0:
                    data[building][resource][timestamp] = value

    forecasts = []
    evaluation = {}

    for building, resources in sorted(data.items()):
        evaluation[building] = {}

        for resource, readings in resources.items():
            ordered = sorted(readings.items())
            if len(ordered) < 24:
                continue

            # Reserve the last 20% for evaluation.
            split = max(24, int(len(ordered) * 0.8))
            split = min(split, len(ordered) - 1)

            train = dict(ordered[:split])
            test = ordered[split:]

            errors = []

            # Rolling-origin evaluation:
            # only readings before the forecast origin
            # are available to the model.
            for origin_index in range(split - 1, len(ordered) - 1):
                origin = ordered[origin_index][0]
                known = dict(ordered[:origin_index + 1])

                for horizon in HORIZONS:
                    target = origin + timedelta(hours=horizon)

                    if target not in readings:
                        continue

                    # Evaluate only held-out targets.
                    if target <= ordered[split - 1][0]:
                        continue

                    prediction = predict(known, target)

                    if prediction is not None:
                        errors.append({
                            "horizon": horizon,
                            "absolute_error": abs(
                                prediction - readings[target]
                            )
                        })

            evaluation[building][resource] = {}

            for horizon in HORIZONS:
                values = [
                    x["absolute_error"]
                    for x in errors
                    if x["horizon"] == horizon
                ]

                evaluation[building][resource][
                    f"{horizon}h_mae"
                ] = (
                    round(sum(values) / len(values), 3)
                    if values else None
                )

            # Produce future forecasts from all observed data.
            history = dict(ordered)
            last_time = ordered[-1][0]

            for hour in range(1, 13):
                target = last_time + timedelta(hours=hour)
                value = predict(history, target)

                if value is not None:
                    forecasts.append({
                        "building_id": building,
                        "timestamp": target.isoformat(),
                        "resource": resource,
                        "forecast_value": round(value, 3),
                        "unit": (
                            "kWh" if resource == "electricity_kwh"
                            else "litres"
                        ),
                        "hours_ahead": hour
                    })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    if forecasts:
        with open(
            OUTPUT, "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=list(forecasts[0].keys())
            )
            writer.writeheader()
            writer.writerows(forecasts)

    with open(REPORT, "w", encoding="utf-8") as file:
        json.dump(evaluation, file, indent=2)

    print("\n===== ECOGRID ADVANCED FORECAST =====")
    print("Buildings analyzed:", len(data))
    print("Forecast rows generated:", len(forecasts))
    print("Evaluation report:", REPORT)
    print("Forecast file:", OUTPUT)
    print("\nForecasting completed!")


if __name__ == "__main__":
    main()

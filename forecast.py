
import csv
import json
from collections import defaultdict
from pathlib import Path

# Read campus dataset
data = defaultdict(list)

with open("data/campus_data.csv", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        building = row["Building"]
        data[building].append({
            "hour": int(row["Hour"]),
            "time": int(row["Time_of_Day"]),
            "electricity": float(row["Electricity"]),
            "water": float(row["Water"]),
            "waste": float(row["Waste"])
        })

# Learn average consumption patterns
# from the first 23 days
training_hours = 23 * 24

patterns = {}

for building, records in data.items():
    patterns[building] = {}

    for time_of_day in range(24):
        matching = [
            r for r in records[:training_hours]
            if r["time"] == time_of_day
        ]

        patterns[building][time_of_day] = {}

        for resource in ["electricity", "water", "waste"]:
            values = [r[resource] for r in matching]
            patterns[building][time_of_day][resource] = (
                sum(values) / len(values)
            )

# Test on the last 7 days
errors = defaultdict(list)

for building, records in data.items():
    for record in records[training_hours:]:
        predicted = patterns[building][record["time"]]

        for resource in ["electricity", "water", "waste"]:
            errors[resource].append(
                abs(record[resource] - predicted[resource])
            )

print("FORECAST MODEL EVALUATION")

for resource, values in errors.items():
    mae = sum(values) / len(values)
    print(f"{resource}: MAE = {mae:.2f}")

# Forecast next 12 hours for each building
forecasts = []

for building, records in data.items():
    last_hour = records[-1]["hour"]

    for step in range(1, 13):
        future_hour = last_hour + step
        time_of_day = future_hour % 24
        prediction = patterns[building][time_of_day]

        forecasts.append({
            "building": building,
            "hours_ahead": step,
            "time_of_day": time_of_day,
            "electricity": round(
                prediction["electricity"], 2
            ),
            "water": round(
                prediction["water"], 2
            ),
            "waste": round(
                prediction["waste"], 2
            )
        })

Path("models").mkdir(exist_ok=True)

with open("models/forecast.json", "w") as file:
    json.dump(forecasts, file, indent=4)

print("\n12-hour forecasts generated!")
print("Saved to models/forecast.json")

for forecast in forecasts[:3]:
    print(forecast)

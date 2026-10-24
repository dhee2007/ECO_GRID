
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT / "data/daily_summary.csv"
OUTPUT_FILE = ROOT / "data/circular_recommendations.csv"
LEADERBOARD_FILE = ROOT / "data/ecopoints_leaderboard.csv"
REPORT_FILE = ROOT / "models/circular_optimizer_report.json"


def read_rows():
    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def num(row, key):
    try:
        return float(row.get(key, 0) or 0)
    except ValueError:
        return 0.0


def main():
    rows = read_rows()

    if not rows:
        raise ValueError("Daily summary dataset is empty.")

    buildings = defaultdict(list)

    for row in rows:
        buildings[row["building_id"]].append(row)

    recommendations = []
    leaderboard = []

    for building_id, records in sorted(buildings.items()):
        electricity = sum(
            num(row, "electricity_kwh") for row in records
        )
        water = sum(
            num(row, "water_litres") for row in records
        )
        solar = sum(
            num(row, "solar_generation_kwh") for row in records
        )
        recycled = sum(
            num(row, "recycled_kg") for row in records
        )
        composted = sum(
            num(row, "composted_kg") for row in records
        )
        landfill = sum(
            num(row, "landfill_kg") for row in records
        )

        waste_total = recycled + composted + landfill

        diversion_rate = (
            100 * (recycled + composted) / waste_total
            if waste_total > 0 else 0
        )

        solar_ratio = (
            min(100, 100 * solar / electricity)
            if electricity > 0 else 0
        )

        # Illustrative improvement scenarios, not measured savings
        electricity_saving = electricity * 0.10
        water_saving = water * 0.10
        landfill_reduction = landfill * 0.15

        actions = [
            {
                "building_id": building_id,
                "resource": "electricity",
                "recommendation": (
                    "Optimize lighting and HVAC schedules"
                ),
                "estimated_saving": round(electricity_saving, 2),
                "unit": "kWh",
                "assumption": "10% reduction scenario"
            },
            {
                "building_id": building_id,
                "resource": "water",
                "recommendation": (
                    "Inspect leaks and optimize water usage"
                ),
                "estimated_saving": round(water_saving, 2),
                "unit": "litres",
                "assumption": "10% reduction scenario"
            },
            {
                "building_id": building_id,
                "resource": "waste",
                "recommendation": (
                    "Improve segregation, recycling and composting"
                ),
                "estimated_saving": round(landfill_reduction, 2),
                "unit": "kg",
                "assumption": "15% landfill reduction scenario"
            }
        ]

        recommendations.extend(actions)

        # Illustrative EcoPoints score, not a verified impact measure
        ecopoints = round(
            diversion_rate * 5
            + solar_ratio * 2
            + min(300, recycled + composted),
            1
        )

        leaderboard.append({
            "building_id": building_id,
            "ecopoints": ecopoints,
            "diversion_rate_pct": round(diversion_rate, 2),
            "solar_ratio_pct": round(solar_ratio, 2),
            "recycled_composted_kg": round(
                recycled + composted, 2
            )
        })

    leaderboard.sort(
        key=lambda row: row["ecopoints"],
        reverse=True
    )

    for rank, row in enumerate(leaderboard, start=1):
        row["rank"] = rank

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(recommendations[0].keys())
        )
        writer.writeheader()
        writer.writerows(recommendations)

    with open(
        LEADERBOARD_FILE, "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(leaderboard[0].keys())
        )
        writer.writeheader()
        writer.writerows(leaderboard)

    report = {
        "buildings_analyzed": len(buildings),
        "recommendations_generated": len(recommendations),
        "leaderboard_entries": len(leaderboard),
        "top_building": leaderboard[0]["building_id"],
        "note": (
            "Savings and EcoPoints are illustrative. "
            "They are not verified reductions or rewards."
        )
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n===== ECOGRID CIRCULAR OPTIMIZER =====")
    print("Buildings analyzed:", len(buildings))
    print("Recommendations:", len(recommendations))
    print("Top EcoPoints building:", leaderboard[0]["building_id"])
    print("Saved:", OUTPUT_FILE)
    print("Saved:", LEADERBOARD_FILE)
    print("\nCircular optimization completed!")


if __name__ == "__main__":
    main()

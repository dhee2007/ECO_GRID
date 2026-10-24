
import csv
import json
import random
import time
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "data/hourly_streams.csv"
OUTPUT = ROOT / "data/scalability_simulation.csv"
REPORT = ROOT / "models/scalability_report.json"

TARGET_BUILDINGS = 30
random.seed(42)


def load_data():
    with open(INPUT, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def main():
    start = time.perf_counter()

    original = load_data()

    if not original:
        raise ValueError("Hourly dataset is empty.")

    source_buildings = sorted({
        row["building_id"] for row in original
    })

    grouped = defaultdict(list)

    for row in original:
        grouped[row["building_id"]].append(row)

    simulated = []
    offline_count = 0
    noisy_count = 0
    recovered_count = 0

    for index in range(TARGET_BUILDINGS):

        new_building = f"SIM_B{index + 1:02d}"
        source = source_buildings[index % len(source_buildings)]

        for row in grouped[source]:

            record = row.copy()
            record["building_id"] = new_building

            # Simulate a temporary offline event.
            offline = random.random() < 0.05

            # Simulate noisy electricity readings.
            noisy = random.random() < 0.10

            record["offline_simulated"] = str(offline)
            record["noise_simulated"] = str(noisy)

            if offline:
                offline_count += 1

                # Simulated local buffering and recovery.
                record["sync_status"] = "recovered_from_buffer"
                recovered_count += 1

            else:
                record["sync_status"] = "received"

            if noisy:
                noisy_count += 1

                try:
                    original_value = float(
                        record["electricity_kwh"]
                    )

                    multiplier = random.uniform(0.85, 1.15)

                    record["electricity_kwh"] = round(
                        original_value * multiplier, 3
                    )

                except (ValueError, TypeError):
                    pass

            simulated.append(record)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(simulated[0].keys())

    with open(
        OUTPUT, "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(simulated)

    elapsed = time.perf_counter() - start

    report = {
        "source_buildings": len(source_buildings),
        "simulated_buildings": TARGET_BUILDINGS,
        "total_sensor_records": len(simulated),
        "simulated_offline_events": offline_count,
        "simulated_noisy_events": noisy_count,
        "simulated_buffer_recoveries": recovered_count,
        "processing_seconds": round(elapsed, 4),
        "records_per_second": round(
            len(simulated) / elapsed, 2
        ) if elapsed else 0,
        "note": (
            "Synthetic 30-building workload generated "
            "from existing building data. Offline recovery "
            "is simulated through status labels; this "
            "does not validate real network recovery."
        )
    }

    with open(REPORT, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n===== ECOGRID SCALABILITY TEST =====")
    print("Original buildings:", len(source_buildings))
    print("Simulated buildings:", TARGET_BUILDINGS)
    print("Total records:", len(simulated))
    print("Offline events:", offline_count)
    print("Noisy events:", noisy_count)
    print("Simulated recoveries:", recovered_count)
    print("Processing time:", round(elapsed, 3), "seconds")
    print("Records/second:", report["records_per_second"])
    print("\nScalability simulation completed!")


if __name__ == "__main__":
    main()


import csv
from pathlib import Path

files = [
    "data/hourly_streams.csv",
    "data/manual_logs.csv",
    "data/daily_summary.csv"
]

for filename in files:
    print("\n" + "=" * 50)
    print("FILE:", filename)

    path = Path(filename)

    if not path.exists():
        print("ERROR: File not found")
        continue

    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        print("COLUMNS:", reader.fieldnames)
        print("\nFIRST 3 RECORDS:")

        for index, row in enumerate(reader):
            if index >= 3:
                break
            print(row)

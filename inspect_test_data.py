
import csv
from pathlib import Path

files = [
    Path("data/waste_events_train.csv"),
    Path("data/waste_events_test.csv")
]

for path in files:
    print("\n" + "=" * 50)
    print("FILE:", path)

    if not path.exists():
        print("ERROR: File not found")
        continue

    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        print("COLUMNS:", reader.fieldnames)

        count = 0

        for row in reader:
            if count < 3:
                print("ROW:", row)
            count += 1

        print("TOTAL ROWS:", count)

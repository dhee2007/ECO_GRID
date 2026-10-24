
import csv
from collections import Counter
from pathlib import Path

file_path = Path("data/waste_events_train.csv")

if not file_path.exists():
    print("ERROR: Training dataset not found.")
    raise SystemExit(1)

with open(file_path, newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)
    rows = list(reader)

if not rows:
    print("ERROR: Dataset is empty.")
    raise SystemExit(1)

print("\n===== ECOGRID WASTE DATASET TEST =====")

print("Total records:", len(rows))
print("Available columns:", list(rows[0].keys()))

if "category" not in rows[0]:
    print("ERROR: 'category' column not found.")
    raise SystemExit(1)

labels = [
    row["category"].strip()
    for row in rows
    if row.get("category", "").strip()
]

counts = Counter(labels)

print("\nWaste categories:")

for category, count in counts.most_common():
    print(f"{category}: {count} records")

print("\nNumber of categories:", len(counts))

if len(counts) >= 5:
    print("PASS: Dataset contains at least 5 categories.")
else:
    print("WARNING: Fewer than 5 categories found.")

print("\nDataset inspection completed.")
print("Model accuracy has NOT been measured yet.")

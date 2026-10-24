
import csv
import random
from pathlib import Path

random.seed(42)

buildings = ["Academic Block", "Hostel", "Cafeteria"]
data = []

for building in buildings:
    for hour in range(24 * 30):
        time_of_day = hour % 24

        electricity = random.randint(10, 50)
        water = random.randint(50, 200)
        waste = random.randint(2, 20)

        if building == "Cafeteria" and time_of_day in [12, 13, 19, 20]:
            electricity += 20
            water += 100
            waste += 15

        if building == "Academic Block" and 9 <= time_of_day <= 17:
            electricity += 15

        if building == "Hostel" and time_of_day >= 20:
            electricity += 10

        data.append([
            building,
            hour,
            time_of_day,
            electricity,
            water,
            waste
        ])

Path("data").mkdir(exist_ok=True)

with open("data/campus_data.csv", "w", newline="") as file:
    writer = csv.writer(file)

    writer.writerow([
        "Building",
        "Hour",
        "Time_of_Day",
        "Electricity",
        "Water",
        "Waste"
    ])

    writer.writerows(data)

print("Dataset created successfully!")
print("Total records:", len(data))
print("Saved to data/campus_data.csv")

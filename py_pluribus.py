#Exercise 3 ->> Append multiple points and track the last N updates
import json
import os
import random
from datetime import datetime, timezone

STORAGE_FILE = "device_storage.json"
MAX_POINTS = 5  # last N points per device

# Load existing storage
if os.path.exists(STORAGE_FILE):
    with open(STORAGE_FILE, "r") as f:
        storage = json.load(f)
else:
    storage = {"latest": {}, "logs": {}}

# Simulate new GPS updates for a device
imei = "3345689"

for i in range(10):  # simulate 10 updates
    new_point = {
        "imei": imei,
        "lat": round(-1.2345 + random.uniform(-0.01, 0.01), 5),
        "long": round(23 + random.uniform(-0.01, 0.01), 5),
        "speed": random.randint(0, 100),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

    # Update latest
    storage["latest"][imei] = new_point

    # Update logs
    logs = storage["logs"].setdefault(imei, [])
    logs.insert(0, new_point)  # newest first

    # Keep only last N points
    if len(logs) > MAX_POINTS:
        del logs[MAX_POINTS:]

    print(f"Stored point {i+1}: {new_point}")

# Write back to disk
with open(STORAGE_FILE, "w") as f:
    json.dump(storage, f, indent=2)

# Verify
print("\nLatest point:", storage["latest"][imei])
print("All stored points (max last 5):", storage["logs"][imei])

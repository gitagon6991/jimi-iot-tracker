# Exercise 2 - store device data locally
# first import the modules
import json
import os

#define the storage path and the max points
STORAGE_FILE = "device_storage.json"
MAX_POINTS = 5 #store last 5 locations per device

#LOAD EXISTING STORAGE IF ANY
if os.path.exists(STORAGE_FILE):
    with open(STORAGE_FILE, "r") as f:
        storage = json.load(f)
else:
    storage = {"latest": {}, "logs": {}}

#Save New Point
#lets assume its clean_data from py_majora
clean_data = {
    "imei": "3345689",
    "device": "iot",
    "lat": -1.2345,
    "long": 23,
    "speed": 5
}

imei = clean_data["imei"]

#update the latest
storage["latest"][imei] = clean_data

#Update log
logs = storage["logs"].setdefault(imei, [])
logs.insert(0, clean_data) #newest first

#Keep only N points
if len(logs) > MAX_POINTS:
    del logs[MAX_POINTS:]

#Write back to disk
with open(STORAGE_FILE, "w") as f:
    json.dump(storage, f, indent=2)

# Print safely
latest = storage["latest"].get(imei)
log = storage["logs"].get(imei, [])

#Test it
print(f"latest for {imei}:", storage["latest"][imei])
print(f"logs for {imei}:", storage["logs"][imei])
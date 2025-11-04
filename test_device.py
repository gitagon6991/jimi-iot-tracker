import requests

data = {
    "imei": "JIMI123",
    "lat": -1.2921,
    "lon": 36.8219,
    "speed": 80,
    "ignition": True
}

r = requests.post("http://127.0.0.1:8000/jimi/push", json=data)
print(r.status_code, r.text)

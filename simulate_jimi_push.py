import requests
import time
import random

ENDPOINT = "http://127.0.0.1:8000/jimi/push"  # change to your ngrok/url when testing externally

def simulate_single(imei="862798051215438"):
    lat = -1.29 + random.random()*0.02
    lon = 36.82 + random.random()*0.02
    speed = random.randint(0, 120)
    payload = {
        "imei": imei,
        "lat": lat,
        "lon": lon,
        "speed": speed,
        "gpstime": None  # server will set now if None
    }
    r = requests.post(ENDPOINT, json=payload, timeout=10)
    print(r.status_code, r.text)

if __name__ == "__main__":
    for i in range(5):
        simulate_single()
        time.sleep(1)

import requests
import json
from datetime import datetime, timezone

class ERPNextSync:
    def __init__(self, base_url, api_key, api_secret):
        """
        Initialize ERPNext connection details.
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {api_key}:{api_secret}"
        }

    def send_telemetry(self, imei, lat, lon, speed, ignition, timestamp=None):
        """
        Send single telemetry record to ERPNext.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        data = {
            "doctype": "Vehicle Telemetry",  # Must match your custom Doctype in ERPNext
            "imei": imei,
            "latitude": lat,
            "longitude": lon,
            "speed": speed,
            "ignition": ignition,
            "timestamp": timestamp
        }

        endpoint = f"{self.base_url}/api/resource/Vehicle Telemetry"
        response = requests.post(endpoint, headers=self.headers, data=json.dumps(data))

        if response.status_code == 200 or response.status_code == 201:
            print(f"[ERPNext] Uploaded telemetry for {imei}")
        else:
            print(f"[ERPNext] Upload failed: {response.status_code} - {response.text}")

    def bulk_upload(self, records):
        """
        Send multiple records (e.g. from local JSON or SQLite).
        """
        for record in records:
            try:
                self.send_telemetry(**record)
            except Exception as e:
                print(f"Error uploading record {record}: {e}")

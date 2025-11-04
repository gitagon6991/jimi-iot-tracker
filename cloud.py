import requests
import logging
from typing import Dict

logger = logging.getLogger("erp")

class ERPService:
    def __init__(self, base_url: str, api_key: str, api_secret: str):
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_key = api_key
        self.api_secret = api_secret

    def _headers(self):
        if not (self.api_key and self.api_secret):
            return {"Content-Type": "application/json"}
        return {
            "Content-Type": "application/json",
            "Authorization": f"token {self.api_key}:{self.api_secret}"
        }

    def create_gps_log(self, point: Dict):
        """
        Create a new 'GPS Log' DocType in ERPNext.
        Adjust the DocType name and fields if your ERPNext differs.
        """
        if not self.base_url:
            logger.debug("ERP URL not configured, skipping upload")
            return {"skipped": True}
        doc = {
            "doctype": "GPS Log",
            "device_imei": point.get("imei"),
            "latitude": point.get("latitude"),
            "longitude": point.get("longitude"),
            "speed_kmh": point.get("speed_kmh"),
            "timestamp": point.get("timestamp"),
            "raw_payload": point.get("raw")
        }
        url = f"{self.base_url}/api/resource/GPS Log"
        r = requests.post(url, json=doc, headers=self._headers(), timeout=15)
        try:
            r.raise_for_status()
        except Exception as e:
            logger.exception("Failed creating GPS Log: %s %s", r.status_code, r.text)
            raise
        return r.json()

    def upsert_vehicle_last_location(self, point: Dict):
        """
        Optional: maintain a Vehicle record keyed by IMEI: update last known location
        We try to find Vehicle with name = imei and update custom fields 'last_lat' and 'last_lng'.
        """
        if not self.base_url:
            return {"skipped": True}
        imei = point.get("imei")
        if not imei:
            return {"error": "no imei"}

        # Try to get Vehicle by name (assuming Vehicle exists); if not, create it
        get_url = f"{self.base_url}/api/resource/Vehicle/{imei}"
        r = requests.get(get_url, headers=self._headers(), timeout=8)
        if r.status_code == 200:
            # update
            patch_url = get_url
            payload = {"last_latitude": point.get("latitude"), "last_longitude": point.get("longitude"), "last_seen": point.get("timestamp")}
            resp = requests.put(patch_url, json=payload, headers=self._headers(), timeout=8)
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                logger.warning("Failed to update Vehicle: %s %s", resp.status_code, resp.text)
                return {"updated": False, "status": resp.status_code, "text": resp.text}
        else:
            # create a basic Vehicle doc with name = imei
            create_url = f"{self.base_url}/api/resource/Vehicle"
            doc = {"doctype":"Vehicle", "name": imei, "vehicle_name": imei, "last_latitude": point.get("latitude"), "last_longitude": point.get("longitude"), "last_seen": point.get("timestamp")}
            resp = requests.post(create_url, json=doc, headers=self._headers(), timeout=8)
            if resp.status_code in (200,201):
                return resp.json()
            else:
                logger.warning("Failed to create Vehicle: %s %s", resp.status_code, resp.text)
                return {"created": False, "status": resp.status_code, "text": resp.text}

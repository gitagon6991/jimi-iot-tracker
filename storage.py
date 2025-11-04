import json
import threading
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

class Storage:
    """
    Simple JSON-backed storage.
    Structure:
    {
      "latest": { "<imei>": <point> },
      "logs": { "<imei>": [point, ...] }
    }
    """
    def __init__(self, path="storage.json", max_points_per_device=1000):
        self.path = path
        self.lock = threading.Lock()
        self.max_points = max_points_per_device
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception:
            self.data = {"latest": {}, "logs": {}}

    def save_to_disk(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def save_point(self, point: dict):
        imei = point.get("imei")
        if not imei:
            return
        with self.lock:
            self.data["latest"][imei] = point
            logs = self.data["logs"].setdefault(imei, [])
            logs.insert(0, point)  # newest first
            if len(logs) > self.max_points:
                del logs[self.max_points:]
            self.save_to_disk()

    def get_latest_all(self):
        with self.lock:
            return self.data.get("latest", {}).copy()

    def get_log_for_imei(self, imei: str, limit: int = 100):
        with self.lock:
            logs = self.data.get("logs", {}).get(imei, [])
            return logs[:limit]

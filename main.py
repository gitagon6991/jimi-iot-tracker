import os
import logging
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
from datetime import datetime, timezone
import asyncio

from storage import Storage
# from cloud import ERPService
from erpnext_sync import ERPNextSync


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jimi-tracker")

# CONFIG from env (set these)
ERP_URL = os.getenv("ERP_URL", "")  # e.g. https://erp.yoursite.com
ERP_API_KEY = os.getenv("ERP_API_KEY", "")
ERP_API_SECRET = os.getenv("ERP_API_SECRET", "")
SAVE_PATH = os.getenv("SAVE_PATH", "storage.json")  # local storage file

app = FastAPI(title="JIMI IoT Car Tracker")
templates = Jinja2Templates(directory=".")
app.mount("/static", StaticFiles(directory="."), name="static")

storage = Storage(SAVE_PATH)
# erp = ERPService(ERP_URL, ERP_API_KEY, ERP_API_SECRET)
erp = ERPNextSync(ERP_URL, ERP_API_KEY, ERP_API_SECRET)


# Helper parse tolerant payloads
def parse_payload(payload: dict):
    # imei = payload.get("imei") or payload.get("deviceId") or payload.get("DeviceId") or payload.get("imei_code") or payload.get("id")
    imei = payload.get("imei") or payload.get("deviceId") or payload.get("DeviceId") or payload.get("device_id") or payload.get("imei_code") or payload.get("id")
    lat = payload.get("lat") or payload.get("latitude") or payload.get("Lat")
    lng = payload.get("lon") or payload.get("lng") or payload.get("longitude") or payload.get("Lon")
    speed = payload.get("speed") or payload.get("spd") or payload.get("velocity") or 0
    timestamp = payload.get("gpstime") or payload.get("time") or payload.get("timestamp") or payload.get("date")
    # normalize types
    try:
        lat = float(lat) if lat is not None else None
        lng = float(lng) if lng is not None else None
        speed = float(speed) if speed is not None else 0.0
    except Exception:
        lat, lng, speed = None, None, 0.0

    if isinstance(timestamp, (int, float)):
        ts_iso = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")

    else:
        try:
            # try parse ISO-ish
            ts_iso = datetime.fromisoformat(timestamp).isoformat()
        except Exception:
            # ts_iso = datetime.utcnow().isoformat() + "Z"
            ts_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


    return {
        "imei": str(imei) if imei is not None else None,
        "latitude": lat,
        "longitude": lng,
        "speed_kmh": speed,
        "timestamp": ts_iso,
        "raw": payload
    }

@app.post("/jimi/push")
async def jimi_push(request: Request):
    """
    Endpoint expected to be set as the JIMI cloud push URL.
    Accepts JSON or form-encoded payloads (tolerant).
    """
    # accept JSON or form data
    try:
        if request.headers.get("content-type", "").startswith("application/json"):
            payload = await request.json()
        else:
            form = await request.form()
            # convert to dict and try parse nested JSON strings
            payload = {k: v for k, v in form.items()}
            # If JIMI sends 'data' with JSON text, try to load it:
            import json
            if "data" in payload:
                try:
                    payload_data = json.loads(payload["data"])
                    if isinstance(payload_data, dict):
                        payload = payload_data
                except Exception:
                    pass
    except Exception as exc:
        logger.exception("failed to parse incoming request")
        raise HTTPException(status_code=400, detail="invalid payload")

    # some pushes use arrays / nested
    if isinstance(payload, list) and payload:
        payload = payload[0]
    if isinstance(payload, dict) and "data" in payload and isinstance(payload["data"], dict):
        payload = payload["data"]

    parsed = parse_payload(payload)
    if not parsed["imei"] or parsed["latitude"] is None or parsed["longitude"] is None:
        logger.warning("missing essential fields in payload: %s", payload)
        return JSONResponse({"error": "missing imei/lat/lng", "received": payload}, status_code=400)

    # persist locally
    storage.save_point(parsed)

    # attempt ERPNext upload asynchronously (fire-and-forget style)
    # run it in background so receiver returns quickly
    asyncio.create_task(push_to_erp(parsed))

    return JSONResponse({"status": "ok", "stored": True}, status_code=200)

async def push_to_erp(point: dict):
    try:
        erp.send_telemetry(
            imei=point["imei"],
            lat=point["latitude"],
            lon=point["longitude"],
            speed=point["speed_kmh"],
            ignition=point["raw"].get("ignition", False),
            timestamp=point["timestamp"]
        )
        logger.info("Sent to ERPNext for IMEI %s", point["imei"])
    except Exception as e:
        logger.exception("ERP push failed: %s", e)

# async def push_to_erp(point: dict):
    # try:
        # create GPS Log doc
        # res = erp.create_gps_log(point)
        # logger.info("ERP push response: %s", res)
        # update vehicle last location (if configured)
        # erp.upsert_vehicle_last_location(point)
    # except Exception as e:
        # logger.exception("ERP push failed: %s", e) 

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Simple dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/latest")
def latest():
    """Return latest data for all vehicles (dict keyed by imei)."""
    return storage.get_latest_all()

@app.get("/api/log/{imei}")
def log_for_imei(imei: str, limit: Optional[int] = 100):
    return storage.get_log_for_imei(imei, limit)

#update fast API (Jan 8th)
@app.get("/api/devices")
def api_devices():
    """
    Return a JSON of all devices with their last 5 points (trail) and ERP sync status.
    """
    devices = {}
    for imei, logs in storage.data.get("logs", {}).items():
        # Only last 5 points for trail
        trail_points = logs[:5][::-1]  # oldest first for map trails

        # Fill missing timestamp safely
        for p in trail_points:
            if "timestamp" not in p:
                p["timestamp"] = "unknown"

        devices[imei] = {
            "trail": [
                {
                    "lat": p.get("latitude"),
                    "lon": p.get("longitude"),
                    "speed": p.get("speed_kmh"),
                    "timestamp": p.get("timestamp")
                }
                for p in trail_points
            ],
            "latest": storage.data["latest"].get(imei, {}),
            "erp_synced": storage.data["latest"].get(imei, {}).get("erp_synced", False)
        }
    return devices

# simple manual test push from form (useful for browser testing)
@app.post("/test/push")
async def test_push(imei: str = Form(...), lat: float = Form(...), lon: float = Form(...), speed: float = Form(0)):
    data = {"imei": imei, "lat": lat, "lon": lon, "speed": speed, "time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    parsed = parse_payload(data)
    storage.save_point(parsed)
    asyncio.create_task(push_to_erp(parsed))
    return JSONResponse({"status": "ok", "parsed": parsed})

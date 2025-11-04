from erpnext_sync import ERPNextSync

sync = ERPNextSync(
    base_url="https://your-erpnext-instance.com",
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET"
)

sync.send_telemetry(
    imei="JIMI123",
    lat=-1.2921,
    lon=36.8219,
    speed=65,
    ignition=True
)

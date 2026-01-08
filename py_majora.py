#parse raw device payload
payload = {
    "deviceToken": "3345689",
    "deviceType": "iot",
    "latitude": 51.22,
    "longitude": -0.22,
    "speed": 80
}
#extract the values
imei = payload.get("deviceToken")
device = payload.get("deviceType")
lat = payload.get("latitude")
long = payload.get("longitude")
speed = payload.get("speed")

#convert types
lat = float(lat)
long = float(long)
speed = int(speed)

#build the clean dictionary
clean_data = {
    "imei": imei,
    "device": device,
    "lat": lat,
    "long": long,
    "speed": speed
}

#print data
print(clean_data)
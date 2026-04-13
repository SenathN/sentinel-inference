# =========================
# VARIABLES
# =========================
_DETECTION_THRESHOLD = 0.5
_MAX_INFERENCES = 10  # Not used in one-shot, but kept for reference

# =========================
# IMPORTS
# =========================
import time
import subprocess
import io
from PIL import Image
import numpy as np
import cv2
from ultralytics import YOLO  # Ultralytics YOLO (2023+)
# import gps  # For gpsd access
import os
import json
import pynmea2  # For parsing NMEA if needed (fallback)

# Create output directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "sentinel_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# LOAD MODEL
# =========================
model_path = os.path.join(SCRIPT_DIR, "best.pt")  # Relative to script directory
model = YOLO(model_path)
model.to('cpu')  # CPU for RPi4
print(f"[Model] Loaded {model_path} successfully")

# GPS Setup (from tutorial)
# session = gps.gps("localhost", "2947")  # Connect to gpsd
# session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

def get_gps_data():
    try:
        report = session.next()
        if report['class'] == 'TPV':
            lat = getattr(report, 'lat', None)
            lon = getattr(report, 'lon', None)
            utc_time = getattr(report, 'time', time.strftime("%Y-%m-%dT%H:%M:%SZ"))
            if lat and lon:
                return lat, lon, utc_time
    except Exception as e:
        print(f"[GPS] Error: {e}")
    # Fallback: Parse raw NMEA if gpsd fails
    try:
        with open('/dev/serial0', 'r') as serial_port:
            line = serial_port.readline()
            if line.startswith('$GPGGA'):
                msg = pynmea2.parse(line)
                return msg.latitude, msg.longitude, msg.timestamp
    except:
        pass
    return None, None, time.strftime("%Y-%m-%dT%H:%M:%SZ")  # Default to current time if no GPS

# Camera command for single frame capture (modified for one-shot)
cmd = [
    "rpicam-still",  # Use still for single image instead of vid
    "--encoding", "jpg",
    "-o", "-"  # Output to stdout
]

# Capture single frame
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
jpeg_data = proc.stdout.read()
image = Image.open(io.BytesIO(jpeg_data)).convert("RGB")
frame_rgb = np.array(image)
frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

# Run YOLO inference
results = model(image, conf=_DETECTION_THRESHOLD, verbose=False)[0]

# Get detections
boxes = results.boxes.xyxy.cpu().numpy()
confs = results.boxes.conf.cpu().numpy()
clss = results.boxes.cls.cpu().numpy().astype(int)
names = results.names

# Draw detections and count passengers
count = 0
for box, conf, cls_id in zip(boxes, confs, clss):
    if conf < _DETECTION_THRESHOLD:
        continue
    count += 1
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
    label = f"{names[cls_id]} {conf:.2f}"
    cv2.putText(frame_bgr, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# Overlay passenger count
cv2.putText(frame_bgr, f"Passengers: {count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)

# Get GPS and timestamp
# lat, lon, gps_time = get_gps_data()
timestamp = time.strftime("%Y%m%d_%H%M%S")
filename = f"sentinel_{timestamp}.jpg"
filepath = os.path.join(OUTPUT_DIR, filename)

# Save image
cv2.imwrite(filepath, frame_bgr)
print(f"[Save] Image saved: {filepath} | Passengers: {count}")

# Save JSON log
log_data = {
#     "timestamp": gps_time,
    "passenger_count": count,
#     "latitude": lat,
#     "longitude": lon,
    "image_file": filename
}
log_path = os.path.join(OUTPUT_DIR, f"sentinel_{timestamp}.json")
with open(log_path, 'w') as f:
    json.dump(log_data, f)
print(f"[Log] JSON saved: {log_path}")

print("\n== Sentinel One-Shot Inference Complete ==\n")

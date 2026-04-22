# =========================
# VARIABLES
# =========================
_DETECTION_THRESHOLD = 0.5
_MAX_INFERENCES = 10  # Not used in one-shot, but kept for reference
_USE_MOCK_DATA = True  # Generates a mock gps data of a moving entity intead of the current location

# =========================
# IMPORTS
# =========================
import time
import subprocess
import io
import sys
from PIL import Image
import numpy as np
import cv2
from ultralytics import YOLO  # Ultralytics YOLO (2023+)
import os
import json
import uuid
import datetime
import platform

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utilities.time_utility import get_ist_time
from utilities.gps_utility import get_gps_data

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

# Get device unique ID
device_id = platform.node() or 'unknown_device'

# Get timestamp in +0530 timezone using utility
ist_time = get_ist_time()
timestamp = ist_time.strftime("%Y%m%d-%H%M%S")
date_folder = ist_time.strftime("%Y-%m-%d")  # Format: 2025-04-13
hour_folder = ist_time.strftime("%H")  # Format: 14

# Create unique identifier for image-JSON pair (simplified for archiver)
unique_id = f"sentinel_{timestamp}_{str(uuid.uuid4())[:8]}"

# Get timestamp first
gps_time = ist_time.strftime("%Y-%m-%dT%H:%M:%S+05:30")

# Get GPS coordinates
if _USE_MOCK_DATA:
    from linear_coords_map import get_coordinate_by_timestamp
    lat, lon = get_coordinate_by_timestamp(gps_time)
else:
    lat, lon, gps_utc = get_gps_data()

if lat is None or lon is None:
    print("[GPS] No fix available, using time-based coordinate mapping as fallback")
    try:
        from linear_coords_map import get_coordinate_by_timestamp
        lat, lon = get_coordinate_by_timestamp(gps_time)
    except Exception as e:
        print(f"[Coords] Error using time-based mapping: {e}")
        lat = 28.6139  # New Delhi sample latitude
        lon = 77.2090  # New Delhi sample longitude

# Create date and hour subdirectories
date_output_dir = os.path.join(OUTPUT_DIR, date_folder)
hourly_output_dir = os.path.join(date_output_dir, hour_folder)
os.makedirs(hourly_output_dir, exist_ok=True)

filename = f"{unique_id}.jpg"
filepath = os.path.join(hourly_output_dir, filename)

# Save image
cv2.imwrite(filepath, frame_bgr)
print(f"[Save] Image saved: {filepath} | Passengers: {count}")

# Save JSON log
log_data = {
    "unique_id": unique_id,
    "timestamp": gps_time,
    "passenger_count": count,
    "latitude": lat,
    "longitude": lon,
    "image_file": filename,
    "device_id": device_id,
    "timezone": "+05:30"
}
log_path = os.path.join(hourly_output_dir, f"{unique_id}.json")
with open(log_path, 'w') as f:
    json.dump(log_data, f)
print(f"[Log] JSON saved: {log_path}")

print("\n== Sentinel One-Shot Inference Complete ==\n")

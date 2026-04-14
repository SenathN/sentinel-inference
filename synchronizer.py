#!/usr/bin/env python3
import os
import json
import requests
import logging
from datetime import datetime
import base64
import hashlib
import datetime as dt

# Set up logging to synchronizer_logs directory
utc_now = dt.datetime.utcnow()
ist_now = utc_now + dt.timedelta(hours=5, minutes=30)
sync_log_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synchronizer_logs", 
                               str(ist_now.year), 
                               f"{ist_now.month:02d}", 
                               f"{ist_now.day:02d}",
                               f"{ist_now.hour:02d}")
os.makedirs(sync_log_dir_path, exist_ok=True)

# Generate synchronizer log filename with timestamp
sync_log_filename = f"{ist_now.strftime('%Y-%m-%d-%H')}-synchronizer.log"
sync_log_file_path = os.path.join(sync_log_dir_path, sync_log_filename)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s +0530 - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(sync_log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Synchronizer log file created: {sync_log_file_path}")

def _get_status_description(status_code):
    """Get human-readable description for HTTP status codes"""
    status_descriptions = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        408: "Request Timeout",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout"
    }
    return status_descriptions.get(status_code, "Unknown Status")

# Configuration
BACKEND_URL = "http://192.168.1.124:8000/api/observer/data-sync"  # Backend URL
API_KEY = "your-api-key-here"  # Update with your API key
SENTINEL_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inference_script", "sentinel_data")

# Generate backend response JSON filename with timestamp
backend_json_filename = f"{ist_now.strftime('%Y-%m-%d-%H%M%S')}-backend_response.json"
backend_json_file_path = os.path.join(sync_log_dir_path, backend_json_filename)

def encode_image_to_base64(image_path):
    """Encode image file to base64 string"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image {image_path}: {e}")
        return None

def calculate_file_hash(file_path):
    """Calculate SHA256 hash of a file"""
    try:
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return None

def collect_latest_data():
    """Collect the latest 5 JSON files and their corresponding images"""
    try:
        # Get all date folders and sort them
        date_folders = []
        for item in os.listdir(SENTINEL_DATA_DIR):
            folder_path = os.path.join(SENTINEL_DATA_DIR, item)
            if os.path.isdir(folder_path):
                date_folders.append(folder_path)
        
        if not date_folders:
            logger.warning("No date folders found")
            return []
        
        # Sort date folders by name (newest first)
        date_folders.sort(reverse=True)
        logger.info(f"Found {len(date_folders)} date folders: {[os.path.basename(f) for f in date_folders]}")
        
        # Collect hourly folders from all date folders
        hourly_folders = []
        for date_folder in date_folders:
            for item in os.listdir(date_folder):
                hour_folder_path = os.path.join(date_folder, item)
                if os.path.isdir(hour_folder_path):
                    hourly_folders.append(hour_folder_path)
        
        # Sort hourly folders by full path (newest first)
        hourly_folders.sort(reverse=True)
        logger.info(f"Found {len(hourly_folders)} hourly folders total")
        
        collected_data = []
        
        # Collect up to 5 most recent JSON files from the latest folder first
        logger.info(f"Collecting up to 5 items from most recent folders")
        
        for folder in hourly_folders:  # Process folders in order (newest first)
            if len(collected_data) >= 5:
                break  # Stop when we have 5 items
                
            json_files = [f for f in os.listdir(folder) if f.endswith('.json')]
            json_files.sort(reverse=True)  # Get latest first
            logger.info(f"Folder {os.path.basename(os.path.dirname(folder))}/{os.path.basename(folder)}: found {len(json_files)} JSON files")
            
            # Take as many as needed from this folder
            needed = 5 - len(collected_data)
            for json_file in json_files[:needed]:  # Take only what we need
                json_path = os.path.join(folder, json_file)
                
                try:
                    # Read JSON data
                    with open(json_path, 'r') as f:
                        json_data = json.load(f)
                    
                    # Find corresponding image
                    image_file = json_data.get('image_file', '')
                    if image_file:
                        image_path = os.path.join(folder, image_file)
                        
                        if os.path.exists(image_path):
                            # Encode image to base64
                            image_base64 = encode_image_to_base64(image_path)
                            image_hash = calculate_file_hash(image_path)
                            
                            if image_base64:
                                # Prepare data for transmission
                                transmission_data = {
                                    'timestamp': datetime.now().isoformat(),
                                    'detection_data': json_data,
                                    'image_data': {
                                        'filename': image_file,
                                        'base64_data': image_base64,
                                        'hash': image_hash,
                                        'size_bytes': os.path.getsize(image_path)
                                    },
                                    'source_folder': f"{os.path.basename(os.path.dirname(folder))}/{os.path.basename(folder)}",
                                    'checksum': hashlib.sha256(
                                        (json.dumps(json_data) + image_hash).encode()
                                    ).hexdigest()
                                }
                                collected_data.append(transmission_data)
                                logger.info(f"Collected data from {json_file} (total: {len(collected_data)}/5)")
                            else:
                                logger.error(f"Failed to encode image {image_file}")
                        else:
                            logger.error(f"Image file not found: {image_path}")
                    else:
                        logger.error(f"No image file specified in {json_file}")
                        
                except Exception as e:
                    logger.error(f"Error processing {json_file}: {e}")
                    continue
        
        logger.info(f"Collection complete: {len(collected_data)} items ready for upload")
        return collected_data
        
    except Exception as e:
        logger.error(f"Error collecting data: {e}")
        return []

def send_to_backend(data_batch):
    """Send collected data to backend via secure POST request"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}',
            'X-API-Key': API_KEY
        }
        
        # Prepare the payload
        payload = {
            'batch_id': hashlib.sha256(
                datetime.now().isoformat().encode()
            ).hexdigest()[:16],
            'sentinel_version': '1.0',
            'data_count': len(data_batch),
            'data': data_batch
        }
        
        # Log detailed request information
        logger.info(f"=== SYNCHRONIZATION REQUEST ===")
        logger.info(f"Backend URL: {BACKEND_URL}")
        logger.info(f"Batch ID: {payload['batch_id']}")
        logger.info(f"Records to send: {len(data_batch)}")
        logger.info(f"Total payload size: {len(json.dumps(payload))} bytes")
        
        # Log individual record details
        for i, record in enumerate(data_batch):
            logger.info(f"Record {i+1}: {record.get('source_folder', 'unknown')} - {record.get('detection_data', {}).get('image_file', 'unknown')}")
        
        # Network diagnostics before sending
        logger.info("=== NETWORK DIAGNOSTICS ===")
        import socket
        from urllib.parse import urlparse
        
        parsed_url = urlparse(BACKEND_URL)
        host = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        logger.info(f"Target Host: {host}")
        logger.info(f"Target Port: {port}")
        logger.info(f"Protocol: {parsed_url.scheme}")
        
        # Test basic connectivity
        try:
            logger.info("Testing basic TCP connectivity...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                logger.info(f"✓ TCP connection to {host}:{port} successful")
            else:
                logger.error(f"✗ TCP connection to {host}:{port} failed (error code: {result})")
                return False
        except Exception as e:
            logger.error(f"✗ Network connectivity test failed: {e}")
            return False
        
        # Send POST request with timeout
        logger.info("Sending POST request to backend...")
        logger.info(f"Request Headers: {headers}")
        logger.info(f"Request URL: {BACKEND_URL}")
        
        response = requests.post(
            BACKEND_URL,
            json=payload,
            headers=headers,
            timeout=30,
            verify=False  # Disable SSL verification for HTTP
        )
        
        # Log detailed response information
        logger.info(f"=== BACKEND RESPONSE ===")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Size: {len(response.content)} bytes")
        
        # Print status code for repeater to capture
        print(f"Status Code: {response.status_code} ({_get_status_description(response.status_code)})")
        
        # Save backend response to JSON file in readable format
        response_data = {
            "timestamp": ist_now.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "status_code": response.status_code,
            "status_description": _get_status_description(response.status_code),
            "headers": dict(response.headers),
            "response_body": response.text,
            "request_url": BACKEND_URL,
            "data_count": len(data_batch),
            "success": response.status_code == 200
        }
        
        try:
            with open(backend_json_file_path, 'w') as f:
                json.dump(response_data, f, indent=2, sort_keys=True)
            logger.info(f"Backend response saved to: {backend_json_file_path}")
            
            # Log readable summary to .log file
            logger.info("=== BACKEND RESPONSE SUMMARY ===")
            logger.info(f"Status: {response.status_code} {_get_status_description(response.status_code)}")
            logger.info(f"Timestamp: {response_data['timestamp']}")
            logger.info(f"Data Count: {len(data_batch)}")
            logger.info(f"Response Body: {response.text}")
            logger.info("=== END BACKEND RESPONSE ===")
            
        except Exception as e:
            logger.error(f"Failed to save backend response: {e}")
        
        if response.status_code == 200:
            logger.info(f"SUCCESS: Data successfully sent to backend")
            logger.info(f"Response Body: {response.text}")
            return True
        else:
            logger.error(f"FAILURE: Backend returned non-200 status")
            logger.error(f"Status Code: {response.status_code} ({_get_status_description(response.status_code)})")
            logger.error(f"Response Body: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("Request to backend timed out")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to backend")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending to backend: {e}")
        return False


def main():
    """Main synchronizer function"""
    logger.info("Starting synchronizer...")
    
    # Collect latest data
    collected_data = collect_latest_data()
    
    if not collected_data:
        logger.warning("No data to synchronize")
        print("Status Code: NO_DATA")
        return False
    
    logger.info(f"Collected {len(collected_data)} records")
    
    # Send to backend (single API call)
    success = send_to_backend(collected_data)
    
    if success:
        logger.info("Synchronization completed successfully")
        print("Status Code: 200 (OK)")
        return True
    else:
        logger.error("Synchronization failed")
        print("Status Code: SYNC_FAILED")
        return False

if __name__ == "__main__":
    main()

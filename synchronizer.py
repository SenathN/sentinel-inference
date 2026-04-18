#!/usr/bin/env python3

# Standard library imports
import os
import json
import logging
import hashlib
import subprocess
import sys
from datetime import datetime

# Third-party imports
import requests

# Local imports
from utilities.time_utility import setup_logging, get_status_description

# Configuration constants
BACKEND_URL = "http://192.168.1.124:8000/api/observer/data-sync"
API_KEY = "your-api-key-here"
SENTINEL_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inference_script", "sentinel_data")
SYNC_COUNT = 15
REQUEST_TIMEOUT = 120
CHUNK_SIZE = 4096
HASH_ALGORITHM = 'sha256'
LOG_DIR_NAME = "synchronizer_logs"
SENTINEL_VERSION = "1.0"
BATCH_ID_LENGTH = 16

# Initialize logging
logger, sync_log_dir_path, ist_now = setup_logging(
    base_dir=os.path.dirname(os.path.abspath(__file__)),
    log_dir_name=LOG_DIR_NAME,
    log_filename_prefix="synchronizer"
)

logger.info(f"Configuration: BACKEND_URL={BACKEND_URL}, SYNC_COUNT={SYNC_COUNT}, REQUEST_TIMEOUT={REQUEST_TIMEOUT}")


# Generate backend response JSON filename with timestamp
backend_json_filename = f"{ist_now.strftime('%Y-%m-%d-%H%M%S')}-backend_response.json"
backend_json_file_path = os.path.join(sync_log_dir_path, backend_json_filename)


def calculate_file_hash(file_path):
    """Calculate hash of a file using configured algorithm"""
    try:
        logger.debug(f"Calculating {HASH_ALGORITHM} hash for file: {file_path}")
        hash_func = getattr(hashlib, HASH_ALGORITHM)()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                hash_func.update(chunk)
        
        file_hash = hash_func.hexdigest()
        logger.debug(f"Hash calculated successfully: {file_hash}")
        return file_hash
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return None


def collect_latest_data():
    """Collect the latest JSON files and their corresponding images"""
    logger.info(f"Starting data collection from {SENTINEL_DATA_DIR}")
    
    try:
        # Validate data directory exists
        if not os.path.exists(SENTINEL_DATA_DIR):
            logger.error(f"Sentinel data directory does not exist: {SENTINEL_DATA_DIR}")
            return []
        
        # Get all date folders and sort them
        date_folders = []
        for item in os.listdir(SENTINEL_DATA_DIR):
            folder_path = os.path.join(SENTINEL_DATA_DIR, item)
            if os.path.isdir(folder_path):
                date_folders.append(folder_path)
                logger.debug(f"Found date folder: {item}")
        
        if not date_folders:
            logger.warning("No date folders found in sentinel data directory")
            return []
        
        # Sort date folders by name (newest first)
        date_folders.sort(reverse=True)
        logger.info(f"Found {len(date_folders)} date folders: {[os.path.basename(f) for f in date_folders]}")
        
        # Collect hourly folders from all date folders
        hourly_folders = []
        for date_folder in date_folders:
            try:
                for item in os.listdir(date_folder):
                    hour_folder_path = os.path.join(date_folder, item)
                    if os.path.isdir(hour_folder_path):
                        hourly_folders.append(hour_folder_path)
                        logger.debug(f"Found hourly folder: {os.path.basename(date_folder)}/{item}")
            except Exception as e:
                logger.warning(f"Error accessing date folder {date_folder}: {e}")
                continue
        
        if not hourly_folders:
            logger.warning("No hourly folders found")
            return []
        
        # Sort hourly folders by full path (newest first)
        hourly_folders.sort(reverse=True)
        logger.info(f"Found {len(hourly_folders)} hourly folders total")
        
        collected_data = []
        processed_files = 0
        skipped_files = 0
        
        # Collect up to SYNC_COUNT most recent JSON files from the latest folder first
        logger.info(f"Collecting up to {SYNC_COUNT} items from most recent folders")
        
        for folder in hourly_folders:  # Process folders in order (newest first)
            if len(collected_data) >= SYNC_COUNT:
                logger.info(f"Reached target collection count: {SYNC_COUNT}")
                break
                
            try:
                json_files = [f for f in os.listdir(folder) if f.endswith('.json')]
                json_files.sort(reverse=True)  # Get latest first
                logger.info(f"Folder {os.path.basename(os.path.dirname(folder))}/{os.path.basename(folder)}: found {len(json_files)} JSON files")
                
                # Take as many as needed from this folder
                needed = SYNC_COUNT - len(collected_data)
                logger.debug(f"Need {needed} more items from this folder")
                
                for json_file in json_files[:needed]:  # Take only what we need
                    json_path = os.path.join(folder, json_file)
                    processed_files += 1
                    
                    try:
                        logger.debug(f"Processing JSON file: {json_file}")
                        
                        # Read JSON data
                        with open(json_path, 'r') as f:
                            json_data = json.load(f)
                        
                        # Validate JSON structure
                        if not isinstance(json_data, dict):
                            logger.warning(f"Invalid JSON structure in {json_file}: not a dictionary")
                            skipped_files += 1
                            continue
                        
                        # Find corresponding image
                        image_file = json_data.get('image_file', '')
                        if not image_file:
                            logger.warning(f"No image file specified in {json_file}")
                            skipped_files += 1
                            continue
                        
                        image_path = os.path.join(folder, image_file)
                        
                        if not os.path.exists(image_path):
                            logger.error(f"Image file not found: {image_path}")
                            skipped_files += 1
                            continue
                        
                        # Calculate image hash and get file info
                        logger.debug(f"Calculating hash for image: {image_file}")
                        image_hash = calculate_file_hash(image_path)
                        
                        if not image_hash:
                            logger.error(f"Failed to calculate hash for {image_file}")
                            skipped_files += 1
                            continue
                        
                        # Prepare data for transmission (image will be sent as file)
                        transmission_data = {
                            'timestamp': datetime.now().isoformat(),
                            'detection_data': json_data,
                            'image_data': {
                                'filename': image_file,
                                'hash': image_hash,
                                'size_bytes': os.path.getsize(image_path)
                            },
                            'source_folder': f"{os.path.basename(os.path.dirname(folder))}/{os.path.basename(folder)}",
                            'checksum': hashlib.sha256(
                                (json.dumps(json_data, sort_keys=True) + image_hash).encode()
                                ).hexdigest()
                        }
                        
                        collected_data.append(transmission_data)
                        logger.info(f"Successfully collected data from {json_file} (total: {len(collected_data)}/{SYNC_COUNT})")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in {json_file}: {e}")
                        skipped_files += 1
                    except Exception as e:
                        logger.error(f"Error processing {json_file}: {e}")
                        skipped_files += 1
                        continue
                        
            except Exception as e:
                logger.error(f"Error processing folder {folder}: {e}")
                continue
        
        logger.info(f"Collection complete: {len(collected_data)} items ready for upload, {processed_files} files processed, {skipped_files} files skipped")
        return collected_data
        
    except Exception as e:
        logger.error(f"Critical error during data collection: {e}")
        return []

def send_to_backend(data_batch):
    """Send collected data to backend via multipart form data"""
    logger.info(f"Preparing to send {len(data_batch)} records to backend")
    
    try:
        # Validate input
        if not data_batch:
            logger.error("No data to send")
            return False, "No data provided"
        
        # Generate batch ID
        batch_id = hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:BATCH_ID_LENGTH]
        logger.info(f"Generated batch ID: {batch_id}")
        
        # Prepare form data
        fields = {
            'batch_id': batch_id,
            'sentinel_version': SENTINEL_VERSION,
            'data_count': str(len(data_batch)),
            'sync_timestamp': datetime.now().isoformat()
        }
        
        # Prepare files
        files = []
        prepared_files = 0
        failed_files = 0
        
        for i, record in enumerate(data_batch):
            try:
                logger.debug(f"Preparing record {i+1}/{len(data_batch)}")
                
                # Validate record structure
                required_keys = ['timestamp', 'detection_data', 'image_data', 'source_folder', 'checksum']
                if not all(key in record for key in required_keys):
                    logger.error(f"Record {i+1} missing required keys")
                    failed_files += 1
                    continue
                
                # Add JSON metadata
                json_data = {
                    'timestamp': record['timestamp'],
                    'detection_data': record['detection_data'],
                    'image_info': {
                        'filename': record['image_data']['filename'],
                        'hash': record['image_data']['hash'],
                        'size_bytes': record['image_data']['size_bytes']
                    },
                    'source_folder': record['source_folder'],
                    'checksum': record['checksum']
                }
                fields[f'data_{i}'] = json.dumps(json_data, sort_keys=True)
                
                # Add image file
                image_path = os.path.join(
                    SENTINEL_DATA_DIR, 
                    record['source_folder'].replace('/', os.sep), 
                    record['image_data']['filename']
                )
                
                if os.path.exists(image_path):
                    file_size = os.path.getsize(image_path)
                    logger.debug(f"Adding image file: {record['image_data']['filename']}, size: {file_size} bytes")
                    
                    # Try using indexed field name to match data_{i} pattern
                    files.append((
                        f'image_{i}',  # Field name matching data_{i}
                        (record['image_data']['filename'], open(image_path, 'rb'), 'image/jpeg')
                    ))
                    prepared_files += 1
                else:
                    logger.error(f"Image file not found for record {i+1}: {image_path}")
                    failed_files += 1
                    
            except Exception as e:
                logger.error(f"Error preparing record {i+1}: {e}")
                failed_files += 1
                continue
        
        if failed_files > 0:
            logger.warning(f"Failed to prepare {failed_files} records")
        
        if not files:
            logger.error("No valid files to send")
            return False, "No valid files to upload"
        
        # Headers
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'X-API-Key': API_KEY,
            'User-Agent': f'Sentinel-Synchronizer/{SENTINEL_VERSION}'
        }
        
        logger.info(f"Sending {len(data_batch)} records with {len(files)} images to {BACKEND_URL}")
        logger.debug(f"Request headers: {headers}")
        logger.debug(f"Form data fields: {list(fields.keys())}")
        logger.debug(f"Files being uploaded: {[f[0] for f in files]}")
        
        # Send request
        try:
            response = requests.post(
                BACKEND_URL,
                files=files,
                data=fields,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {REQUEST_TIMEOUT} seconds")
            return False, "Request timeout"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return False, "Connection error"
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            return False, "Request failed"
        
        # Close files
        for file_tuple in files:
            try:
                if len(file_tuple) == 3:
                    # Format: (field_name, (filename, file_obj, content_type))
                    file_obj = file_tuple[1][1]
                else:
                    # Format: (field_name, file_obj)
                    file_obj = file_tuple[1]
                if hasattr(file_obj, 'close'):
                    file_obj.close()
            except Exception as e:
                logger.warning(f"Error closing file: {e}")
        
        # Log response details
        logger.info(f"Status: {response.status_code} ({get_status_description(response.status_code)})")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # Save response to file for debugging
        try:
            response_data = {
                'batch_id': batch_id,
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'status_description': get_status_description(response.status_code),
                'response_text': response.text,
                'headers': dict(response.headers),
                'records_sent': len(data_batch),
                'files_uploaded': len(files)
            }
            
            with open(backend_json_file_path, 'w') as f:
                json.dump(response_data, f, indent=2)
            
            logger.info(f"Response saved to: {backend_json_file_path}")
        except Exception as e:
            logger.warning(f"Failed to save response to file: {e}")
        
        # Log response content (truncated if too long)
        response_text = response.text
        if len(response_text) > 1000:
            logger.info(f"Response content (truncated): {response_text[:1000]}...")
        else:
            logger.info(f"Response content: {response_text}")
        
        return response.status_code == 200, response.text
        
    except Exception as e:
        logger.error(f"Critical error during backend transmission: {e}")
        return False, str(e)


def main():
    """Main synchronizer function"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"Starting synchronizer at {start_time.isoformat()}")
    logger.info(f"Target: {BACKEND_URL}")
    logger.info(f"Data directory: {SENTINEL_DATA_DIR}")
    logger.info("=" * 80)
    
    try:
        # Collect data
        logger.info("Phase 1: Data collection")
        collected_data = collect_latest_data()
        
        if not collected_data:
            logger.warning("No data to synchronize")
            logger.info("Synchronization completed: NO_DATA")
            print("Status Code: NO_DATA")
            return False
        
        logger.info(f"Phase 1 complete: Collected {len(collected_data)} records")
        
        # Send to backend
        logger.info("Phase 2: Backend transmission")
        success, response = send_to_backend(collected_data)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if success:
            logger.info(f"Phase 2 complete: Transmission successful")
            logger.info(f"Synchronization completed successfully in {duration:.2f} seconds")
            logger.info("=" * 80)
            print("Status Code: 200 (OK)")
            return True
        else:
            logger.error(f"Phase 2 failed: Transmission unsuccessful")
            logger.error(f"Synchronization failed after {duration:.2f} seconds")
            logger.error(f"Backend response: {response}")
            logger.info("=" * 80)
            print("Status Code: SYNC_FAILED")
            return False
            
    except KeyboardInterrupt:
        logger.warning("Synchronization interrupted by user")
        print("Status Code: INTERRUPTED")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        print("Status Code: ERROR")
        return False

if __name__ == "__main__":
    main()

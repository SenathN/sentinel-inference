#!/usr/bin/env python3
import os
import json
import shutil
import logging
import sys
import requests
import datetime as dt

# Create hierarchical log directory structure based on +0530 timezone (similar to repeater)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
utc_now = dt.datetime.utcnow()
ist_now = utc_now + dt.timedelta(hours=5, minutes=30)
log_dir_path = os.path.join(CURRENT_DIR, "archiver_logs", 
                           str(ist_now.year), 
                           f"{ist_now.month:02d}", 
                           f"{ist_now.day:02d}")
os.makedirs(log_dir_path, exist_ok=True)

# Generate hourly log filename (for complete hour)
log_filename = f"{ist_now.strftime('%Y-%m-%d-%H')}-archiver_log.log"
log_file_path = os.path.join(log_dir_path, log_filename)

# Set up proper logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s +0530 - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),  # hierarchical file log
        logging.StreamHandler()              # also show in journalctl
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Log file created: {log_file_path}")

# Configuration
SENTINEL_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inference_script", "sentinel_data")
INFERENCE_ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inference_script", "inference_archive")
BACKEND_URL = "http://192.168.1.124:8000/api/observer/sync-check"
API_KEY = "your-api-key-here"

def get_unarchived_unique_ids():
    """Scan local sentinel_data directory for unarchived unique_ids and sync with backend"""
    try:
        # Scan local sentinel_data directory for all unique IDs
        logger.info("=== SCANNING LOCAL SENTINEL_DATA ===")
        logger.info(f"Scanning directory: {SENTINEL_DATA_DIR}")
        
        all_unique_ids = []
        
        # Walk through all date/hour folders
        for root, dirs, files in os.walk(SENTINEL_DATA_DIR):
            # Find JSON files and extract unique IDs
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            json_data = json.load(f)
                        unique_id = json_data.get('unique_id', '')
                        if unique_id and unique_id.startswith('sentinel_'):
                            all_unique_ids.append(unique_id)
                    except Exception as e:
                        logger.warning(f"Error reading {file_path}: {e}")
        
        logger.info(f"Found {len(all_unique_ids)} total unique IDs in local directory")
        logger.info(f"Local unique IDs: {all_unique_ids}")
        
        # Take first 50 IDs
        unique_ids_to_check = all_unique_ids[:50]
        logger.info(f"Checking first {len(unique_ids_to_check)} IDs with backend")
        
        # POST to sync-check endpoint
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}',
            'X-API-Key': API_KEY
        }
        
        logger.info("=== POSTING TO SYNC-CHECK ===")
        payload = {
            "unique_ids": unique_ids_to_check
        }
        
        sync_response = requests.post(BACKEND_URL, json=payload, headers=headers, timeout=30)
        
        logger.info(f"=== SYNC-CHECK RESPONSE ===")
        logger.info(f"Status Code: {sync_response.status_code}")
        
        if sync_response.status_code != 200:
            logger.error(f"Failed to sync-check: {sync_response.status_code}")
            return []
        
        sync_data = sync_response.json()
        logger.info(f"Sync Response Data: {json.dumps(sync_data, indent=2)}")
        
        # Extract synchronized_unique_ids from response
        synchronized_ids = sync_data.get('synchronized_unique_ids', [])
        logger.info(f"=== SYNCHRONIZED IDS FOR ARCHIVAL ===")
        logger.info(f"Synchronized IDs: {synchronized_ids}")
        logger.info(f"Total items to archive: {len(synchronized_ids)}")
        logger.info("=== END SYNCHRONIZED IDS ===")
        
        return synchronized_ids
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in sync-check process: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

def archive_files(unique_ids):
    """Archive files based on unique_ids list"""
    try:
        logger.info(f"Starting archive process for {len(unique_ids)} items")
        
        archived_count = 0
        failed_count = 0
        
        for unique_id in unique_ids:
            try:
                # Extract timestamp from unique_id
                # Format: sentinel_YYYYMMDD-HHMMSS_hash
                if '_' not in unique_id:
                    logger.warning(f"Invalid unique_id format: {unique_id}")
                    failed_count += 1
                    continue
                    
                timestamp_part = unique_id.split('_')[1]  # Get "YYYYMMDD-HHMMSS"
                if '-' not in timestamp_part:
                    logger.warning(f"Invalid timestamp format: {timestamp_part}")
                    failed_count += 1
                    continue
                    
                date_part = timestamp_part.split('-')[0]     # Get "YYYYMMDD"
                time_part = timestamp_part.split('-')[1]     # Get "HHMMSS"
                
                # Parse the date and time
                year = date_part[:4]
                month = date_part[4:6]
                day = date_part[6:8]
                hour = time_part[:2]
                
                # Construct source folder path (handle both YYYY/MM/DD/HH and YYYY-MM-DD/HH formats)
                # Try YYYY/MM/DD/HH format first
                source_folder_path = os.path.join(SENTINEL_DATA_DIR, year, month, day, hour)
                
                if not os.path.exists(source_folder_path):
                    # Try YYYY-MM-DD/HH format
                    date_folder_name = f"{year}-{month}-{day}"
                    source_folder_path = os.path.join(SENTINEL_DATA_DIR, date_folder_name, hour)
                
                if not os.path.exists(source_folder_path):
                    logger.warning(f"Source folder not found: {source_folder_path}")
                    failed_count += 1
                    continue
                
                # Construct destination folder path (preserve original YYYY-MM-DD/HH format)
                date_folder_name = f"{year}-{month}-{day}"
                dest_folder_path = os.path.join(INFERENCE_ARCHIVE_DIR, date_folder_name, hour)
                os.makedirs(dest_folder_path, exist_ok=True)
                
                # Find specific files that match unique_id
                source_items = os.listdir(source_folder_path)
                matching_files = [item for item in source_items if unique_id in item]
                
                if not matching_files:
                    logger.warning(f"No matching files found for {unique_id} in {source_folder_path}")
                    failed_count += 1
                    continue
                
                # Move each matching file (should be .jpg and .json pair)
                for file_name in matching_files:
                    source_path = os.path.join(source_folder_path, file_name)
                    dest_path = os.path.join(dest_folder_path, file_name)
                    
                    if os.path.exists(dest_path):
                        logger.warning(f"Destination already exists, removing: {dest_path}")
                        os.remove(dest_path)
                    
                    logger.info(f"Moving {source_path} -> {dest_path}")
                    shutil.move(source_path, dest_path)
                    archived_count += 1
                
            except Exception as e:
                logger.error(f"Error archiving {unique_id}: {e}")
                failed_count += 1
        
        logger.info(f"Archive process completed: {archived_count} successful, {failed_count} failed")
        return archived_count, failed_count
        
    except Exception as e:
        logger.error(f"Critical error in archive process: {e}")
        return 0, len(unique_ids)

# def confirm_archival_to_backend(archived_ids, failed_ids):
#     """Confirm to backend which IDs were archived"""
#     try:
#         headers = {
#             'Content-Type': 'application/json',
#             'Authorization': f'Bearer {API_KEY}',
#             'X-API-Key': API_KEY
#         }
        
#         payload = {
#             'archived_ids': archived_ids,
#             'failed_ids': failed_ids,
#             'timestamp': dt.datetime.now().isoformat()
#         }
        
#         logger.info("=== CONFIRMING ARCHIVAL TO BACKEND ===")
#         logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
#         response = requests.post(
#             "http://192.168.1.124:8000/api/observer/confirm-archival",
#             json=payload,
#             headers=headers,
#             timeout=30
#         )
        
#         logger.info(f"Confirmation Response Status: {response.status_code}")
#         if response.status_code == 200:
#             logger.info("Archival confirmation sent successfully")
#         else:
#             logger.error(f"Failed to confirm archival: {response.status_code}")
            
#     except Exception as e:
#         logger.error(f"Error confirming archival: {e}")

def main():
    """Main archiver function"""
    logger.info("Starting archiver...")
    
    # Get synchronized unique_ids from backend
    synchronized_ids = get_unarchived_unique_ids()
    
    if not synchronized_ids:
        logger.info("No synchronized items found")
        return True
    
    # Archive the files
    archived_count, failed_count = archive_files(synchronized_ids)
    
    # Prepare confirmation lists
    archived_ids = synchronized_ids[:archived_count]  # Successfully archived
    failed_ids = synchronized_ids[archived_count:]  # Failed to archive
    
    # Confirm to backend
    # confirm_archival_to_backend(archived_ids, failed_ids)
    
    if failed_count == 0:
        logger.info("Archiver completed successfully")
        return True
    else:
        logger.warning(f"Archiver completed with {failed_count} failures")
        return False

if __name__ == "__main__":
    main()

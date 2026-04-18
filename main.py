#!/usr/bin/env python3

"""
Main Sentinel System Controller
Coordinates inference, synchronization, archiving, and cleaning operations
"""

import time
import logging
import traceback
import os
import subprocess
import sys

# Local imports
from utilities.time_utility import setup_logging

# Configuration constants
CURRENT_DIR = "/home/i_deed/Desktop/sentinel-files/ultralytics_v1"
LOG_DIR_NAME = "main_logs"
LOG_FILENAME_PREFIX = "main"

# Initialize logging
logger, log_dir_path, ist_now = setup_logging(
    base_dir=CURRENT_DIR,
    log_dir_name=LOG_DIR_NAME,
    log_filename_prefix=LOG_FILENAME_PREFIX
)

# Restart service for changes to take effect
#
#   sudo nano /etc/systemd/system/sentinel_main.service
#   sudo systemctl restart sentinel_main.service
# 

def run_inference():
    """Run the inferencer controller"""
    try:
        logger.info("Starting inferencer controller...")
        inferencer_path = os.path.join(CURRENT_DIR, "inferencer.py")
        result = subprocess.run([sys.executable, inferencer_path], 
                              capture_output=True, text=True, cwd=CURRENT_DIR)
        
        if result.returncode == 0:
            logger.info("Inferencer controller executed successfully")
            if result.stdout:
                logger.info(f"Output: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"Inferencer controller failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Error occurred during inferencer: {e}")
        logger.error(traceback.format_exc())
        return False

def run_synchronizer():
    """Run the synchronizer script"""
    try:
        logger.info("Starting synchronization...")
        synchronizer_path = os.path.join(CURRENT_DIR, "synchronizer.py")
        result = subprocess.run([sys.executable, synchronizer_path], 
                              capture_output=True, text=True, cwd=CURRENT_DIR)
        
        if result.returncode == 0:
            # Extract HTTP status code from synchronizer output if available
            http_status = "N/A"
            if result.stdout:
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines:
                    if "Status Code:" in line:
                        # Extract status code from line like "Status Code: 200 (OK)"
                        parts = line.split("Status Code:")[1].strip().split()
                        http_status = parts[0] if parts else "N/A"
                        break
            
            logger.info(f"[{http_status}] Synchronization completed successfully")
            if result.stdout:
                logger.info(f"Sync output: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"[{result.returncode}] Synchronization failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Sync error: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Error running synchronizer: {e}")
        return False

def run_archiver():
    """Run the archiver script"""
    try:
        logger.info("Starting archiver...")
        archiver_path = os.path.join(CURRENT_DIR, "archiver.py")
        result = subprocess.run([sys.executable, archiver_path], 
                              capture_output=True, text=True, cwd=CURRENT_DIR)
        
        if result.returncode == 0:
            logger.info("Archiver completed successfully")
            if result.stdout:
                logger.info(f"Archiver output: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"Archiver failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Archiver error: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Error running archiver: {e}")
        return False

def run_cleaner():
    """Run the cleaner script"""
    try:
        logger.info("Starting directory cleanup...")
        cleaner_path = os.path.join(CURRENT_DIR, "cleaner.py")
        result = subprocess.run([sys.executable, cleaner_path], 
                              capture_output=True, text=True, cwd=CURRENT_DIR)
        
        if result.returncode == 0:
            logger.info("Directory cleanup completed successfully")
            if result.stdout:
                logger.info(f"Cleaner output: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"Directory cleanup failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Cleaner error: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Error running cleaner: {e}")
        return False

def main():
    """Main controller function"""
    logger.info("=" * 80)
    logger.info("Starting Sentinel System Controller")
    logger.info(f"Started at: {ist_now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    # Phase 1: Run inference
    logger.info("=== PHASE 1: INFERENCE ===")
    inference_success = run_inference()
    
    if not inference_success:
        logger.error("Inference failed, but continuing with other phases...")
    
    # Phase 2: Run synchronizer
    logger.info("=== PHASE 2: SYNCHRONIZATION ===")
    sync_success = run_synchronizer()
    
    # Phase 3: Run archiver (always runs regardless of sync success/failure)
    logger.info("=== PHASE 3: ARCHIVING ===")
    archive_success = run_archiver()
    
    # Phase 4: Run cleaner (always runs after archiver)
    logger.info("=== PHASE 4: CLEANUP ===")
    cleanup_success = run_cleaner()
    
    # Summary
    logger.info("=" * 80)
    logger.info("SENTINEL SYSTEM RUN SUMMARY:")
    logger.info(f"  Inference:    {'SUCCESS' if inference_success else 'FAILED'}")
    logger.info(f"  Synchronizer: {'SUCCESS' if sync_success else 'FAILED'}")
    logger.info(f"  Archiver:     {'SUCCESS' if archive_success else 'FAILED'}")
    logger.info(f"  Cleaner:      {'SUCCESS' if cleanup_success else 'FAILED'}")
    logger.info("=" * 80)
    
    # Overall status
    all_success = inference_success and sync_success and archive_success and cleanup_success
    if all_success:
        logger.info("All phases completed successfully")
        print("Status Code: ALL_SUCCESS")
        return True
    else:
        logger.warning("Some phases failed, but run completed")
        print("Status Code: PARTIAL_SUCCESS")
        return False

if __name__ == "__main__":
    main()

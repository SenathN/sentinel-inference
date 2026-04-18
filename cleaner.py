#!/usr/bin/env python3

"""
Directory cleaner for Sentinel system
Removes empty directories from sentinel_data directory structure
"""

import os
import sys
from utilities.time_utility import setup_logging

# Initialize logging
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
logger, log_dir_path, ist_now = setup_logging(
    base_dir=CURRENT_DIR,
    log_dir_name="cleaner_logs",
    log_filename_prefix="cleaner"
)

# Configuration
SENTINEL_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inference_script", "sentinel_data")


def is_directory_empty(directory_path):
    """Check if a directory is empty (no files or subdirectories)"""
    try:
        return not os.listdir(directory_path)
    except OSError:
        return True  # Directory doesn't exist or is inaccessible


def clean_empty_directories():
    """Remove empty directories from sentinel_data directory structure"""
    logger.info("Starting directory cleanup...")
    logger.info(f"Target directory: {SENTINEL_DATA_DIR}")
    
    if not os.path.exists(SENTINEL_DATA_DIR):
        logger.warning(f"Sentinel data directory does not exist: {SENTINEL_DATA_DIR}")
        return False
    
    empty_dirs_removed = 0
    total_dirs_checked = 0
    
    try:
        # Walk through directory structure from bottom to top
        for root, dirs, files in os.walk(SENTINEL_DATA_DIR, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                total_dirs_checked += 1
                
                if is_directory_empty(dir_path):
                    try:
                        os.rmdir(dir_path)
                        logger.info(f"Removed empty directory: {dir_path}")
                        empty_dirs_removed += 1
                    except OSError as e:
                        logger.error(f"Failed to remove directory {dir_path}: {e}")
        
        # Also check the root level date folders
        for item in os.listdir(SENTINEL_DATA_DIR):
            item_path = os.path.join(SENTINEL_DATA_DIR, item)
            if os.path.isdir(item_path) and is_directory_empty(item_path):
                try:
                    os.rmdir(item_path)
                    logger.info(f"Removed empty date directory: {item_path}")
                    empty_dirs_removed += 1
                except OSError as e:
                    logger.error(f"Failed to remove date directory {item_path}: {e}")
        
        logger.info(f"Cleanup complete: {empty_dirs_removed} empty directories removed")
        logger.info(f"Total directories checked: {total_dirs_checked}")
        return True
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return False


def main():
    """Main cleaner function"""
    logger.info("=" * 60)
    logger.info("Starting Sentinel Data Directory Cleaner")
    logger.info(f"Started at: {ist_now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    success = clean_empty_directories()
    
    if success:
        logger.info("Directory cleanup completed successfully")
        print("Status Code: CLEANUP_SUCCESS")
        return True
    else:
        logger.error("Directory cleanup failed")
        print("Status Code: CLEANUP_FAILED")
        return False


if __name__ == "__main__":
    main()

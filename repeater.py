#!/usr/bin/env python3
import time
import logging
import traceback
import os
import subprocess
import sys
import datetime

# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_DIR = "/home/i_deed/Desktop/sentinel-files/ultralytics_v1"

# Create hierarchical log directory structure based on +0530 timezone
utc_now = datetime.datetime.utcnow()
ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
log_dir_path = os.path.join(CURRENT_DIR, "repeater_logs", 
                           str(ist_now.year), 
                           f"{ist_now.month:02d}", 
                           f"{ist_now.day:02d}")
os.makedirs(log_dir_path, exist_ok=True)

# Generate hourly log filename (for complete hour)
log_filename = f"{ist_now.strftime('%Y-%m-%d-%H')}-repeater_log.log"
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

# Restart the service for changes to take effect
#
#   sudo nano /etc/systemd/system/sentinel_repeater.service
#   sudo systemctl restart sentinel_repeater.service
# 

def main():
    max_run_count = 1

    while max_run_count > 0:
        try:
            # Run the inference script
            script_path = os.path.join(CURRENT_DIR, "inference_script", "oneshotinf.py")
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, cwd=CURRENT_DIR)
            
            if result.returncode == 0:
                logger.info("Inference script executed successfully")
                if result.stdout:
                    logger.info(f"Output: {result.stdout.strip()}")
            else:
                logger.error(f"Inference script failed with return code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error: {result.stderr.strip()}")
            
            logger.info("Run Success.")

        except Exception as e:
            logger.error(f"Error occurred: {e}")
            logger.error(traceback.format_exc())

        finally:
            max_run_count -= 1
            time.sleep(5)   # Run every 5 seconds
    
    # Run synchronizer after inference loop completes
    logger.info("Inference loop completed. Starting synchronization...")
    try:
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
        else:
            logger.error(f"[{result.returncode}] Synchronization failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Sync error: {result.stderr.strip()}")
    except Exception as e:
        logger.error(f"Error running synchronizer: {e}")
        
if __name__ == "__main__":
    main()
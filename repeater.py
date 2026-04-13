#!/usr/bin/env python3
import time
import logging
import traceback
import os

# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_DIR = "/home/i_deed/Desktop/sentinel-files/ultralytics_v1"

# Set up proper logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler( os.path.join(CURRENT_DIR, "repeater_logs", "myscript.log") ),  # optional file log
        logging.StreamHandler()                       # also show in journalctl
    ]
)

logger = logging.getLogger(__name__)

# Restart the service for changes to take effect
#
#   sudo systemctl restart sentinel_repeater.service
#

def main():
    max_run_count = 10

    while max_run_count > 0:
        try:
            # ... do your work ...
            
            logger.info("Run Success.")
            
            time.sleep(5)   # Change 30 to your desired N seconds

        except Exception as e:
            logger.error(f"Error occurred: {e}")
            logger.error(traceback.format_exc())
            time.sleep(5)    # Short delay before retry

        finally:
            max_run_count -= 1
        
if __name__ == "__main__":
    main()
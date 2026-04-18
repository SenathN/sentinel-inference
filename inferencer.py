#!/usr/bin/env python3

"""
Inferencer Controller
Handles multiple inference runs using oneshotinf.py
"""

import os
import sys
import subprocess
import logging
import time
from utilities.time_utility import setup_logging

# Configuration constants
CURRENT_DIR = "/home/i_deed/Desktop/sentinel-files/ultralytics_v1"
MAX_INFERENCES = 2  # Maximum number of inference runs
INFERENCE_DELAY = 1   # Delay between inference runs in seconds
INFERENCE_SCRIPT = "oneshotinf.py"

# Initialize logging
logger, log_dir_path, ist_now = setup_logging(
    base_dir=CURRENT_DIR,
    log_dir_name="inferencer_logs",
    log_filename_prefix="inferencer"
)


def run_single_inference():
    """Run a single inference using oneshotinf.py"""
    try:
        script_path = os.path.join(CURRENT_DIR, "inference_script", INFERENCE_SCRIPT)
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, cwd=CURRENT_DIR)
        
        if result.returncode == 0:
            logger.info("Single inference executed successfully")
            if result.stdout:
                logger.info(f"Output: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"Single inference failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Error occurred during single inference: {e}")
        return False


def main():
    """Main inferencer function - runs multiple inference cycles"""
    logger.info("=" * 60)
    logger.info("Starting Inferencer Controller")
    logger.info(f"Maximum inferences: {MAX_INFERENCES}")
    logger.info(f"Delay between runs: {INFERENCE_DELAY} seconds")
    logger.info("=" * 60)
    
    successful_inferences = 0
    failed_inferences = 0
    
    for run_count in range(MAX_INFERENCES):
        logger.info(f"=== INFERENCE RUN {run_count + 1}/{MAX_INFERENCES} ===")
        
        success = run_single_inference()
        
        if success:
            successful_inferences += 1
            logger.info(f"Run {run_count + 1} completed successfully")
        else:
            failed_inferences += 1
            logger.error(f"Run {run_count + 1} failed")
        
        # Add delay between runs (except after the last run)
        if run_count < MAX_INFERENCES - 1:
            logger.info(f"Waiting {INFERENCE_DELAY} seconds before next run...")
            time.sleep(INFERENCE_DELAY)
    
    # Final summary
    logger.info("=" * 60)
    logger.info("INFERENCE RUN SUMMARY:")
    logger.info(f"  Successful runs: {successful_inferences}")
    logger.info(f"  Failed runs: {failed_inferences}")
    logger.info(f"  Total runs: {successful_inferences + failed_inferences}")
    logger.info("=" * 60)
    
    # Return overall success status
    if successful_inferences > 0:
        logger.info("Inferencer completed with at least one successful run")
        print("Status Code: INFERENCE_SUCCESS")
        return True
    else:
        logger.error("Inferencer completed with no successful runs")
        print("Status Code: INFERENCE_FAILED")
        return False


if __name__ == "__main__":
    main()

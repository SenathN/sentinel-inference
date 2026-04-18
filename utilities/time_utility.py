#!/usr/bin/env python3

"""
Time and logging utility functions for Sentinel applications
"""

import logging
import datetime as dt
import os


class ISTFormatter(logging.Formatter):
    """Custom formatter to display timestamps in IST timezone"""
    def __init__(self):
        super().__init__('%(asctime)s +0530 - %(levelname)s - %(message)s')
    
    def formatTime(self, record, datefmt=None):
        # Convert UTC to IST (+0530)
        utc_dt = dt.datetime.fromtimestamp(record.created, dt.timezone.utc)
        ist_dt = utc_dt + dt.timedelta(hours=5, minutes=30)
        return ist_dt.strftime('%Y-%m-%d %H:%M:%S')


def get_ist_time():
    """Get current time in IST timezone"""
    utc_now = dt.datetime.utcnow()
    ist_now = utc_now + dt.timedelta(hours=5, minutes=30)
    return ist_now


def setup_logging(base_dir, log_dir_name, log_filename_prefix):
    """Set up logging configuration with IST timestamps and hierarchical directory structure
    
    Args:
        base_dir: Base directory for logs
        log_dir_name: Name of the log directory (e.g., 'synchronizer_logs', 'repeater_logs')
        log_filename_prefix: Prefix for log filename (e.g., 'synchronizer', 'repeater')
    
    Returns:
        tuple: (logger, log_dir_path, ist_now)
    """
    # Get current time in IST for directory structure
    ist_now = get_ist_time()
    
    # Create hierarchical log directory structure
    log_dir_path = os.path.join(
        base_dir,
        log_dir_name,
        str(ist_now.year), 
        f"{ist_now.month:02d}", 
        f"{ist_now.day:02d}",
        f"{ist_now.hour:02d}"
    )
    os.makedirs(log_dir_path, exist_ok=True)
    
    # Generate log filename with timestamp
    log_filename = f"{ist_now.strftime('%Y-%m-%d-%H')}-{log_filename_prefix}.log"
    log_file_path = os.path.join(log_dir_path, log_filename)
    
    # Custom formatter for IST timestamps
    ist_formatter = ISTFormatter()
    
    # Set up handlers with custom formatter
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(ist_formatter)
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(ist_formatter)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, stream_handler]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Log file created: {log_file_path}")
    
    return logger, log_dir_path, ist_now


def get_status_description(status_code):
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

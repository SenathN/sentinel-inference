#!/usr/bin/env python3

"""
Configuration utility for loading environment variables from .env file.
"""

import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file in project root."""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def get_backend_url():
    """Get backend URL from environment or default."""
    load_env()
    return os.getenv('BACKEND_URL', 'https://sentinel.copper-wave.com/api/observer/data-sync')


def get_backend_sync_check_url():
    """Get backend sync-check URL from environment or default."""
    load_env()
    return os.getenv('BACKEND_SYNC_CHECK_URL', 'http://192.168.1.124:8000/api/observer/sync-check')


def get_api_key():
    """Get API key from environment or default."""
    load_env()
    return os.getenv('API_KEY', 'your-api-key-here')


def use_mock_gps():
    """Get USE_MOCK_DATA setting from environment or default."""
    load_env()
    return os.getenv('USE_MOCK_DATA', 'False').lower() in ('true', '1', 'yes')

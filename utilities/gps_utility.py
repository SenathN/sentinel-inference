#!/usr/bin/env python3

"""
GPS utility for reading NMEA data from serial port on Raspberry Pi.
Reads from /dev/serial0 and parses NMEA sentences using pynmea2.
"""

import time
import pynmea2


SERIAL_PORT = '/dev/serial0'
GPS_TIMEOUT = 10  # seconds to wait for a valid fix


def _parse_gprmc(line):
    """Parse GPRMC sentence and return (lat, lon, utc_time) or None."""
    msg = pynmea2.parse(line)
    if msg.status != 'A':
        return None  # Void/invalid fix
    lat = msg.latitude
    lon = msg.longitude
    utc_time = msg.timestamp
    if lat is not None and lon is not None and (lat != 0.0 or lon != 0.0):
        return lat, lon, utc_time
    return None


def _parse_gpgga(line):
    """Parse GPGGA sentence and return (lat, lon, utc_time) or None."""
    msg = pynmea2.parse(line)
    if msg.gps_qual == 0:
        return None  # No fix
    lat = msg.latitude
    lon = msg.longitude
    utc_time = msg.timestamp
    if lat is not None and lon is not None and (lat != 0.0 or lon != 0.0):
        return lat, lon, utc_time
    return None


def get_gps_data(serial_port=SERIAL_PORT, timeout=GPS_TIMEOUT, debug=False):
    """Read NMEA sentences from serial port and return GPS coordinates.

    Reads lines from the serial port until a valid fix is found or
    timeout is reached. Tries GPRMC first (recommended minimum), then
    GPGGA (fix data) as fallback.

    Args:
        serial_port: Path to serial device (default: /dev/serial0)
        timeout: Max seconds to wait for a valid fix (default: 10)
        debug: If True, print debug info about NMEA sentences (default: False)

    Returns:
        tuple: (latitude, longitude, utc_time) or (None, None, current_utc_time)
               if no fix is available.
    """
    start = time.time()
    sentence_count = 0
    try:
        with open(serial_port, 'r') as port:
            while time.time() - start < timeout:
                line = port.readline().strip()
                if not line:
                    continue
                sentence_count += 1
                try:
                    if line.startswith('$GPRMC'):
                        if debug:
                            print(f"[DEBUG] GPRMC: {line}")
                        result = _parse_gprmc(line)
                        if result:
                            if debug:
                                print(f"[DEBUG] GPRMC valid fix found")
                            return result
                        elif debug:
                            print(f"[DEBUG] GPRMC no fix (status invalid or empty coords)")
                    elif line.startswith('$GPGGA'):
                        if debug:
                            print(f"[DEBUG] GPGGA: {line}")
                        result = _parse_gpgga(line)
                        if result:
                            if debug:
                                print(f"[DEBUG] GPGGA valid fix found")
                            return result
                        elif debug:
                            print(f"[DEBUG] GPGGA no fix (gps_qual=0 or empty coords)")
                except pynmea2.ParseError as e:
                    if debug:
                        print(f"[DEBUG] Parse error: {e}")
                    continue
                except Exception as e:
                    if debug:
                        print(f"[DEBUG] Exception: {e}")
                    continue
    except FileNotFoundError:
        print(f"[GPS] Serial port {serial_port} not found")
    except PermissionError:
        print(f"[GPS] Permission denied for {serial_port} (try: sudo usermod -aG dialout $USER)")
    except Exception as e:
        print(f"[GPS] Error reading serial: {e}")

    if debug:
        print(f"[DEBUG] Read {sentence_count} sentences, no valid fix found")
    return None, None, time.strftime("%Y-%m-%dT%H:%M:%SZ")

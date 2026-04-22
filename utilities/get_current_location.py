#!/usr/bin/env python3

"""
Standalone utility to fetch and display current GPS location.
Uses the GPS utility module to read NMEA data from /dev/serial0.
"""

import sys
import os
import time
import pynmea2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.gps_utility import get_gps_data, SERIAL_PORT, GPS_TIMEOUT


def get_gps_with_connectivity(serial_port=SERIAL_PORT, timeout=GPS_TIMEOUT):
    """Read GPS data and satellite connectivity information."""
    start = time.time()
    satellites = {}  # {sat_id: snr}
    lat, lon, utc_time = None, None, None
    sentence_count = 0
    
    try:
        with open(serial_port, 'r') as port:
            while time.time() - start < timeout:
                line = port.readline().strip()
                if not line:
                    continue
                sentence_count += 1
                
                try:
                    if line.startswith('$GPGSV'):
                        msg = pynmea2.parse(line)
                        # GPGSV format: $GPGSV,<num_msgs>,<msg_num>,<num_sv>,<sat_id1>,<elev1>,<azim1>,<snr1>,<sat_id2>,<elev2>,<azim2>,<snr2>,...
                        data = msg.data
                        if len(data) >= 4:
                            num_sv = int(data[2]) if data[2] else 0
                            # Parse satellites (4 per sentence, starting from index 3)
                            for i in range(3, len(data), 4):
                                if i + 3 < len(data):
                                    sat_id = int(data[i]) if data[i] else None
                                    elevation = int(data[i+1]) if data[i+1] else None
                                    azimuth = int(data[i+2]) if data[i+2] else None
                                    snr = int(data[i+3]) if data[i+3] else None
                                    if sat_id is not None and sat_id > 0:
                                        satellites[sat_id] = snr
                    
                    elif line.startswith('$GPRMC'):
                        msg = pynmea2.parse(line)
                        if msg.status == 'A':
                            lat = msg.latitude
                            lon = msg.longitude
                            utc_time = msg.timestamp
                            if lat and lon and (lat != 0.0 or lon != 0.0):
                                return lat, lon, utc_time, satellites, sentence_count
                    
                    elif line.startswith('$GPGGA'):
                        msg = pynmea2.parse(line)
                        if msg.gps_qual > 0:
                            lat = msg.latitude
                            lon = msg.longitude
                            utc_time = msg.timestamp
                            if lat and lon and (lat != 0.0 or lon != 0.0):
                                return lat, lon, utc_time, satellites, sentence_count
                except Exception:
                    continue
    except FileNotFoundError:
        print(f"[GPS] Serial port {serial_port} not found")
    except PermissionError:
        print(f"[GPS] Permission denied for {serial_port}")
    except Exception as e:
        print(f"[GPS] Error: {e}")
    
    utc_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    return lat, lon, utc_time, satellites, sentence_count


def main():
    print(f"Fetching GPS location from {SERIAL_PORT}...")
    print(f"Timeout: {GPS_TIMEOUT} seconds")
    print("-" * 50)
    
    lat, lon, utc_time, satellites, sentence_count = get_gps_with_connectivity()
    
    print(f"NMEA sentences read: {sentence_count}")
    print(f"Satellites in view: {len(satellites)}")
    
    if satellites:
        print("Satellite details:")
        for sat_id, snr in sorted(satellites.items()):
            if snr:
                print(f"  SAT {sat_id}: SNR {snr} dB")
            else:
                print(f"  SAT {sat_id}: No signal")
    else:
        print("No satellites detected")
    
    print("-" * 50)
    
    if lat is not None and lon is not None:
        print(f"Latitude:  {lat:.6f}")
        print(f"Longitude: {lon:.6f}")
        print(f"UTC Time:  {utc_time}")
        print("-" * 50)
        print("Status: GPS fix acquired")
    else:
        print(f"Latitude:  None")
        print(f"Longitude: None")
        print(f"UTC Time:  {utc_time}")
        print("-" * 50)
        print("Status: No GPS fix - ensure module has clear sky view")
        print("Note: This is normal indoors or without satellite reception")
        if len(satellites) > 0:
            print(f"      {len(satellites)} satellite(s) visible but insufficient for position fix")


if __name__ == "__main__":
    main()

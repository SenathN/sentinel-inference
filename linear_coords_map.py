import datetime
import random

def get_start_end_coordinates(hour = 0):
    """Get first and last coordinates from the original JSON data"""
    # First coordinate: [6.92778, 79.84472]
    # Last coordinate: [6.84376, 79.96811]
    
    if hour % 2 == 1:
        start_coord = [6.878400, 81.828789]
        end_coord = [6.932654, 79.845963]
    else:
        start_coord = [6.932654, 79.845963]
        end_coord = [6.878400, 81.828789]

    return start_coord, end_coord

def get_coordinate_by_time(target_time=None):
    """
    Get coordinate based on time, spanning 826 coordinates over 1 hour.
    Uses linear interpolation between first and last coordinates from JSON.
    
    Args:
        target_time: datetime object (defaults to current time)
    
    Returns:
        tuple: (latitude, longitude) for the given time
    """
    if target_time is None:
        # Get current time in +05:30 timezone
        utc_now = datetime.datetime.utcnow()
        target_time = utc_now + datetime.timedelta(hours=5, minutes=30)
    
    # Calculate minutes and seconds past the hour
    minutes_past_hour = target_time.minute
    seconds_past_hour = target_time.second
    total_seconds_past_hour = minutes_past_hour * 60 + seconds_past_hour
    
    # Calculate coordinate index (826 coordinates spread over 3600 seconds = 1 hour)
    total_coords = 826
    total_seconds_in_span = 3600
    
    # Linear interpolation: index = (seconds_past_hour / 3600) * 826
    index = int((total_seconds_past_hour / total_seconds_in_span) * (total_coords - 1))
    
    # Use modulo to loop continuously after 1 hour
    index = index % total_coords
    
    # Get start and end coordinates
    start_coord, end_coord = get_start_end_coordinates(target_time.hour)
    
    # Linear interpolation between start and end coordinates
    progress = index / (total_coords - 1)  # 0.0 to 1.0
    
    lat = start_coord[0] + (end_coord[0] - start_coord[0]) * progress
    lon = start_coord[1] + (end_coord[1] - start_coord[1]) * progress
    
    # Add small random noise for more realistic movement
    # Noise range: approximately ±0.0001 degrees (about 11 meters)
    lat_noise = random.uniform(-0.01, 0.001)
    lon_noise = random.uniform(-0.001, 0.001)
    
    lat += lat_noise
    lon += lon_noise
    
    # Apply time-based offset relative to 12 noon
    hour = target_time.hour
    if hour >= 12:
        # After noon: add n*2 km to north (positive latitude)
        hours_after_noon = hour - 12
        offset_km = hours_after_noon * 5
        # Convert km to degrees latitude (approximately 111 km per degree)
        lat_offset = offset_km / 111.0
        lat += lat_offset
    else:
        # Before noon: add n*2 km to south (negative latitude)
        hours_before_noon = 12 - hour
        offset_km = hours_before_noon * 5
        # Convert km to degrees latitude
        lat_offset = offset_km / 111.0
        lat -= lat_offset
    
    return lat, lon

def get_coordinate_by_timestamp(timestamp_str):
    """
    Get coordinate based on timestamp string.
    
    Args:
        timestamp_str: String in format "YYYY-MM-DDTHH:MM:SS+05:30"
    
    Returns:
        tuple: (latitude, longitude) for the given timestamp
    """
    # Parse timestamp string
    # Remove timezone info for parsing
    time_part = timestamp_str.split('+')[0]
    target_time = datetime.datetime.strptime(time_part, "%Y-%m-%dT%H:%M:%S")
    
    return get_coordinate_by_time(target_time)

# Example usage and testing
if __name__ == "__main__":
    # Test current time
    lat, lon = get_coordinate_by_time()
    print(f"Current time coordinate: {lat}, {lon}")
    
    # Test specific times
    test_times = [
        "2026-04-15T00:00:00+05:30",  # Start of hour
        "2026-04-15T00:20:00+05:30",  # 20 minutes (should be ~413th index)
        "2026-04-15T00:45:00+05:30",  # 45 minutes
        "2026-04-15T00:59:59+05:30",  # End of hour
    ]
    
    for ts in test_times:
        lat, lon = get_coordinate_by_timestamp(ts)
        print(f"Timestamp {ts}: {lat}, {lon}")

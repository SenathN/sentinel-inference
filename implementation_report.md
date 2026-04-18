# Sentinel Inference System Implementation Report

## Executive Summary

The Sentinel Inference System is a comprehensive computer vision pipeline designed for automated object detection and data management. The system consists of three main components that work in coordination: the inference engine, synchronizer, and archiver. This implementation provides real-time object detection, secure data transmission to backend services, and automated archival of processed data.

## System Architecture

### Core Components

1. **Inference Engine** (`inference_script/oneshotinf.py`)
2. **Synchronizer** (`synchronizer.py`)
3. **Archiver** (`archiver.py`)
4. **Repeater** (`repeater.py`) - Process management

## Implementation Details

### 1. Inference Engine

**File:** `inference_script/oneshotinf.py`

**Key Features:**
- YOLOv8-based object detection
- Real-time image processing
- Metadata generation with unique IDs
- Structured data output

**Implementation Highlights:**
```python
# Unique ID generation format: sentinel_YYYYMMDD-HHMMSS_hash
unique_id = f"sentinel_{timestamp}_{hash_suffix}"
```

**Data Structure:**
- JSON metadata files containing detection results
- Corresponding image files
- Timestamp-based organization in directory structure

### 2. Synchronizer Component

**File:** `synchronizer.py`

**Primary Function:** 
Collect and transmit detection data to backend API

**Key Implementation Features:**

#### File Selection Algorithm
- **Creation Date-Based Sorting**: Files are selected based on actual file creation time using `os.path.getctime()`
- **Priority Processing**: Most recently created files are processed first
- **Batch Processing**: Collects up to 10 files per synchronization cycle

```python
# Reference: Lines 122-131 in synchronizer.py
json_files_with_dates = []
for json_file in json_files:
    json_path = os.path.join(folder, json_file)
    creation_time = os.path.getctime(json_path)
    json_files_with_dates.append((json_file, creation_time))

# Sort by creation time (newest first)
json_files_with_dates.sort(key=lambda x: x[1], reverse=True)
```

#### Data Transmission Protocol
- **Multipart Form Data**: Secure transmission of JSON metadata and image files
- **Checksum Verification**: SHA256 hash generation for data integrity
- **Network Diagnostics**: Pre-connection testing and comprehensive error handling

```python
# Reference: Lines 244-259 in synchronizer.py
# Network connectivity testing
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
result = sock.connect_ex((host, port))
```

#### Logging System
- **Hierarchical Log Structure**: Year/Month/Day/Hour organization
- **IST Timezone**: Proper timezone handling (+0530 offset)
- **Detailed Response Logging**: Complete API request/response documentation

### 3. Archiver Component

**File:** `archiver.py`

**Primary Function:** 
Automated archival of synchronized data

**Key Implementation Features:**

#### Backend Synchronization Check
- **API Integration**: Queries backend for synchronized unique IDs
- **Batch Processing**: Processes up to 50 IDs per cycle
- **Creation Date-Based Selection**: Prioritizes most recent files

```python
# Reference: Lines 64-72 in archiver.py
# Get creation time for sorting
creation_time = os.path.getctime(file_path)
all_files_with_dates.append((unique_id, creation_time))

# Sort by creation time (newest first)
all_files_with_dates.sort(key=lambda x: x[1], reverse=True)
```

#### File Archival Process
- **Directory Structure Preservation**: Maintains original date/hour organization
- **Duplicate Handling**: Safe file replacement with conflict resolution
- **Comprehensive Logging**: Detailed archival operation tracking

#### Timestamp Correction
- **Custom IST Formatter**: Proper timezone-aware logging
- **UTC to IST Conversion**: Accurate timestamp representation

```python
# Reference: Lines 25-33 in archiver.py
class ISTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        utc_dt = dt.datetime.fromtimestamp(record.created, dt.timezone.utc)
        ist_dt = utc_dt + dt.timedelta(hours=5, minutes=30)
        return ist_dt.strftime('%Y-%m-%d %H:%M:%S')
```

### 4. Process Management

**File:** `repeater.py`

**Function:** 
Orchestrates the execution cycle of all components

**Implementation:**
- Configurable execution intervals
- Error recovery and retry mechanisms
- Process monitoring and logging

## Data Flow Architecture

```
Input Images
    |
    v
[Inference Engine] --> Detection Results (JSON + Images)
    |
    v
[Synchronizer] --> Backend API Transmission
    |
    v
[Archiver] --> Local Archive Storage
```

## Technical Specifications

### File Organization Structure
```
inference_script/
sentinel_data/
    YYYY-MM-DD/
        HH/
            sentinel_YYYYMMDD-HHMMSS_hash.json
            corresponding_image.jpg
inference_archive/
    YYYY-MM-DD/
        HH/
            archived_files...
```

### API Endpoints
- **Data Sync**: `POST /api/observer/data-sync`
- **Sync Check**: `POST /api/observer/sync-check`

### Security Features
- API key authentication
- SHA256 checksums for data integrity
- SSL/TLS support (configurable)

### Performance Optimizations
- Creation date-based file prioritization
- Batch processing for network efficiency
- Asynchronous error handling

## Configuration Management

### Key Configuration Parameters
- **SYNC_COUNT**: 10 files per synchronization cycle
- **API_TIMEOUT**: 30 seconds
- **MAX_RETRIES**: Configurable retry mechanisms
- **TIMEZONE**: IST (+0530)

### Logging Configuration
- **Log Levels**: INFO, WARNING, ERROR
- **Log Rotation**: Hourly log files
- **Log Retention**: Hierarchical directory structure

## Error Handling and Resilience

### Network Error Recovery
- Connection timeout handling
- Automatic retry mechanisms
- Fallback error reporting

### Data Integrity Measures
- File existence verification
- Hash-based checksum validation
- Duplicate file handling

### Logging and Monitoring
- Comprehensive error logging
- Performance metrics tracking
- Network diagnostics

## Security Considerations

### Authentication
- Bearer token authentication
- API key validation
- Request header security

### Data Protection
- Local file encryption (optional)
- Secure file transmission
- Access control through directory permissions

## Maintenance and Operations

### Log Management
- Automated log directory creation
- Timestamp-based log organization
- IST timezone standardization

### File Cleanup
- Automated archival process
- Storage space management
- Data retention policies

## Future Enhancements

### Scalability Improvements
- Distributed processing capabilities
- Load balancing for API calls
- Horizontal scaling support

### Monitoring Enhancements
- Real-time dashboard integration
- Performance analytics
- Alert system implementation

### Security Enhancements
- End-to-end encryption
- Multi-factor authentication
- Audit trail implementation

## Conclusion

The Sentinel Inference System provides a robust, scalable solution for automated object detection with comprehensive data management capabilities. The implementation prioritizes data integrity, security, and operational reliability through careful architecture design and comprehensive error handling.

The creation date-based file selection algorithm ensures optimal performance by prioritizing the most recent data, while the comprehensive logging system provides detailed operational visibility for maintenance and troubleshooting purposes.

## References

1. **Synchronizer Implementation**: `/synchronizer.py` - Lines 80-175 (data collection), Lines 176-340 (transmission)
2. **Archiver Implementation**: `/archiver.py` - Lines 43-112 (sync checking), Lines 114-196 (archival process)
3. **Inference Engine**: `/inference_script/oneshotinf.py` - Object detection and metadata generation
4. **Process Management**: `/repeater.py` - System orchestration and monitoring

---
*Report Generated: April 18, 2026*
*System Version: 1.0*

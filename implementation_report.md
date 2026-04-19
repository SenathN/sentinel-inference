# Sentinel Inference System Implementation Report

## Executive Summary

The Sentinel Inference System is a comprehensive computer vision pipeline designed for automated object detection and data management. The system consists of five main components that work in coordination: the main controller, inferencer engine, synchronizer, archiver, and cleaner. This implementation provides real-time object detection, secure data transmission to backend services, automated archival of processed data, and directory cleanup maintenance.

## System Architecture

### Core Components

1. **Main Controller** (`main.py`) - System orchestration and phase management
2. **Inferencer Engine** (`inferencer.py`) - Multi-run inference controller
3. **Detection Engine** (`inference_script/oneshotinf.py`) - YOLO-based object detection
4. **Synchronizer** (`synchronizer.py`) - Backend data transmission
5. **Archiver** (`archiver.py`) - Automated data archival
6. **Cleaner** (`cleaner.py`) - Directory maintenance
7. **Utilities** (`utilities/time_utility.py`) - Shared time/logging functions

## Implementation Details

### 1. Main Controller

**File:** `main.py`

**Primary Function:** 
Orchestrates the complete 4-phase execution cycle

**Key Implementation Features:**

#### Phase-Based Execution
- **Phase 1: Inference** - Runs inferencer controller for multiple detection cycles
- **Phase 2: Synchronization** - Transmits collected data to backend
- **Phase 3: Archiving** - Archives synchronized data locally
- **Phase 4: Cleanup** - Removes empty directories

```python
# Reference: Lines 140-180 in main.py
def main():
    # Phase 1: Run inference
    inference_success = run_inference()
    
    # Phase 2: Run synchronizer
    sync_success = run_synchronizer()
    
    # Phase 3: Run archiver (always runs regardless of sync success/failure)
    archive_success = run_archiver()
    
    # Phase 4: Run cleaner (always runs after archiver)
    cleanup_success = run_cleaner()
```

#### Comprehensive Status Reporting
- Individual phase success/failure tracking
- Overall system status codes (`ALL_SUCCESS`, `PARTIAL_SUCCESS`)
- Detailed execution summaries

### 2. Inferencer Engine

**File:** `inferencer.py`

**Primary Function:** 
Manages multiple inference runs using configurable parameters

**Key Implementation Features:**

#### Configurable Inference Parameters
```python
# Reference: Lines 14-17 in inferencer.py
MAX_INFERENCES = 2  # Maximum number of inference runs
INFERENCE_DELAY = 1   # Delay between inference runs in seconds
INFERENCE_SCRIPT = "oneshotinf.py"
```

#### Multi-Run Execution Loop
- **Sequential Processing**: Runs detection cycles with configurable delays
- **Success/Failure Tracking**: Monitors individual run outcomes
- **Comprehensive Logging**: Detailed run-by-run progress reporting

#### Run Summary Reporting
- Successful vs failed run counts
- Total execution statistics
- Status code extraction (`INFERENCE_SUCCESS`, `INFERENCE_FAILED`)

### 3. Detection Engine

**File:** `inference_script/oneshotinf.py`

**Key Features:**
- YOLOv8-based object detection
- Real-time image processing
- Metadata generation with unique IDs
- IST timezone timestamp handling using centralized utility

**Implementation Highlights:**
```python
# Using centralized time utility
from utilities.time_utility import get_ist_time

# Get timestamp in +0530 timezone using utility
ist_time = get_ist_time()
timestamp = ist_time.strftime("%Y%m%d-%H%M%S")
```

**Data Structure:**
- JSON metadata files containing detection results
- Corresponding image files
- Timestamp-based organization in directory structure

### 4. Synchronizer Component

**File:** `synchronizer.py`

**Primary Function:** 
Collect and transmit detection data to backend API

**Key Implementation Features:**

#### Enhanced Data Collection
- **Hierarchical Directory Traversal**: Processes date/hour folder structure
- **Configurable Batch Size**: Collects up to 15 files per cycle
- **JSON Validation**: Ensures data integrity before transmission

#### Multipart Form Data Transmission
- **Indexed Field Naming**: Uses `image_0`, `image_1` to match `data_0`, `data_1`
- **File Integrity**: SHA256 hash generation for each image
- **Comprehensive Error Handling**: Network timeout, connection errors, request exceptions

#### Response Processing
- **Backend Response Logging**: Complete API response documentation
- **File Reception Tracking**: Monitors `files_received` count from backend
- **Status Code Extraction**: Human-readable HTTP status descriptions

### 5. Archiver Component

**File:** `archiver.py`

**Primary Function:** 
Automated archival of synchronized data

**Key Implementation Features:**

#### Backend Synchronization Check
- **API Integration**: Queries backend for synchronized unique IDs
- **Batch Processing**: Processes multiple IDs per cycle
- **Creation Date-Based Selection**: Prioritizes most recent files

#### File Archival Process
- **Directory Structure Preservation**: Maintains original date/hour organization
- **Safe File Operations**: Conflict resolution and error handling
- **Centralized Logging**: Uses shared time utility for consistent timestamps

### 6. Cleaner Component

**File:** `cleaner.py`

**Primary Function:** 
Removes empty directories from sentinel_data structure

**Key Implementation Features:**

#### Bottom-Up Directory Traversal
- **Safe Empty Detection**: Only removes truly empty directories
- **Hierarchical Cleanup**: Processes subdirectories before parent directories
- **Comprehensive Reporting**: Tracks directories checked and removed

#### Error Handling
- **Permission Error Handling**: Graceful handling of inaccessible directories
- **Detailed Logging**: IST timezone logging with centralized utility
- **Status Reporting**: `CLEANUP_SUCCESS`/`CLEANUP_FAILED` status codes

### 7. Utilities Module

**File:** `utilities/time_utility.py`

**Primary Function:** 
Centralized time and logging utilities

**Key Implementation Features:**

#### IST Timezone Handling
```python
# Reference: Lines 16-24 in time_utility.py
class ISTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        utc_dt = dt.datetime.fromtimestamp(record.created, dt.timezone.utc)
        ist_dt = utc_dt + dt.timedelta(hours=5, minutes=30)
        return ist_dt.strftime('%Y-%m-%d %H:%M:%S')
```

#### Centralized Logging Setup
- **Hierarchical Log Structure**: Year/Month/Day/Hour organization
- **Consistent Formatting**: IST timestamps across all components
- **Reusable Functions**: `setup_logging()`, `get_ist_time()`, `get_status_description()`

## Data Flow Architecture

```
[Main Controller]
    |
    +-- Phase 1: [Inferencer] --> Multiple [Detection Engine] Runs --> Detection Results
    |
    +-- Phase 2: [Synchronizer] --> Backend API Transmission
    |
    +-- Phase 3: [Archiver] --> Local Archive Storage
    |
    +-- Phase 4: [Cleaner] --> Directory Maintenance
```

## Technical Specifications

### File Organization Structure
```
ultralytics_v1/
|
+-- main.py                    # System controller
+-- inferencer.py              # Inference controller
+-- synchronizer.py            # Backend transmission
+-- archiver.py                # Data archival
+-- cleaner.py                 # Directory cleanup
+-- utilities/
|   +-- time_utility.py       # Shared time/logging functions
|
+-- inference_script/
|   +-- oneshotinf.py          # YOLO detection engine
|   +-- sentinel_data/         # Active data directory
|   |   +-- YYYY-MM-DD/
|   |       +-- HH/
|   |           +-- sentinel_YYYYMMDD-HHMMSS_hash.json
|   |           +-- corresponding_image.jpg
|   +-- inference_archive/     # Archived data
|
+-- *_logs/                    # Hierarchical log directories
    +-- YYYY/MM/DD/HH/
        +-- YYYY-MM-DD-HH-*.log
```

### API Endpoints
- **Data Sync**: `POST http://192.168.1.124:8000/api/observer/data-sync`
- **Sync Check**: `POST http://192.168.1.124:8000/api/observer/sync-check`

### Configuration Management

#### Key Configuration Parameters
```python
# Main Controller
CURRENT_DIR = "/home/i_deed/Desktop/sentinel-files/ultralytics_v1"
LOG_DIR_NAME = "main_logs"
LOG_FILENAME_PREFIX = "main"

# Inferencer
MAX_INFERENCES = 2
INFERENCE_DELAY = 1
INFERENCE_SCRIPT = "oneshotinf.py"

# Synchronizer
BACKEND_URL = "http://192.168.1.124:8000/api/observer/data-sync"
SYNC_COUNT = 15
REQUEST_TIMEOUT = 120
API_KEY = "your-api-key-here"

# Utilities
TIMEZONE_OFFSET_HOURS = 5
TIMEZONE_OFFSET_MINUTES = 30
```

### Security Features
- API key authentication with Bearer tokens
- SHA256 checksums for data integrity
- Multipart form data for secure file transmission
- User-Agent identification

### Performance Optimizations
- Creation date-based file prioritization
- Batch processing for network efficiency (15 files per sync)
- Configurable inference delays
- Bottom-up directory cleanup

## Error Handling and Resilience

### Network Error Recovery
- Connection timeout handling (120 seconds)
- Automatic retry mechanisms with detailed logging
- Specific exception handling (Timeout, ConnectionError, RequestException)

### Data Integrity Measures
- JSON structure validation before processing
- File existence verification
- Hash-based checksum validation
- Duplicate file handling in archiver

### Logging and Monitoring
- Comprehensive error logging with IST timestamps
- Performance metrics tracking
- Phase-by-phase execution monitoring
- Hierarchical log organization for easy troubleshooting

## System Integration

### Service Management
```bash
# System service configuration
sudo nano /etc/systemd/system/sentinel_main.service
sudo systemctl restart sentinel_main.service
```

### Execution Modes
- **Full System**: `./main.py` - Complete 4-phase execution
- **Individual Components**: Each script can run independently
- **Standalone Inference**: `./inferencer.py` - Multi-run detection cycles

## Maintenance and Operations

### Log Management
- Automated log directory creation with IST timestamps
- Hierarchical organization: `logs/YYYY/MM/DD/HH/`
- Centralized time formatting across all components
- Comprehensive status code reporting

### File Cleanup
- Automated empty directory removal
- Storage space management through archival
- Configurable cleanup parameters

### Data Retention
- Active data in `sentinel_data/`
- Archived data in `inference_archive/`
- Backend synchronization tracking

## Security Considerations

### Authentication
- Bearer token authentication
- API key validation
- Request header security with User-Agent

### Data Protection
- Secure file transmission via multipart form data
- Local file access control through directory permissions
- Checksum validation for data integrity

## Future Enhancements

### Scalability Improvements
- Configurable batch sizes for different environments
- Distributed processing capabilities
- Load balancing for API calls

### Monitoring Enhancements
- Real-time dashboard integration
- Performance analytics and metrics
- Alert system implementation

### Feature Enhancements
- Configurable inference parameters via config files
- Dynamic backend URL configuration
- Enhanced error recovery mechanisms

## Conclusion

The Sentinel Inference System provides a robust, modular solution for automated object detection with comprehensive data management capabilities. The implementation prioritizes:

1. **Modularity**: Clear separation of concerns with dedicated components
2. **Maintainability**: Centralized utilities and consistent logging
3. **Reliability**: Comprehensive error handling and status reporting
4. **Performance**: Optimized file processing and network transmission
5. **Scalability**: Configurable parameters and extensible architecture

The phase-based execution ensures systematic processing while the centralized time utility maintains consistency across all components. The system provides detailed operational visibility through comprehensive logging and status reporting.

## References

1. **Main Controller**: `/main.py` - System orchestration and phase management
2. **Inferencer Engine**: `/inferencer.py` - Multi-run inference control
3. **Detection Engine**: `/inference_script/oneshotinf.py` - YOLO object detection
4. **Synchronizer**: `/synchronizer.py` - Backend data transmission
5. **Archiver**: `/archiver.py` - Data archival and synchronization checking
6. **Cleaner**: `/cleaner.py` - Directory maintenance
7. **Utilities**: `/utilities/time_utility.py` - Shared time and logging functions

---
*Report Generated: April 18, 2026*
*System Version: 2.0*
*Architecture: Modular Phase-Based Execution*

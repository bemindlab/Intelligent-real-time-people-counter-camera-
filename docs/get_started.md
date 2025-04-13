# MANTA Documentation

**Monitoring and Analytics Node for Tracking Activity**

Version 1.1 | April 11, 2025

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Setup & Installation](#3-setup--installation)
4. [Configuration](#4-configuration)
5. [Core Components](#5-core-components)
6. [Firebase Integration](#6-firebase-integration)
7. [n8n Automation](#7-n8n-automation)
8. [Running & Deploying](#8-running--deploying)
9. [Troubleshooting](#9-troubleshooting)
10. [Development Guide](#10-development-guide)
11. [API Reference](#11-api-reference)
12. [Contributing](#12-contributing)

---

## 1. Introduction

MANTA (Monitoring and Analytics Node for Tracking Activity) is an intelligent camera-based system designed to detect, count, and track people in real-time. The system utilizes computer vision and machine learning to identify unique individuals while avoiding double-counting through re-identification techniques.

### Key Features:

- Real-time person detection using YOLO models
- Person re-identification to prevent duplicate counting
- Local logging and data storage
- Firebase Realtime Database integration for cloud storage
- Automation workflows with n8n for notifications and data processing
- Offline capability with data synchronization upon reconnection

### Use Cases:

- Retail traffic analysis
- Smart building occupancy monitoring
- Public space usage analytics
- Event attendance tracking
- Security monitoring

---

## 2. System Overview

MANTA consists of several integrated components that work together to provide a complete people tracking solution:

![System Architecture](https://via.placeholder.com/800x400?text=MANTA+System+Architecture)

### Architecture Components:

1. **Camera & NPU Board**

   - Physical camera for video capture
   - Optional Neural Processing Unit (NPU) for hardware acceleration

2. **Detection System**

   - YOLO inference for person detection
   - Optimized for edge devices

3. **Re-Identification System**

   - Feature extraction and vector comparison
   - Person hash generation to identify unique individuals

4. **Logging & Storage**

   - Local JSON/SQLite storage
   - Firebase Realtime Database integration

5. **Automation System**
   - n8n workflows for notifications and data processing
   - Integration with external services (LINE, Telegram, Google Sheets, etc.)

### Data Flow:

1. Video stream is captured from the camera
2. Frames are processed by YOLO to detect people
3. Detected people are analyzed by the Re-ID system
4. New unique people are logged locally
5. Log data is synced to Firebase when online
6. n8n processes data and triggers automated workflows

---

## 3. Setup & Installation

### Prerequisites

- Python 3.8+ with pip
- Docker and Docker Compose (for n8n)
- Edge computing device (Raspberry Pi 5, NVIDIA Jetson, or similar)
- Camera (USB, CSI, or IP camera)
- Optional: Neural Processing Unit (Coral USB, Hailo, etc.)

### Hardware Setup

1. **Raspberry Pi 5 Setup**:

   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install dependencies
   sudo apt install python3-pip python3-opencv libatlas-base-dev libjpeg-dev libtiff5 -y
   sudo apt install docker.io docker-compose -y

   # Enable camera if using Raspberry Pi camera
   sudo raspi-config  # Navigate to Interface Options → Camera and enable
   ```

2. **Camera Connection**:

   - For USB cameras: Simply connect to a USB port
   - For Raspberry Pi Camera: Connect to the CSI port
   - For IP cameras: Note the RTSP URL for configuration

3. **NPU Setup (Optional)**:
   - **Google Coral**:
     ```bash
     echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
     curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
     sudo apt update
     sudo apt install libedgetpu1-std python3-pycoral
     ```
   - Other NPUs: Follow manufacturer's installation instructions

### Software Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/username/manta.git
   cd manta
   ```

2. **Install Python Dependencies**:

   ```bash
   pip install -r models/requirements.txt
   ```

3. **Download YOLO Model**:

   ```bash
   # Create models directory if it doesn't exist
   mkdir -p models

   # Download YOLOv8n ONNX model
   wget -O models/yolov8n.onnx https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.onnx
   ```

4. **Setup Firebase**:

   - Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
   - Enable Realtime Database
   - Generate and download a service account key
   - Place the key at `firebase/firebase_config.json`

5. **Setup n8n**:

   ```bash
   # Navigate to n8n directory
   cd n8n

   # Start n8n with Docker Compose
   docker-compose up -d
   ```

---

## 4. Configuration

MANTA uses a YAML configuration file located at `config/config.yaml` to control all aspects of the system.

### Configuration Structure

```yaml
# Camera Configuration
camera:
  id: "cam_001"
  source: 0 # 0 for default webcam, can be a RTSP URL or file path
  resolution:
    width: 640
    height: 480
  fps: 15

# Detection Configuration
detection:
  model_path: "../models/yolov8n.onnx"
  confidence_threshold: 0.5
  nms_threshold: 0.45
  device: "CPU" # CPU, CUDA, NPU, etc.
  classes:
    - person

# Re-identification Configuration
reid:
  feature_size: 128
  similarity_threshold: 0.6 # Cosine similarity threshold
  retention_period: 3600 # How long to remember a person (in seconds)
  max_stored_vectors: 1000 # Maximum number of feature vectors to store

# Logging Configuration
logging:
  local_path: "../logs/local_log.json"
  log_level: "INFO" # DEBUG, INFO, WARNING, ERROR
  retention_days: 7

# Firebase Configuration
firebase:
  enabled: true
  config_path: "../firebase/firebase_config.json"
  database_url: "https://manta-xxxxx.firebaseio.com"
  path_prefix: "cameras"
  retry_interval: 60 # Seconds between retries when offline
  batch_size: 10 # Number of logs to send in one batch

# n8n Configuration
n8n:
  webhook_url: "http://your-n8n-instance:5678/webhook/manta"
  notify_events:
    - new_person
    - offline_mode
    - error
```

### Configuration Parameters Explained

#### Camera Configuration

- `id`: Unique identifier for this camera
- `source`: Camera input source (0 for default webcam, RTSP URL, or file path)
- `resolution`: Frame width and height
- `fps`: Target frames per second

#### Detection Configuration

- `model_path`: Path to YOLO ONNX model
- `confidence_threshold`: Minimum confidence for valid detections
- `nms_threshold`: Non-maximum suppression threshold
- `device`: Hardware to use for inference (CPU, CUDA, NPU)
- `classes`: Object classes to detect (usually just "person")

#### Re-identification Configuration

- `feature_size`: Size of feature vectors
- `similarity_threshold`: Threshold for determining if a person is the same
- `retention_period`: How long to remember a person
- `max_stored_vectors`: Limit on stored vectors to prevent memory issues

#### Logging Configuration

- `local_path`: Path to store local logs
- `log_level`: Verbosity of logging
- `retention_days`: How long to keep local logs

#### Firebase Configuration

- `enabled`: Whether to use Firebase
- `config_path`: Path to Firebase service account key
- `database_url`: Firebase Realtime Database URL
- `path_prefix`: Path in database to store data
- `retry_interval`: How often to retry when offline
- `batch_size`: Number of logs to send in one batch

#### n8n Configuration

- `webhook_url`: URL endpoint for n8n webhook
- `notify_events`: Events that trigger notifications

---

## 5. Core Components

### 5.1 Person Detection (`detection.py`)

The detection module uses YOLO (You Only Look Once) in ONNX format to detect people in video frames.

#### Key Features:

- ONNX Runtime for optimized inference
- Support for multiple hardware acceleration options
- Configurable confidence thresholds
- Non-maximum suppression for clean detections

#### Example Usage:

```python
from camera.detection import PersonDetector

# Initialize detector
detector = PersonDetector(
    model_path="models/yolov8n.onnx",
    confidence_threshold=0.5,
    device="CPU"
)

# Detect people in a frame
detections = detector.detect(frame)

# Process detections
for x1, y1, x2, y2, confidence, class_id in detections:
    # Do something with each detected person
    person_img = frame[int(y1):int(y2), int(x1):int(x2)]
```

### 5.2 Re-Identification (`reid.py`)

The re-identification module extracts feature vectors from detected people and compares them against previously seen people to avoid double-counting.

#### Key Features:

- Feature vector extraction
- Cosine similarity comparison
- Time-based retention of known people
- Hash-based identification

#### Example Usage:

```python
from camera.reid import PersonReIdentifier

# Initialize re-identifier
reidentifier = PersonReIdentifier(
    feature_size=128,
    similarity_threshold=0.6,
    retention_period=3600  # 1 hour
)

# Process a detected person
is_new_person, person_hash = reidentifier.process(person_img)

if is_new_person:
    print(f"New person detected with hash: {person_hash}")
```

### 5.3 Activity Logger (`logger.py`)

The logger module handles local storage of detection events and system logs.

#### Key Features:

- JSON-based logging
- Configurable log levels
- Automatic log rotation
- Structured event data

#### Example Usage:

```python
from camera.logger import ActivityLogger

# Initialize logger
logger = ActivityLogger(
    local_path="logs/local_log.json",
    camera_id="cam_001",
    log_level="INFO"
)

# Log a detected person
log_entry = {
    "timestamp": "2025-04-11T14:30:22",
    "person_hash": "7d82aef9",
    "camera_id": "cam_001"
}
logger.log_person(log_entry)

# Log system events
logger.info("System started")
logger.error("Camera connection lost")
```

### 5.4 Firebase Uploader (`uploader.py`)

The uploader module synchronizes local logs with Firebase Realtime Database.

#### Key Features:

- Batch uploads for efficiency
- Offline operation with retry
- Configurable sync intervals
- Error handling and recovery

#### Example Usage:

```python
from camera.uploader import FirebaseUploader

# Initialize uploader
uploader = FirebaseUploader(
    config_path="firebase/firebase_config.json",
    database_url="https://manta-xxxxx.firebaseio.com",
    path_prefix="cameras",
    camera_id="cam_001"
)

# Upload a log entry
log_entry = {
    "timestamp": "2025-04-11T14:30:22",
    "person_hash": "7d82aef9",
    "camera_id": "cam_001"
}
uploader.upload_log(log_entry)

# Force sync all pending logs
uploader.flush()
```

---

## 6. Firebase Integration

MANTA uses Firebase Realtime Database to store detection logs and provide real-time access to data from multiple cameras.

### Database Structure

```
"cameras": {
  "cam_001": {
    "logs": {
      "log_id_001": {
        "timestamp": "2025-04-11T14:30:22",
        "person_hash": "7d82aef9"
      },
      "log_id_002": {
        "timestamp": "2025-04-11T14:31:45",
        "person_hash": "3fa8c6d2"
      }
    },
    "status": {
      "last_seen": "2025-04-11T14:31:45",
      "is_online": true,
      "version": "1.1"
    }
  },
  "cam_002": {
    ...
  }
}
```

### Setup Instructions

1. **Create Firebase Project**:

   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project or use an existing one

2. **Set Up Realtime Database**:

   - Navigate to "Realtime Database" in the Firebase console
   - Click "Create Database"
   - Start in test mode or define security rules

3. **Generate Service Account Key**:

   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file as `firebase/firebase_config.json`

4. **Configure MANTA**:
   - Update `config.yaml` with your Firebase database URL
   - Ensure the `firebase.enabled` setting is set to `true`

### Security Considerations

- The default Firebase setup uses a service account with full read/write access
- For production, consider implementing custom security rules
- Example security rules:

```json
{
  "rules": {
    "cameras": {
      "$camera_id": {
        ".read": "auth != null",
        ".write": "auth != null && auth.uid === 'service-account'"
      }
    }
  }
}
```

---

## 7. n8n Automation

MANTA integrates with n8n to provide workflow automation for notifications, data processing, and backup tasks.

### Setup n8n

1. **Start n8n Container**:

   ```bash
   cd n8n
   docker-compose up -d
   ```

2. **Access n8n Interface**:
   - Open `http://your-server-ip:5678` in a browser
   - Log in with credentials from `docker-compose.yml`

### Example Workflows

#### 1. New Person Notification Workflow

This workflow sends a notification to LINE or Telegram when a new person is detected.

1. In n8n, create a new workflow
2. Add a "Webhook" node as trigger
3. Configure the webhook to match your `n8n.webhook_url` setting
4. Add a "Firebase" node to listen for new logs
5. Add a "LINE" or "Telegram" node to send notifications
6. Connect nodes and activate the workflow

#### 2. Daily Summary Workflow

This workflow generates a daily summary of people counts and sends it to Google Sheets.

1. Create a new workflow
2. Add a "Cron" node set to run daily
3. Add a "Firebase" node to retrieve daily logs
4. Add a "Function" node to process and summarize data
5. Add a "Google Sheets" node to update a spreadsheet
6. Connect nodes and activate the workflow

#### 3. Backup Workflow

This workflow backs up Firebase data to Google Drive.

1. Create a new workflow
2. Add a "Cron" node set to run weekly
3. Add a "Firebase" node to export data
4. Add a "Google Drive" node to save the backup file
5. Connect nodes and activate the workflow

### n8n Configuration File

The n8n setup is defined in the `n8n/docker-compose.yml` file:

```yaml
version: "3.8"

services:
  n8n:
    image: n8nio/n8n
    platform: linux/arm64 # for Raspberry Pi
    restart: always
    ports:
      - 5678:5678
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=securepassword
      - WEBHOOK_URL=https://your-public-url.com/
      - GENERIC_TIMEZONE=Asia/Bangkok
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
```

---

## 8. Running & Deploying

### Development Mode

For testing and development:

```bash
# Run with debug output
python camera/main.py --debug

# Run without uploading to Firebase
python camera/main.py --debug --no-upload

# Run with a specific config file
python camera/main.py --config my_custom_config.yaml
```

### Production Deployment

For production environments, set up MANTA as a system service:

1. **Create a systemd service file**:

   ```bash
   sudo nano /etc/systemd/system/manta.service
   ```

2. **Add the following configuration**:

   ```
   [Unit]
   Description=MANTA People Counter
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /path/to/manta/camera/main.py --config /path/to/manta/config/config.yaml
   WorkingDirectory=/path/to/manta
   Restart=always
   User=pi  # or your username

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service**:

   ```bash
   sudo systemctl enable manta.service
   sudo systemctl start manta.service
   ```

4. **Check service status**:
   ```bash
   sudo systemctl status manta.service
   ```

### Updating the System

To update MANTA to a new version:

```bash
# Stop the service
sudo systemctl stop manta.service

# Pull latest changes
cd /path/to/manta
git pull

# Update dependencies
pip install -r models/requirements.txt

# Restart the service
sudo systemctl start manta.service
```

---

## 9. Troubleshooting

### Common Issues and Solutions

#### Camera Connection Problems

**Issue**: Cannot connect to camera or camera feed is blank.

**Solutions**:

- Check camera connections
- Verify camera permissions: `sudo usermod -a -G video $USER`
- Try different `source` values in config.yaml
- Install v4l-utils and check available devices: `v4l2-ctl --list-devices`

#### YOLO Model Errors

**Issue**: "Error loading YOLO model" or inference failures.

**Solutions**:

- Verify the model file exists at the specified path
- Try downloading the model again
- Check ONNX Runtime installation
- Reduce resolution if running on low-memory devices

#### Firebase Connection Issues

**Issue**: Cannot connect to Firebase or upload errors.

**Solutions**:

- Check internet connection
- Verify Firebase config JSON is valid
- Ensure database URL is correct
- Check Firebase project permissions
- Look for quota limits or restrictions

#### Performance Problems

**Issue**: System running slowly or dropping frames.

**Solutions**:

- Reduce resolution in config
- Lower the target FPS
- Use hardware acceleration if available
- Increase confidence threshold to reduce detections
- Check for CPU/memory bottlenecks: `htop`

### Accessing Logs

```bash
# View system service logs
sudo journalctl -u manta.service

# View recent application logs
tail -n 100 /path/to/manta/logs/local_log.json

# Monitor logs in real-time
tail -f /path/to/manta/logs/local_log.json
```

### Diagnostic Commands

```bash
# Check Python version
python3 --version

# Verify ONNX Runtime installation
python3 -c "import onnxruntime as ort; print(ort.get_device())"

# Test camera access
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera working:', cap.isOpened()); cap.release()"

# Check Firebase connection
python3 -c "import firebase_admin; from firebase_admin import credentials, db; cred = credentials.Certificate('firebase/firebase_config.json'); firebase_admin.initialize_app(cred, {'databaseURL': 'https://manta-xxxxx.firebaseio.com'}); print('Firebase connected')"
```

---

## 10. Development Guide

### Project Structure

```
manta/
├── camera/
│   ├── main.py                # Main application
│   ├── detection.py           # YOLO detection
│   ├── reid.py                # Re-identification
│   ├── logger.py              # Local logging
│   └── uploader.py            # Firebase upload
│
├── models/
│   ├── yolov8n.onnx           # YOLO model
│   └── requirements.txt       # Dependencies
│
├── dataset/                   # For training (optional)
│
├── n8n/
│   ├── docker-compose.yml     # n8n setup
│   └── workflows/             # Saved workflows
│
├── firebase/
│   ├── firebase_config.json   # Firebase credentials
│   └── firebase_utils.py      # Firebase helper functions
│
├── utils/
│   ├── camera_utils.py        # Camera helpers
│   └── vector_utils.py        # Vector math utilities
│
├── config/
│   └── config.yaml            # Configuration
│
├── logs/
│   └── local_log.json         # Local log storage
```

### Adding New Features

#### 1. Adding a New Detector

To add a different detection model:

1. Add the model file to `models/`
2. Create a new detector class in `detection.py` or extend the existing one
3. Update the configuration to support the new model
4. Modify `main.py` to use the new detector when specified

#### 2. Extending Re-Identification

To improve re-identification:

1. Add a specialized feature extractor model to `models/`
2. Update `reid.py` to use the new model
3. Consider adding clustering algorithms for better matching
4. Update thresholds in configuration

#### 3. Adding Analytics

To add analytics features:

1. Create a new module `analytics.py` in the `camera/` directory
2. Implement functions for processing detection data
3. Update `main.py` to call the analytics functions
4. Add configuration options for analytics
5. Create n8n workflows to visualize the analytics data

### Coding Standards

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Use type hints where appropriate
- Write unit tests for new functionality
- Use consistent error handling

### Testing

```bash
# Run unit tests
python -m unittest discover tests

# Run a specific test file
python -m unittest tests.test_detection

# Test with coverage
python -m pytest --cov=camera
```

---

## 11. API Reference

### Main Module

```python
class MANTASystem:
    """Main system class that coordinates all components."""

    def __init__(self, config_path=None, debug=False, no_upload=False):
        """Initialize the system with configuration."""

    def run(self):
        """Run the system in a continuous loop."""

    def stop(self):
        """Stop the system and clean up resources."""
```

### Detection Module

```python
class PersonDetector:
    """Class for detecting people in frames using YOLO."""

    def __init__(self, model_path, confidence_threshold=0.5,
                 nms_threshold=0.45, device="CPU", classes=None):
        """Initialize the detector with model and settings."""

    def detect(self, frame):
        """
        Detect people in a frame.

        Args:
            frame: OpenCV image frame

        Returns:
            List of detections [x1, y1, x2, y2, confidence, class_id]
        """
```

### Re-Identification Module

```python
class PersonReIdentifier:
    """Class for re-identifying people to avoid double-counting."""

    def __init__(self, feature_size=128, similarity_threshold=0.6,
                 retention_period=3600, max_stored_vectors=1000):
        """Initialize with feature settings."""

    def process(self, person_img):
        """
        Process a person image and determine if it's a new person.

        Args:
            person_img: Cropped image of a person

        Returns:
            Tuple (is_new_person, person_hash)
        """
```

### Logger Module

```python
class ActivityLogger:
    """Class for logging detection events and system logs."""

    def __init__(self, local_path, camera_id, log_level="INFO",
                 retention_days=7):
        """Initialize with log settings."""

    def log_person(self, log_entry):
        """Log a detected person."""

    def info(self, message):
        """Log an info message."""

    def error(self, message):
        """Log an error message."""

    def debug(self, message):
        """Log a debug message."""
```

### Uploader Module

```python
class FirebaseUploader:
    """Class for uploading logs to Firebase Realtime Database."""

    def __init__(self, config_path, database_url, path_prefix,
                 camera_id, retry_interval=60, batch_size=10):
        """Initialize with Firebase settings."""

    def upload_log(self, log_entry):
        """Upload a log entry to Firebase."""

    def flush(self):
        """Force upload of all pending logs."""
```

---

## 12. Contributing

MANTA is an open-source project and welcomes contributions from the community.

### How to Contribute

1. **Fork the Repository**:

   - Create a personal fork of the project on GitHub

2. **Create a Branch**:

   - Make a branch for your feature or bugfix: `git checkout -b feature/new-feature`

3. **Make Changes**:

   - Implement your changes following the coding standards
   - Update documentation as needed
   - Add tests for new functionality

4. **Test Your Changes**:

   - Run the test suite to ensure all tests pass
   - Test on actual hardware if possible

5. **Submit a Pull Request**:
   - Push your changes to your fork: `git push origin feature/new-feature`
   - Submit a pull request to the main repository
   - Describe your changes and why they should be included

### Areas for Contribution

- Improving Re-ID algorithms for better accuracy
- Adding support for new hardware acceleration
- Creating web dashboard for monitoring
- Implementing heatmaps and advanced analytics
- Optimizing performance on low-power devices
- Improving documentation and examples
- Adding internationalization support

### Contact

For questions, suggestions, or discussions:

- GitHub Issues: [project-url]/issues
- Email: dev@manta-system.dev

---

**License**: MIT  
**Copyright**: 2025 MANTA Team

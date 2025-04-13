# MANTA Technical Specification

## System Architecture

MANTA follows a modular architecture designed for flexibility and extensibility. This document outlines the technical details of each component and provides guidance for developers.

### Architecture Overview

```
┌─────────────────┐       ┌─────────────────┐      ┌─────────────────┐
│  Video Source   │──────▶│  Detection      │─────▶│  ReID           │
│  (Camera/File)  │       │  (YOLO/ONNX)    │      │  (Feature Ext.) │
└─────────────────┘       └─────────────────┘      └─────────────────┘
                                                             │
                                                             ▼
┌─────────────────┐       ┌─────────────────┐      ┌─────────────────┐
│  n8n            │◀──────│  Uploader       │◀─────│  Logger         │
│  (Automation)   │       │  (Firebase)     │      │  (Activity)     │
└─────────────────┘       └─────────────────┘      └─────────────────┘
```

## Core Components

### 1. Video Source Module

**Purpose**: Provides the raw video feed to the system.

**Implementation Details**:

- Uses OpenCV's VideoCapture for camera access
- Supports various input types:
  - Local webcams (index 0, 1, etc.)
  - RTSP streams (rtsp://...)
  - Video files (.mp4, .avi, etc.)
- Configurable resolution and frame rate

**Key Functions**:

- `setup_camera()` in `camera_utils.py`: Initializes the camera with specified parameters
- Frame acquisition in the main loop with error handling and reconnection logic

### 2. Detection Module

**Purpose**: Identifies people in each frame.

**Implementation Details**:

- Uses YOLO (v8 preferred) in ONNX format for efficient inference
- Supports multiple execution providers:
  - CPU (default)
  - CUDA (NVIDIA GPUs)
  - TensorRT (NVIDIA accelerated)
  - NPU support for edge devices
- Configurable parameters for detection confidence and NMS

**Key Classes and Methods**:

- `PersonDetector` class in `detection.py`:
  - `__init__()`: Loads model and configures detection parameters
  - `detect()`: Processes frames and returns bounding boxes
  - `preprocess()`: Prepares frames for model input

**Model Specifications**:

- Input: RGB image resized to model dimensions (e.g., 640x640)
- Output: Tensor containing detection parameters (boxes, scores, classes)
- Format: ONNX (.onnx) with required optimization

### 3. Re-Identification Module

**Purpose**: Creates feature vectors for detected individuals to track them across frames.

**Implementation Details**:

- Feature extraction using a lightweight model (MobileNet-based or similar)
- Cosine similarity for vector comparison
- Configurable similarity threshold and retention period

**Key Classes and Methods**:

- `PersonReIdentifier` class in `reid.py`:
  - `process()`: Main entry point that handles a detected person
  - `_extract_features()`: Creates feature vector from person image
  - `_compare_vectors()`: Compares against known vectors
  - `_clean_old_vectors()`: Removes expired entries

**Technical Approach**:

- Each detected person generates a feature vector (128-dimensional by default)
- Vectors are compared using cosine similarity
- Privacy-preserving: Stores only feature vectors, not images
- Time-based expiration of stored vectors

### 4. Logger Module

**Purpose**: Records activity data for analysis.

**Implementation Details**:

- JSON-based local logging
- Configurable retention policy
- Support for different log levels

**Key Classes and Methods**:

- `ActivityLogger` class in `logger.py`:
  - `log_person()`: Records a person detection event
  - `info()`, `debug()`, `error()`: General logging
  - `clean_old_logs()`: Applies retention policy

**Log Entry Format**:

```json
{
  "timestamp": "2025-04-12T14:30:22.145Z",
  "event_type": "person_detected",
  "camera_id": "cam_001",
  "person_hash": "a1b2c3d4e5f6...",
  "confidence": 0.92
}
```

### 5. Uploader Module

**Purpose**: Synchronizes data with Firebase for cloud storage.

**Implementation Details**:

- Firebase Realtime Database for data storage
- Offline mode with local caching
- Batched uploads for efficiency

**Key Classes and Methods**:

- `FirebaseUploader` class in `uploader.py`:
  - `upload_log()`: Sends an entry to Firebase
  - `flush()`: Forces upload of pending entries
  - `_connect()`: Establishes Firebase connection
  - `_handle_offline()`: Manages offline behavior

**Firebase Data Structure**:

```
manta/
  ├── cameras/
  │   ├── cam_001/
  │   │   ├── status: "online"
  │   │   ├── last_update: "2025-04-12T14:35:10.145Z"
  │   │   └── detections/
  │   │       ├── -NpQr5sT6uVwXyZ: {...}
  │   │       └── -NpQr8dE9fGhIjK: {...}
  │   └── cam_002/
  │       └── ...
  └── stats/
      ├── daily/
      │   └── 2025-04-12: {
      │       "total_detections": 42,
      │       "cameras": {
      │           "cam_001": 28,
      │           "cam_002": 14
      │       }
      │   }
      └── hourly/
          └── ...
```

### 6. n8n Integration

**Purpose**: Enables workflow automation based on detection events.

**Implementation Details**:

- Webhook-based integration
- JSON payloads for event data
- Configurable triggers

**Integration Methods**:

- REST API calls to n8n webhook endpoints
- Event filtering based on configuration

**Sample Webhook Payload**:

```json
{
  "event": "new_person",
  "timestamp": "2025-04-12T14:30:22.145Z",
  "camera_id": "cam_001",
  "count": {
    "total": 42,
    "new": 1
  }
}
```

## Data Flow

1. **Frame Acquisition**:

   - Camera provides raw frames to the main loop
   - Frames are processed at the configured rate

2. **Person Detection**:

   - Each frame is processed by the detection module
   - Detection results include bounding boxes for each person

3. **Re-Identification**:

   - Each detected person is processed by the ReID module
   - Feature vectors are extracted and compared against known vectors
   - New persons are identified based on similarity threshold

4. **Logging**:

   - Detection events are recorded by the logger
   - System status and errors are also logged

5. **Cloud Integration**:

   - If enabled, logs are uploaded to Firebase
   - Upload can be immediate or batched

6. **Workflow Automation**:
   - Configurable events trigger n8n webhooks
   - n8n workflows process the events and take actions

## Configuration Reference

The system is configured through a YAML file with the following structure:

```yaml
# Camera Configuration
camera:
  id: "cam_001" # Unique identifier for this camera
  source: 0 # Camera source (0 for default webcam, URL for RTSP)
  resolution: # Target resolution (may be adjusted based on camera capabilities)
    width: 640
    height: 480
  fps: 15 # Target frame rate

# Detection Configuration
detection:
  model_path: "../models/yolov8n.onnx" # Path to YOLO model
  confidence_threshold: 0.5 # Minimum detection confidence
  nms_threshold: 0.45 # Non-maximum suppression threshold
  device: "CPU" # Execution device (CPU, CUDA, etc.)
  classes: # Classes to detect (COCO dataset)
    - person

# Re-identification Configuration
reid:
  feature_size: 128 # Size of feature vectors
  similarity_threshold: 0.6 # Cosine similarity threshold
  retention_period: 3600 # How long to remember a person (seconds)
  max_stored_vectors: 1000 # Maximum number of vectors to store

# Logging Configuration
logging:
  local_path: "../logs/local_log.json" # Path to log file
  log_level: "INFO" # Log level (DEBUG, INFO, WARNING, ERROR)
  retention_days: 7 # Log retention period (days)

# Firebase Configuration
firebase:
  enabled: true # Enable Firebase integration
  config_path: "../firebase/firebase_config.json" # Firebase credentials
  database_url: "https://manta-xxxxx.firebaseio.com" # Database URL
  path_prefix: "cameras" # Path prefix in database
  retry_interval: 60 # Seconds between retries when offline
  batch_size: 10 # Number of logs to send in one batch

# n8n Configuration
n8n:
  webhook_url: "http://your-n8n-instance:5678/webhook/manta" # n8n webhook
  notify_events: # Events that trigger webhooks
    - new_person
    - offline_mode
    - error
```

## Performance Considerations

### CPU Usage Optimization

- **Frame Rate**: Adjust `fps` to balance detection quality and CPU usage
- **Resolution**: Lower resolution reduces processing time but affects detection quality
- **Model Selection**: Smaller models like YOLOv8n are faster but less accurate

### Memory Management

- **Vector Storage**: Configure `max_stored_vectors` based on expected traffic
- **Log Retention**: Set appropriate `retention_days` to manage disk usage
- **Batched Uploads**: Use `batch_size` to control memory usage during uploads

### Edge Device Deployment

For resource-constrained devices (Raspberry Pi, Jetson Nano, etc.):

1. Use quantized models (INT8) for faster inference
2. Reduce resolution and frame rate
3. Increase detection interval (process every Nth frame)
4. Utilize hardware acceleration when available

## Development Guidelines

### Adding New Features

1. **Module Isolation**: Keep new functionality in appropriate modules
2. **Configuration Integration**: Add new features to config.yaml
3. **Error Handling**: Implement robust error handling and logging
4. **Testing**: Create test scripts for new components

### Code Style

- Follow PEP 8 guidelines for Python code
- Use type hints for function parameters and return values
- Document functions and classes with docstrings
- Use meaningful variable and function names

### Testing Approach

- Unit tests for individual components
- Integration tests for module interactions
- System tests for end-to-end functionality
- Performance benchmarking for optimization

## Deployment Options

### Docker Deployment

A Dockerfile is provided for containerized deployment:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "camera/main.py"]
```

### Multi-Camera Setup

For multiple camera deployments:

1. Create separate configuration files for each camera
2. Use Docker containers for isolation
3. Configure Firebase for centralized data collection
4. Set up n8n for aggregated processing

## Troubleshooting

### Common Issues

1. **Camera Access Problems**:

   - Check camera permissions
   - Verify RTSP URL format and authentication
   - Test camera with `cv2.VideoCapture()` directly

2. **Model Loading Errors**:

   - Ensure model paths are correct
   - Verify ONNX model compatibility
   - Check execution provider availability

3. **Firebase Connection Issues**:
   - Validate credentials in firebase_config.json
   - Check network connectivity
   - Verify database rules allow write access

### Logging and Debugging

- Use `--debug` flag for visual output
- Check logs in the configured log file
- Enable DEBUG level logging for detailed information

## Future Development Roadmap

Planned enhancements for future versions:

1. **Multi-Object Tracking**: Support for tracking multiple object types
2. **Advanced Analytics**: Traffic patterns and heatmap generation
3. **Web Dashboard**: Built-in visualization and management interface
4. **Hardware Acceleration**: Expanded support for NPUs and specialized hardware
5. **Transfer Learning**: Tools for custom model fine-tuning

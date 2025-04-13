#!/bin/bash
# MANTA Installation Script for Raspberry Pi
# This script sets up the MANTA camera system on a Raspberry Pi

echo "=========================================================="
echo "MANTA - Monitoring and Analytics Node for Tracking Activity"
echo "=========================================================="
echo "Installing on Raspberry Pi..."
echo ""

# Exit on error
set -e

# Check if running on Raspberry Pi
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" != "raspbian" && "$ID_LIKE" != *"debian"* ]]; then
        echo "Warning: This doesn't appear to be a Raspberry Pi running Raspbian."
        echo "This script is designed for Raspberry Pi. Continue anyway? (y/n)"
        read -r response
        if [[ "$response" != "y" ]]; then
            echo "Installation cancelled."
            exit 1
        fi
    fi
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p config/
mkdir -p logs/
mkdir -p models/
mkdir -p dataset/images
mkdir -p dataset/labels
mkdir -p firebase/

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
echo "Installing required packages..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-opencv \
    libopencv-dev \
    cmake \
    libatlas-base-dev \
    libjasper-dev \
    libpython3-dev \
    python3-numpy \
    git

# Install PiCamera if on Raspberry Pi
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Installing PiCamera..."
    sudo apt-get install -y python3-picamera
fi

# Install Python packages
echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install -r models/requirements.txt

# Download YOLOv8 model if it doesn't exist
if [ ! -f "models/yolov8n.onnx" ]; then
    echo "Downloading YOLOv8 model..."
    mkdir -p models
    wget -O models/yolov8n.onnx https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.onnx
fi

# Download COCO class names
if [ ! -f "models/coco.names" ]; then
    echo "Downloading COCO class names..."
    wget -O models/coco.names https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names
fi

# Check for camera access
echo "Checking camera access..."
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    # For Raspberry Pi camera
    if ! vcgencmd get_camera | grep -q "detected=1"; then
        echo "Warning: No Raspberry Pi camera detected. Please check your camera connection."
    else
        echo "Raspberry Pi camera detected."
    fi
else
    # For regular webcam
    if [ ! -e /dev/video0 ]; then
        echo "Warning: No webcam detected at /dev/video0."
    else
        echo "Webcam detected."
    fi
fi

# Check for Firebase config
if [ ! -f "firebase/firebase_config.json" ]; then
    echo "Warning: Firebase configuration file not found."
    echo "Please place your Firebase config JSON in firebase/firebase_config.json."
    echo "If you don't have a Firebase account, you can run in local mode."
fi

# Create a default config if it doesn't exist
if [ ! -f "config/config.yaml" ]; then
    echo "Creating default configuration..."
    cat > config/config.yaml << EOL
# MANTA Configuration File
# Version: 1.0

# Camera Configuration
camera:
  id: "cam_001"
  source: 0  # 0 for default webcam, can be a RTSP URL or file path
  resolution:
    width: 640
    height: 480
  fps: 15

# Detection Configuration
detection:
  model_path: "models/yolov8n.onnx"
  confidence_threshold: 0.5
  nms_threshold: 0.45
  device: "CPU"  # CPU, CUDA, NPU, etc.
  classes:
    - person

# Re-identification Configuration
reid:
  feature_size: 128
  similarity_threshold: 0.6  # Cosine similarity threshold for re-identification
  retention_period: 3600  # How long to remember a person (in seconds)
  max_stored_vectors: 1000  # Maximum number of feature vectors to store

# Logging Configuration
logging:
  local_path: "logs/local_log.json"
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  retention_days: 7

# Firebase Configuration
firebase:
  enabled: false
  config_path: "firebase/firebase_config.json"
  database_url: "https://manta-smart-camera-default-rtdb.asia-southeast1.firebasedatabase.app"
  path_prefix: "cameras"
  retry_interval: 60  # Seconds between retries when offline
  batch_size: 10  # Number of logs to send in one batch
EOL
fi

echo ""
echo "Installation completed!"
echo ""
echo "To run MANTA, use:"
echo "python3 camera/main.py"
echo ""
echo "Optional arguments:"
echo "  --config <path>   : Use a custom config file"
echo "  --debug           : Enable debug mode"
echo "  --no-upload       : Disable uploading to Firebase"
echo ""
echo "For more information, see the README.md file."
echo "=========================================================="
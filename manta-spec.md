# MANTA - Monitoring and Analytics Node for Tracking Activity

## Project Overview

MANTA is a people detection and tracking system that can be deployed on Raspberry Pi devices. The system uses computer vision to detect people, track them across frames, and log activity data for analytics purposes.

## Key Components

### Hardware Requirements
- Raspberry Pi 4 (min 2GB RAM) or newer
- Raspberry Pi Camera Module or USB webcam
- Power supply
- (Optional) Network connectivity for cloud uploads

### Software Architecture
The system is built with a modular architecture:

1. **Camera Module**: Handles video capture using Raspberry Pi camera or USB webcam
2. **Detection Module**: Uses a lightweight YOLO model to detect people in frames
3. **Re-identification Module**: Matches detected people across frames using feature vectors
4. **Logging Module**: Maintains local logs of detected activity
5. **Uploader Module**: Sends data to Firebase for cloud storage and analytics

## Installation

The system provides a simple installation script for Raspberry Pi:

```bash
# Clone the repository
git clone https://github.com/BemindTech/bmt-manta-camera.git
cd bmt-manta-camera

# Run the installation script
./scripts/get_started.sh
```

## Configuration

The system is configured via a YAML file in the `config` directory. This allows for customization of:

- Camera properties (resolution, FPS)
- Detection parameters (confidence thresholds)
- Re-identification settings
- Logging options
- Firebase connection settings

## Usage

Basic usage:
```bash
python3 camera/main.py
```

Options:
- `--config`: Use a custom config file
- `--debug`: Enable debug mode with visualization
- `--no-upload`: Disable uploading to Firebase

## Raspberry Pi Specific Features

The system includes special optimizations for Raspberry Pi:

1. **PiCamera Support**: Native integration with the Raspberry Pi camera
2. **Performance Optimizations**: 
   - Frame skipping to maintain processing speed
   - Resolution scaling for better performance
   - Thread-based processing for real-time analytics

3. **Low Power Modes**: Ability to operate with reduced functionality when on battery power

## Data Flow

1. Camera captures video frames
2. Frames are processed to detect people
3. Detected people are assigned IDs through re-identification
4. Activity is logged locally
5. Logs are uploaded to Firebase when connectivity is available

## Integration Options

The system can integrate with:

- Firebase for cloud storage and analytics
- n8n for workflow automation
- Custom webhook endpoints for notifications

## Contributing

See the `CONTRIBUTING.md` file for guidelines on how to contribute to the project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
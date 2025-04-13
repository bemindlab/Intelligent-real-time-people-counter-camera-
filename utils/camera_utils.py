#!/usr/bin/env python3
"""
ฟังก์ชันอรรถประโยชน์สำหรับการตั้งค่าและการใช้งานกล้อง
(Utility functions for camera setup and operations)

รองรับทั้งกล้อง Raspberry Pi Camera Module และกล้อง USB แบบทั่วไป
เหมาะสำหรับการใช้งานกับ Raspberry Pi 5 Model B
"""

import cv2
from typing import Union, Tuple, Optional

def setup_camera(source: Union[int, str], width: int = 640, height: int = 480, fps: int = 30) -> cv2.VideoCapture:
    """
    Set up the camera with the given parameters.
    
    Args:
        source: Camera source (0 for default webcam, or URL/file path)
        width: Desired frame width
        height: Desired frame height
        fps: Desired frames per second
        
    Returns:
        Configured cv2.VideoCapture object
    """
    camera = cv2.VideoCapture(source)
    
    # Check if camera opened successfully
    if not camera.isOpened():
        raise RuntimeError(f"Error: Could not open camera source {source}")
    
    # Set properties
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    camera.set(cv2.CAP_PROP_FPS, fps)
    
    return camera

def setup_raspberry_pi_camera(resolution: Tuple[int, int] = (640, 480), 
                             framerate: int = 30, 
                             sensor_mode: int = 0,
                             rotation: int = 0) -> 'PiCamera':
    """
    Set up the Raspberry Pi camera with the given parameters.
    
    Args:
        resolution: Tuple of (width, height)
        framerate: Frames per second
        sensor_mode: Sensor mode (0 for auto)
        rotation: Camera rotation in degrees (0, 90, 180, or 270)
        
    Returns:
        Configured PiCamera object
    """
    try:
        from picamera import PiCamera
        import time
        
        # Initialize camera
        camera = PiCamera()
        camera.resolution = resolution
        camera.framerate = framerate
        camera.sensor_mode = sensor_mode
        camera.rotation = rotation
        
        # Allow camera to warm up
        time.sleep(2)
        
        return camera
    except ImportError:
        raise ImportError("picamera module not found. Please install it with: pip install picamera")

def get_pi_camera_frame(camera: 'PiCamera', format: str = 'rgb') -> Optional[bytes]:
    """
    Capture a frame from the Raspberry Pi camera.
    
    Args:
        camera: PiCamera instance
        format: Output format ('rgb', 'bgr', 'yuv', etc.)
        
    Returns:
        Frame data in the specified format
    """
    try:
        import io
        import numpy as np
        from PIL import Image
        
        # Create in-memory stream
        stream = io.BytesIO()
        
        # Capture frame to stream
        camera.capture(stream, format='jpeg', use_video_port=True)
        
        # Convert to numpy array
        stream.seek(0)
        data = np.frombuffer(stream.getvalue(), dtype=np.uint8)
        
        # Decode the image
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        
        # Convert to requested format if not BGR (OpenCV default)
        if format.lower() == 'rgb':
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return image
    except Exception as e:
        print(f"Error capturing frame: {e}")
        return None

def create_pi_camera_video_stream(resolution: Tuple[int, int] = (640, 480), 
                                framerate: int = 30) -> Tuple['PiCamera', 'PiRGBArray']:
    """
    Create a video stream using the Raspberry Pi camera.
    
    Args:
        resolution: Tuple of (width, height)
        framerate: Frames per second
        
    Returns:
        Tuple of (camera, rawCapture) for streaming
    """
    try:
        from picamera import PiCamera
        from picamera.array import PiRGBArray
        import time
        
        # Initialize camera
        camera = PiCamera()
        camera.resolution = resolution
        camera.framerate = framerate
        
        # Initialize the buffer for camera captures
        raw_capture = PiRGBArray(camera, size=resolution)
        
        # Allow camera to warm up
        time.sleep(2)
        
        return camera, raw_capture
    except ImportError:
        raise ImportError("picamera module not found. Please install it with: pip install picamera[array]")

#!/usr/bin/env python3
"""
สคริปต์ทดสอบเฉพาะสำหรับฟังก์ชันการทำงานของกล้อง Raspberry Pi
(Test script specifically for Raspberry Pi camera functionality)

สคริปต์นี้ให้การทดสอบเพิ่มเติมสำหรับคุณสมบัติเฉพาะของ Raspberry Pi 5
รองรับทั้งการบันทึกภาพนิ่งและวิดีโอด้วยโมดูลกล้อง Pi Camera
"""

import os
import sys
import time
import argparse
import numpy as np
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_basic_picamera():
    """
    Test basic PiCamera functionality without OpenCV dependency.
    """
    print("\nTesting basic PiCamera functionality")
    
    try:
        # Try to import picamera
        try:
            from picamera import PiCamera
        except ImportError:
            print("❌ PiCamera module not available")
            print("   Install with: pip install picamera")
            return False
        
        # Initialize camera
        camera = PiCamera()
        print(f"✅ Pi Camera initialized successfully")
        print(f"   Default resolution: {camera.resolution}")
        print(f"   Default framerate: {camera.framerate}")
        
        # Set resolution and framerate
        camera.resolution = (640, 480)
        camera.framerate = 30
        print(f"   New resolution: {camera.resolution}")
        print(f"   New framerate: {camera.framerate}")
        
        # Capture a still image
        output_path = "picamera_test.jpg"
        print(f"Capturing still image to {output_path}...")
        
        # Allow camera to warm up
        time.sleep(2)
        
        # Capture image
        camera.capture(output_path)
        
        # Check if file was created
        if os.path.exists(output_path):
            print(f"✅ Image captured successfully: {output_path}")
        else:
            print(f"❌ Failed to capture image")
            
        # Clean up
        camera.close()
        
        return os.path.exists(output_path)
    
    except Exception as e:
        print(f"❌ Error testing basic PiCamera: {e}")
        return False

def test_picamera_recording(duration=5):
    """
    Test video recording with PiCamera.
    
    Args:
        duration: Recording duration in seconds
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\nTesting PiCamera video recording ({duration} seconds)")
    
    try:
        # Try to import picamera
        try:
            from picamera import PiCamera
        except ImportError:
            print("❌ PiCamera module not available")
            print("   Install with: pip install picamera")
            return False
        
        # Initialize camera
        camera = PiCamera()
        camera.resolution = (640, 480)
        camera.framerate = 30
        print(f"✅ Pi Camera initialized for recording")
        
        # Setup output file
        output_path = "picamera_video.h264"
        print(f"Recording {duration} second video to {output_path}...")
        
        # Allow camera to warm up
        time.sleep(2)
        
        # Start recording
        camera.start_recording(output_path)
        
        # Record for specified duration
        camera.wait_recording(duration)
        
        # Stop recording
        camera.stop_recording()
        
        # Clean up
        camera.close()
        
        # Check if file was created and has data
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"✅ Video recorded successfully: {output_path}")
            print(f"   File size: {os.path.getsize(output_path) / 1024:.2f} KB")
            return True
        else:
            print(f"❌ Failed to record video or file is empty")
            return False
    
    except Exception as e:
        print(f"❌ Error testing PiCamera recording: {e}")
        return False

def test_picamera_advanced():
    """
    Test advanced PiCamera features.
    
    Returns:
        True if successful, False otherwise
    """
    print("\nTesting advanced PiCamera features")
    
    try:
        # Try to import picamera
        try:
            from picamera import PiCamera
            import picamera.array
        except ImportError:
            print("❌ PiCamera module not available")
            print("   Install with: pip install picamera[array]")
            return False
        
        # Initialize camera
        camera = PiCamera()
        camera.resolution = (640, 480)
        camera.framerate = 30
        print(f"✅ Pi Camera initialized for advanced testing")
        
        # Allow camera to warm up
        time.sleep(2)
        
        # Test camera modes
        print("Testing camera modes:")
        
        # Test resolution change
        test_resolutions = [(640, 480), (1280, 720), (1920, 1080)]
        for res in test_resolutions:
            try:
                camera.resolution = res
                time.sleep(1)  # Allow time to change
                print(f"   Resolution {res}: ✅")
            except Exception as e:
                print(f"   Resolution {res}: ❌ - {e}")
        
        # Test framerate change
        test_framerates = [15, 30, 60]
        for fps in test_framerates:
            try:
                camera.framerate = fps
                time.sleep(1)  # Allow time to change
                print(f"   Framerate {fps}: ✅")
            except Exception as e:
                print(f"   Framerate {fps}: ❌ - {e}")
        
        # Test exposure modes
        test_exposure_modes = ['auto', 'night', 'sports']
        for mode in test_exposure_modes:
            try:
                camera.exposure_mode = mode
                time.sleep(1)  # Allow time to change
                print(f"   Exposure mode '{mode}': ✅")
            except Exception as e:
                print(f"   Exposure mode '{mode}': ❌ - {e}")
        
        # Test direct array capture
        try:
            with picamera.array.PiRGBArray(camera) as output:
                camera.capture(output, 'rgb')
                print(f"   Direct array capture: ✅")
                print(f"     Array shape: {output.array.shape}")
                print(f"     Array dtype: {output.array.dtype}")
        except Exception as e:
            print(f"   Direct array capture: ❌ - {e}")
        
        # Clean up
        camera.close()
        
        return True
    
    except Exception as e:
        print(f"❌ Error testing advanced PiCamera features: {e}")
        return False

def test_picamera_stream():
    """
    Test PiCamera streaming mode.
    
    Returns:
        True if successful, False otherwise
    """
    print("\nTesting PiCamera streaming")
    
    try:
        # Try to import picamera
        try:
            from picamera import PiCamera
            from picamera.array import PiRGBArray
        except ImportError:
            print("❌ PiCamera module not available")
            print("   Install with: pip install picamera[array]")
            return False
        
        # Initialize camera
        camera = PiCamera()
        camera.resolution = (640, 480)
        camera.framerate = 30
        print(f"✅ Pi Camera initialized for streaming")
        
        # Initialize the buffer
        raw_capture = PiRGBArray(camera, size=(640, 480))
        
        # Allow camera to warm up
        time.sleep(2)
        
        # Stream frames
        stream_count = 10
        print(f"Streaming {stream_count} frames...")
        
        frame_count = 0
        start_time = time.time()
        
        # Capture frames from the camera
        for frame in camera.capture_continuous(raw_capture, format="rgb", use_video_port=True):
            # Get the numpy array
            image = frame.array
            
            frame_count += 1
            print(f"   Frame {frame_count}: {image.shape} - dtype: {image.dtype}")
            
            # Clear the stream
            raw_capture.truncate(0)
            
            # Break after desired number of frames
            if frame_count >= stream_count:
                break
        
        # Calculate actual FPS
        elapsed_time = time.time() - start_time
        actual_fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        
        print(f"✅ Captured {frame_count} frames in streaming mode")
        print(f"   Actual FPS: {actual_fps:.2f}")
        
        # Clean up
        camera.close()
        
        return frame_count > 0
    
    except Exception as e:
        print(f"❌ Error testing PiCamera streaming: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test Raspberry Pi camera functionality')
    parser.add_argument('--test', type=str, default='all',
                        choices=['all', 'basic', 'recording', 'advanced', 'streaming'],
                        help='Test to run')
    parser.add_argument('--duration', type=int, default=5,
                        help='Duration for recording test in seconds')
    args = parser.parse_args()
    
    print("\n===== Raspberry Pi Camera Test =====\n")
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            if 'Raspberry Pi' in model:
                print(f"✅ Running on {model}")
            else:
                print(f"⚠️ Not running on a Raspberry Pi: {model}")
    except:
        print("⚠️ Could not determine if running on a Raspberry Pi")
    
    # Run requested tests
    success = True
    
    if args.test in ['all', 'basic']:
        success = test_basic_picamera() and success
    
    if args.test in ['all', 'recording']:
        success = test_picamera_recording(args.duration) and success
    
    if args.test in ['all', 'advanced']:
        success = test_picamera_advanced() and success
    
    if args.test in ['all', 'streaming']:
        success = test_picamera_stream() and success
    
    print("\n===== Test Complete =====\n")
    
    if success:
        print("✅ All tests completed successfully")
    else:
        print("❌ Some tests failed")

if __name__ == "__main__":
    main()
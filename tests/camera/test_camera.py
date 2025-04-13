#!/usr/bin/env python3
"""
สคริปต์ทดสอบสำหรับฟังก์ชันการทำงานของกล้องในระบบ MANTA
(Test script for camera functionality in MANTA system)

สคริปต์นี้ทดสอบทั้งเว็บแคมมาตรฐานและกล้อง Raspberry Pi หากมี
เหมาะสำหรับการใช้งานกับ Raspberry Pi 5 Model B
"""

import os
import sys
import time
import argparse
import cv2
import numpy as np
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import camera utilities
from utils.camera_utils import setup_camera, setup_raspberry_pi_camera, get_pi_camera_frame

def test_webcam(source=0, width=640, height=480, fps=30, frames=10, display=True, save_path=None):
    """
    Test webcam functionality using OpenCV.
    
    Args:
        source: Camera source (0 for default webcam, or URL/file path)
        width: Frame width
        height: Frame height
        fps: Frames per second
        frames: Number of frames to capture
        display: Whether to display frames (requires a display)
        save_path: Directory to save test frames
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\nTesting webcam (source: {source}, {width}x{height} @ {fps} fps)")
    
    try:
        # Setup camera
        camera = setup_camera(source, width, height, fps)
        
        if not camera.isOpened():
            print("❌ Failed to open camera")
            return False
        
        # Get actual camera properties
        actual_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = camera.get(cv2.CAP_PROP_FPS)
        
        print(f"✅ Camera opened successfully")
        print(f"   Actual resolution: {actual_width}x{actual_height}")
        print(f"   Actual FPS: {actual_fps}")
        
        # Capture frames
        print(f"Capturing {frames} frames...")
        
        successful_frames = 0
        start_time = time.time()
        
        for i in range(frames):
            success, frame = camera.read()
            
            if not success:
                print(f"❌ Failed to read frame {i+1}")
                continue
            
            successful_frames += 1
            
            # Display frame if requested
            if display:
                cv2.imshow("Webcam Test", frame)
                cv2.waitKey(1)  # Small delay
            
            # Save frame if requested
            if save_path:
                os.makedirs(save_path, exist_ok=True)
                frame_path = os.path.join(save_path, f"webcam_frame_{i+1}.jpg")
                cv2.imwrite(frame_path, frame)
                print(f"   Saved frame to {frame_path}")
        
        # Calculate actual FPS
        elapsed_time = time.time() - start_time
        actual_fps = successful_frames / elapsed_time if elapsed_time > 0 else 0
        
        print(f"✅ Captured {successful_frames}/{frames} frames")
        print(f"   Actual FPS: {actual_fps:.2f}")
        
        # Clean up
        camera.release()
        if display:
            cv2.destroyAllWindows()
        
        return successful_frames > 0
    
    except Exception as e:
        print(f"❌ Error testing webcam: {e}")
        return False

def test_pi_camera(width=640, height=480, fps=30, frames=10, display=True, save_path=None):
    """
    Test Raspberry Pi camera functionality.
    
    Args:
        width: Frame width
        height: Frame height
        fps: Frames per second
        frames: Number of frames to capture
        display: Whether to display frames (requires a display)
        save_path: Directory to save test frames
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\nTesting Raspberry Pi camera ({width}x{height} @ {fps} fps)")
    
    try:
        # Check if PiCamera is available
        try:
            from picamera import PiCamera
            picamera_available = True
        except ImportError:
            print("❌ PiCamera module not available")
            print("   Install with: pip install picamera[array]")
            return False
        
        # Setup Pi camera
        camera = setup_raspberry_pi_camera((width, height), fps)
        print(f"✅ Pi Camera initialized successfully")
        print(f"   Resolution: {camera.resolution}")
        print(f"   Framerate: {camera.framerate}")
        
        # Capture frames
        print(f"Capturing {frames} frames...")
        
        successful_frames = 0
        start_time = time.time()
        
        for i in range(frames):
            # Capture frame
            frame = get_pi_camera_frame(camera)
            
            if frame is None or frame.size == 0:
                print(f"❌ Failed to capture frame {i+1}")
                continue
            
            successful_frames += 1
            
            # Display frame if requested
            if display:
                # Convert RGB to BGR for OpenCV display
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imshow("Pi Camera Test", frame_bgr)
                cv2.waitKey(1)  # Small delay
            
            # Save frame if requested
            if save_path:
                os.makedirs(save_path, exist_ok=True)
                frame_path = os.path.join(save_path, f"picamera_frame_{i+1}.jpg")
                # Convert RGB to BGR for OpenCV imwrite
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(frame_path, frame_bgr)
                print(f"   Saved frame to {frame_path}")
        
        # Calculate actual FPS
        elapsed_time = time.time() - start_time
        actual_fps = successful_frames / elapsed_time if elapsed_time > 0 else 0
        
        print(f"✅ Captured {successful_frames}/{frames} frames")
        print(f"   Actual FPS: {actual_fps:.2f}")
        
        # Clean up
        camera.close()
        if display:
            cv2.destroyAllWindows()
        
        return successful_frames > 0
    
    except Exception as e:
        print(f"❌ Error testing Pi camera: {e}")
        return False

def test_camera_streaming(source=0, width=640, height=480, fps=30, duration=5, display=True):
    """
    Test continuous camera streaming.
    
    Args:
        source: Camera source (0 for default webcam, or URL/file path)
        width: Frame width
        height: Frame height
        fps: Frames per second
        duration: Duration to stream in seconds
        display: Whether to display frames (requires a display)
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\nTesting camera streaming (source: {source}, {width}x{height} @ {fps} fps)")
    print(f"Duration: {duration} seconds")
    
    try:
        # Setup camera
        camera = setup_camera(source, width, height, fps)
        
        if not camera.isOpened():
            print("❌ Failed to open camera")
            return False
        
        # Get actual camera properties
        actual_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        print(f"✅ Camera opened successfully")
        print(f"   Actual resolution: {actual_width}x{actual_height}")
        
        # Stream for the specified duration
        print(f"Streaming for {duration} seconds...")
        
        start_time = time.time()
        frame_count = 0
        
        while (time.time() - start_time) < duration:
            success, frame = camera.read()
            
            if not success:
                print("❌ Failed to read frame")
                continue
            
            frame_count += 1
            
            # Add timestamp to frame
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Add frame counter
            cv2.putText(frame, f"Frame: {frame_count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Display frame if requested
            if display:
                cv2.imshow("Camera Stream", frame)
                
                # Break if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Streaming stopped by user")
                    break
        
        # Calculate actual FPS
        elapsed_time = time.time() - start_time
        actual_fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        
        print(f"✅ Streaming completed")
        print(f"   Frames captured: {frame_count}")
        print(f"   Actual FPS: {actual_fps:.2f}")
        
        # Clean up
        camera.release()
        if display:
            cv2.destroyAllWindows()
        
        return frame_count > 0
    
    except Exception as e:
        print(f"❌ Error testing camera streaming: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test MANTA camera functionality')
    parser.add_argument('--source', type=str, default='0',
                        help='Camera source (0 for default webcam, or URL/file path)')
    parser.add_argument('--width', type=int, default=640,
                        help='Frame width')
    parser.add_argument('--height', type=int, default=480,
                        help='Frame height')
    parser.add_argument('--fps', type=int, default=30,
                        help='Frames per second')
    parser.add_argument('--frames', type=int, default=10,
                        help='Number of frames to capture in basic test')
    parser.add_argument('--duration', type=int, default=5,
                        help='Duration to stream in seconds')
    parser.add_argument('--save', type=str, default=None,
                        help='Directory to save test frames')
    parser.add_argument('--no-display', action='store_true',
                        help='Disable frame display')
    parser.add_argument('--test', type=str, default='all',
                        choices=['all', 'webcam', 'picamera', 'streaming'],
                        help='Test to run')
    args = parser.parse_args()
    
    # Convert source to int if it's a number
    try:
        args.source = int(args.source)
    except ValueError:
        pass  # Keep as string if not a number
    
    print("\n===== MANTA Camera Test =====\n")
    
    # Run requested tests
    if args.test in ['all', 'webcam']:
        test_webcam(args.source, args.width, args.height, args.fps, args.frames, 
                   not args.no_display, args.save)
    
    if args.test in ['all', 'picamera']:
        test_pi_camera(args.width, args.height, args.fps, args.frames, 
                      not args.no_display, args.save)
    
    if args.test in ['all', 'streaming']:
        test_camera_streaming(args.source, args.width, args.height, args.fps, 
                             args.duration, not args.no_display)
    
    print("\n===== Test Complete =====\n")

if __name__ == "__main__":
    main()
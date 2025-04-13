#!/usr/bin/env python3
"""
แทนที่โมดูล picamera สำหรับการทดสอบบน macOS
"""

import sys
import os
import numpy as np
import cv2
from types import ModuleType

# ตรวจสอบว่าเรากำลังทำงานบน macOS หรือไม่
def is_macos():
    return sys.platform == 'darwin'

# แทนที่โมดูล picamera สำหรับ macOS
def patch_picamera():
    if not is_macos():
        return  # ไม่ต้องแทนที่บนระบบปฏิบัติการอื่น
    
    # สร้าง mock module
    mock_picamera = ModuleType('picamera')
    mock_array = ModuleType('picamera.array')
    
    # สร้าง PiCamera class
    class MockPiCamera:
        def __init__(self):
            self.resolution = (640, 480)
            self.framerate = 30
            self.sensor_mode = 0
            self.rotation = 0
            self.exposure_mode = 'auto'
            self._camera = cv2.VideoCapture(0)
            
            if not self._camera.isOpened():
                print("Warning: Could not open webcam, using simulated frames")
                self._use_webcam = False
            else:
                self._use_webcam = True
        
        def capture(self, output, format='jpeg', use_video_port=False):
            if self._use_webcam:
                ret, frame = self._camera.read()
                if not ret:
                    frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
            else:
                # สร้างภาพจำลอง
                frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                # วาดวงกลมสุ่มเพื่อให้แต่ละเฟรมแตกต่างกัน
                for _ in range(10):
                    x = np.random.randint(0, self.resolution[0])
                    y = np.random.randint(0, self.resolution[1])
                    radius = np.random.randint(10, 50)
                    color = tuple(np.random.randint(0, 255, 3).tolist())
                    cv2.circle(frame, (x, y), radius, color, -1)
            
            # จัดการกับ output
            if isinstance(output, str):
                cv2.imwrite(output, frame)
            else:
                output.array = frame
        
        def start_recording(self, output):
            print("[MockPiCamera] Recording started")
        
        def wait_recording(self, duration):
            import time
            print(f"[MockPiCamera] Recording for {duration} seconds")
            time.sleep(duration)
        
        def stop_recording(self):
            print("[MockPiCamera] Recording stopped")
        
        def close(self):
            if hasattr(self, '_camera') and self._camera is not None:
                self._camera.release()
            print("[MockPiCamera] Camera closed")
    
    # สร้าง PiRGBArray class
    class MockPiRGBArray:
        def __init__(self, camera, size=None):
            self.camera = camera
            self.size = size or camera.resolution
            self.array = np.zeros((self.size[1], self.size[0], 3), dtype=np.uint8)
        
        def truncate(self, size=0):
            self.array = np.zeros((self.size[1], self.size[0], 3), dtype=np.uint8)
    
    # ตั้งค่า mock classes
    mock_picamera.PiCamera = MockPiCamera
    mock_array.PiRGBArray = MockPiRGBArray
    
    # ตั้งค่า mock functions สำหรับ capture_continuous
    def mock_capture_continuous(camera, output, format='jpeg', use_video_port=False):
        while True:
            camera.capture(output, format, use_video_port)
            yield output
    
    MockPiCamera.capture_continuous = mock_capture_continuous
    
    # แทนที่โมดูลใน sys.modules
    sys.modules['picamera'] = mock_picamera
    sys.modules['picamera.array'] = mock_array
    mock_picamera.array = mock_array
    
    print("[MacOS] Successfully patched picamera module for testing")
    return mock_picamera

# ใช้งานจริง
if __name__ == '__main__':
    if is_macos():
        patch_picamera()
        
        # ทดสอบการนำเข้า
        from picamera import PiCamera
        from picamera.array import PiRGBArray
        
        camera = PiCamera()
        print(f"ทดสอบกล้องจำลอง: {camera.resolution}, {camera.framerate} fps")
        
        # ทดสอบการจับภาพ
        output_file = 'test_patch.jpg'
        camera.capture(output_file)
        print(f"บันทึกภาพทดสอบไปยัง {output_file}")
        
        camera.close()
    else:
        print("ระบบนี้ไม่ใช่ macOS ไม่จำเป็นต้องใช้การแทนที่")
# คู่มือการทดสอบ MANTA บน macOS
(MANTA Testing Guide on macOS)

## บทนำ

เอกสารนี้อธิบายวิธีการทดสอบระบบ MANTA บน macOS โดยที่ไม่จำเป็นต้องมีอุปกรณ์ Raspberry Pi ใช้สำหรับนักพัฒนาที่ต้องการทดสอบและพัฒนาบนเครื่อง Mac ก่อนที่จะนำไปใช้งานบน Raspberry Pi จริง

## ข้อกำหนดเบื้องต้น

1. **macOS** 11 (Big Sur) หรือใหม่กว่า
2. **Python 3.9** หรือใหม่กว่า
3. **กล้องเว็บแคม** หรือกล้องเสมือน (virtual camera)
4. โคลนโปรเจกต์ MANTA แล้ว

## การติดตั้ง

### 1. สร้างและเปิดใช้งานสภาพแวดล้อมเสมือน

```bash
# สร้างสภาพแวดล้อมเสมือน
python -m venv venv

# เปิดใช้งานบน macOS
source venv/bin/activate
```

### 2. ติดตั้งแพ็กเกจที่จำเป็น

```bash
# ติดตั้งแพ็กเกจหลัก
pip install -r requirements.txt

# ติดตั้งแพ็กเกจสำหรับการพัฒนา
pip install -r requirements-dev.txt

# ติดตั้ง OpenCV
pip install opencv-python

# ติดตั้งแพ็กเกจสำหรับทดสอบบน macOS
pip install pyfakewebcam
pip install mockito
```

## การจำลองอุปกรณ์ Raspberry Pi

บน macOS ไม่สามารถใช้ไลบรารี PiCamera ได้โดยตรง เนื่องจากเป็นไลบรารีเฉพาะสำหรับ Raspberry Pi เราจำเป็นต้องใช้วิธีการจำลองอุปกรณ์ดังนี้:

### วิธี 1: สร้างกล้องเสมือนด้วย Pyfakewebcam

เราสามารถสร้างกล้องเสมือนสำหรับทดสอบได้ดังนี้:

1. เริ่มต้นด้วยการสร้างไฟล์ `macos_camera_mock.py` ในโฟลเดอร์ `tests/mock`:

```python
#!/usr/bin/env python3
"""
จำลองกล้อง Raspberry Pi สำหรับการทดสอบบน macOS
"""

import cv2
import numpy as np
import time

class MockPiCamera:
    """จำลองคลาส PiCamera เพื่อให้ทำงานบน macOS"""
    
    def __init__(self):
        self.resolution = (640, 480)
        self.framerate = 30
        self.sensor_mode = 0
        self.rotation = 0
        self.webcam = cv2.VideoCapture(0)  # ใช้กล้องเว็บแคมจริงบน macOS
        
        if not self.webcam.isOpened():
            print("⚠️ ไม่สามารถเปิดกล้องเว็บแคมได้ ใช้กล้องจำลองแทน")
            self.use_real_camera = False
        else:
            self.use_real_camera = True
        
    def capture(self, output, format='jpeg', use_video_port=False):
        """จำลองการจับภาพ"""
        if self.use_real_camera:
            success, frame = self.webcam.read()
            if success:
                if isinstance(output, str):
                    # บันทึกเป็นไฟล์
                    cv2.imwrite(output, frame)
                else:
                    # ส่งกลับเป็น stream
                    if format.lower() == 'rgb':
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    output.write(cv2.imencode('.jpg', frame)[1].tobytes())
        else:
            # สร้างภาพจำลอง
            img = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
            # เพิ่มเส้นกริดเพื่อให้มองเห็นชัดเจน
            for i in range(0, self.resolution[0], 50):
                cv2.line(img, (i, 0), (i, self.resolution[1]), (0, 255, 0), 1)
            for i in range(0, self.resolution[1], 50):
                cv2.line(img, (0, i), (self.resolution[0], i), (0, 255, 0), 1)
            
            # เพิ่มข้อความลงในภาพ
            cv2.putText(img, f"Mock Pi Camera - {time.strftime('%H:%M:%S')}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if isinstance(output, str):
                cv2.imwrite(output, img)
            else:
                if format.lower() == 'rgb':
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                output.write(cv2.imencode('.jpg', img)[1].tobytes())
    
    def start_recording(self, output):
        """จำลองการเริ่มบันทึกวิดีโอ"""
        print(f"เริ่มการบันทึกวิดีโอไปยัง {output}")
    
    def wait_recording(self, duration):
        """จำลองการรอบันทึกวิดีโอ"""
        print(f"บันทึกวิดีโอเป็นเวลา {duration} วินาที")
        time.sleep(duration)
    
    def stop_recording(self):
        """จำลองการหยุดบันทึกวิดีโอ"""
        print("หยุดการบันทึกวิดีโอ")
    
    def close(self):
        """ปิดกล้อง"""
        if self.use_real_camera:
            self.webcam.release()
        print("ปิดกล้องแล้ว")

class PiRGBArray:
    """จำลองคลาส PiRGBArray"""
    
    def __init__(self, camera, size=None):
        self.camera = camera
        self.size = size or camera.resolution
        self.array = np.zeros((self.size[1], self.size[0], 3), dtype=np.uint8)
    
    def truncate(self, size=0):
        """ล้างข้อมูลในบัฟเฟอร์"""
        self.array = np.zeros((self.size[1], self.size[0], 3), dtype=np.uint8)

# ตั้งค่าฟังก์ชันช่วยเหลือ
def mock_picamera_import():
    """ฟังก์ชันสำหรับแทนที่การนำเข้า picamera"""
    import sys
    from types import ModuleType
    
    # สร้างโมดูลจำลอง
    picamera_module = ModuleType('picamera')
    picamera_module.PiCamera = MockPiCamera
    
    # สร้างโมดูลย่อย array
    array_module = ModuleType('array')
    array_module.PiRGBArray = PiRGBArray
    picamera_module.array = array_module
    
    # เพิ่มโมดูลเข้าไปใน sys.modules
    sys.modules['picamera'] = picamera_module
    sys.modules['picamera.array'] = array_module
    
    return picamera_module

# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    # จำลองการนำเข้าโมดูล picamera
    mock_picamera = mock_picamera_import()
    
    # สร้างอินสแตนซ์ของกล้องจำลอง
    camera = mock_picamera.PiCamera()
    print(f"กล้องจำลอง: {camera.resolution}, {camera.framerate} fps")
    
    # จับภาพทดสอบ
    camera.capture('test_mock.jpg')
    print("บันทึกภาพทดสอบไปยัง test_mock.jpg")
    
    # ทดสอบการบันทึกวิดีโอ
    camera.start_recording('test_mock.h264')
    camera.wait_recording(2)
    camera.stop_recording()
    
    # ปิดกล้อง
    camera.close()
```

### วิธี 2: ใช้การแทนที่ระดับโมดูล (Monkey Patching)

เราสามารถแทนที่ module `picamera` ที่จะถูกนำเข้าโดยใช้ monkey patching ดังนี้:

1. สร้างไฟล์ `patch_picamera.py` ในโฟลเดอร์ `tests/mock`:

```python
#!/usr/bin/env python3
"""
แทนที่โมดูล picamera สำหรับการทดสอบบน macOS
"""

import sys
import os
import numpy as np
import cv2
from unittest.mock import MagicMock

# ตรวจสอบว่าเรากำลังทำงานบน macOS หรือไม่
def is_macos():
    return sys.platform == 'darwin'

# แทนที่โมดูล picamera สำหรับ macOS
def patch_picamera():
    if not is_macos():
        return  # ไม่ต้องแทนที่บนระบบปฏิบัติการอื่น
    
    from types import ModuleType
    
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
```

## วิธีการรัน MANTA Tests บน macOS

### ขั้นตอนที่ 1: อัปเดตไฟล์ทดสอบ

ก่อนรันการทดสอบ เราต้องปรับปรุงไฟล์ทดสอบให้รองรับการทำงานบน macOS:

1. สร้างไฟล์ `macos_test_helper.py` ใน `tests/` ดังนี้:

```python
#!/usr/bin/env python3
"""
Helper script for running MANTA tests on macOS
"""

import sys
import os

def setup_macos_testing():
    """Setup environment for macOS testing"""
    
    # Check if running on macOS
    if sys.platform != 'darwin':
        return False
    
    # Get the project root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Add the mock directory to path
    mock_dir = os.path.join(root_dir, 'tests', 'mock')
    if not os.path.exists(mock_dir):
        os.makedirs(mock_dir)
    
    # Add the root directory to path
    sys.path.insert(0, root_dir)
    
    # Import the patch module (create the file if it doesn't exist)
    patch_file = os.path.join(mock_dir, 'patch_picamera.py')
    
    if not os.path.exists(patch_file):
        print(f"Creating patch file at {patch_file}")
        with open(patch_file, 'w') as f:
            f.write("""#!/usr/bin/env python3
\"\"\"
Patches the picamera module for testing on macOS
\"\"\"

import sys
import numpy as np
import cv2
from types import ModuleType

def patch_picamera():
    \"\"\"Patch the picamera module for macOS\"\"\"
    
    # Create mock modules
    mock_picamera = ModuleType('picamera')
    mock_array = ModuleType('picamera.array')
    
    # Create mock PiCamera class
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
                # Create a simulated frame
                frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                # Draw some random shapes to make each frame different
                for _ in range(10):
                    x = np.random.randint(0, self.resolution[0])
                    y = np.random.randint(0, self.resolution[1])
                    radius = np.random.randint(10, 50)
                    color = tuple(np.random.randint(0, 255, 3).tolist())
                    cv2.circle(frame, (x, y), radius, color, -1)
            
            # Handle the output
            if isinstance(output, str):
                cv2.imwrite(output, frame)
            else:
                output.array = frame
        
        def start_recording(self, output):
            print("[MockPiCamera] Recording started")
        
        def wait_recording(self, duration):
            import time
            time.sleep(duration)
        
        def stop_recording(self):
            print("[MockPiCamera] Recording stopped")
        
        def close(self):
            if hasattr(self, '_camera') and self._camera is not None:
                self._camera.release()
    
    # Create mock PiRGBArray class
    class MockPiRGBArray:
        def __init__(self, camera, size=None):
            self.camera = camera
            self.size = size or camera.resolution
            self.array = np.zeros((self.size[1], self.size[0], 3), dtype=np.uint8)
        
        def truncate(self, size=0):
            self.array = np.zeros((self.size[1], self.size[0], 3), dtype=np.uint8)
    
    # Setup mock classes
    mock_picamera.PiCamera = MockPiCamera
    mock_array.PiRGBArray = MockPiRGBArray
    
    # Setup mock continuous capture
    def mock_capture_continuous(camera, output, format='jpeg', use_video_port=False):
        while True:
            camera.capture(output, format, use_video_port)
            yield output
    
    MockPiCamera.capture_continuous = mock_capture_continuous
    
    # Replace modules in sys.modules
    sys.modules['picamera'] = mock_picamera
    sys.modules['picamera.array'] = mock_array
    mock_picamera.array = mock_array
    
    print("[MacOS] Patched picamera module for testing")
    return mock_picamera

# Patch picamera if this file is imported
patch_picamera()
""")
    
    # Import the patch module
    sys.path.insert(0, mock_dir)
    
    try:
        from patch_picamera import patch_picamera
        patch_picamera()
        print("✅ macOS test environment setup complete")
        return True
    except Exception as e:
        print(f"❌ Error setting up macOS test environment: {e}")
        return False

if __name__ == "__main__":
    setup_macos_testing()
```

### ขั้นตอนที่ 2: อัปเดตสคริปต์รันการทดสอบ

สร้างสคริปต์ `run_tests_macos.py` ในโฟลเดอร์ `tests/`:

```python
#!/usr/bin/env python3
"""
Script to run MANTA tests on macOS
"""

import os
import sys
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the macOS test helper
from tests.macos_test_helper import setup_macos_testing

def run_tests():
    """Run the MANTA tests on macOS"""
    
    # Setup macOS testing environment
    if not setup_macos_testing():
        print("❌ Failed to setup macOS test environment")
        return False
    
    print("\n===== Running MANTA Tests on macOS =====\n")
    
    # Run the camera tests
    camera_tests = [
        ["python", "tests/camera/test_camera.py", "--test", "webcam", "--no-display"],
        ["python", "tests/camera/test_camera.py", "--test", "streaming", "--duration", "2", "--no-display"]
    ]
    
    for cmd in camera_tests:
        print(f"\nRunning: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"❌ Test failed: {' '.join(cmd)}")
            return False
    
    print("\n✅ All tests completed successfully")
    return True

if __name__ == "__main__":
    run_tests()
```

### ขั้นตอนที่ 3: รันการทดสอบ

รันการทดสอบโดยใช้คำสั่งต่อไปนี้:

```bash
# ไปที่โฟลเดอร์โปรเจกต์
cd /path/to/bmt-manta-camera

# เปิดใช้งานสภาพแวดล้อมเสมือน
source venv/bin/activate

# รันการทดสอบสำหรับ macOS
python tests/run_tests_macos.py
```

## การทดสอบเฉพาะส่วน

### 1. ทดสอบกล้องเว็บแคม

สำหรับการทดสอบเฉพาะกล้องเว็บแคม:

```bash
python tests/camera/test_camera.py --test webcam
```

### 2. ทดสอบการสตรีมมิ่ง

สำหรับการทดสอบการสตรีมมิ่ง:

```bash
python tests/camera/test_camera.py --test streaming --duration 5
```

### 3. ทดสอบอัปโหลด Firebase

ใช้คำสั่งต่อไปนี้:

```bash
python tests/firebase/test_firebase.py
```

## การแก้ไขปัญหา

### ปัญหา: ไม่สามารถนำเข้าโมดูล PiCamera

**แนวทางแก้ไข**: ตรวจสอบให้แน่ใจว่าได้รัน `macos_test_helper.py` ก่อนรันการทดสอบ หรือเพิ่มโค้ดต่อไปนี้ที่จุดเริ่มต้นของสคริปต์ทดสอบ:

```python
import sys
if sys.platform == 'darwin':
    from tests.mock.patch_picamera import patch_picamera
    patch_picamera()
```

### ปัญหา: กล้องไม่ทำงานบน macOS

**แนวทางแก้ไข**: ตรวจสอบการอนุญาตกล้องของ macOS โดยเข้าไปที่ การตั้งค่าระบบ > ความเป็นส่วนตัวและความปลอดภัย > กล้อง และอนุญาตให้แอพพลิเคชัน Terminal หรือ IDE ที่ใช้งานอยู่เข้าถึงกล้องได้

### ปัญหา: ไม่มีการแสดงผล

**แนวทางแก้ไข**: หากคุณใช้โหมด `--no-display` แต่ต้องการดูผลลัพธ์ภาพ ให้ปรับปรุงโค้ดเพื่อบันทึกภาพด้วย `--save` แทน:

```bash
python tests/camera/test_camera.py --test webcam --save test_output
```

## คำแนะนำสำหรับการพัฒนา

1. **ใช้กล้องเว็บแคมจริง**: หากเป็นไปได้ ใช้กล้องเว็บแคมจริงจะให้ผลการทดสอบที่ใกล้เคียงกับระบบจริงมากกว่าการใช้กล้องจำลอง

2. **แยกโค้ดเฉพาะแพลตฟอร์ม**: ใช้เงื่อนไข `if sys.platform == 'darwin'` หรือ `if not hasattr(sys.modules.get('picamera', type('obj', (object,), {})), 'PiCamera')` เพื่อแยกโค้ดเฉพาะแพลตฟอร์ม

3. **ทดสอบบน Docker**: หากต้องการสภาพแวดล้อมที่ใกล้เคียงกับ Raspberry Pi มากกว่า การใช้ Docker อาจเป็นทางเลือกที่ดี:

```bash
docker run --name manta-test -v $(pwd):/app -w /app arm32v7/python:3.9 python -m tests.run_tests
```

4. **ใช้สภาพแวดล้อมทดสอบเสมือน**: สร้างสภาพแวดล้อมทดสอบด้วยวิดีโอจำลองเพื่อทดสอบการตรวจจับบุคคลและการติดตาม โดยไม่ต้องใช้กล้องจริง

## อ้างอิง

- [OpenCV Documentation](https://docs.opencv.org/)
- [Python Mock Objects](https://docs.python.org/3/library/unittest.mock.html)
- [Raspberry Pi Camera Python Library](https://picamera.readthedocs.io/)
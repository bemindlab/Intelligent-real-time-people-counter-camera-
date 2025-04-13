MANTA Camera for Debian

---

This package provides the MANTA person detection and tracking system for Raspberry Pi.

The system is automatically configured based on your hardware (Raspberry Pi 4 or 5).

After installation, you can use 'manta-setup' to configure the system.

-- BemindTech <info@bemind.tech> Sun, 14 Apr 2024

9. ตัวอย่างโค้ดเพิ่มเติม

9.1 การสร้างส่วนขยายการตรวจจับใหม่

# camera/detection_extensions.py

from camera.detection import PersonDetector

class EnhancedDetector(PersonDetector):
"""ตัวตรวจจับที่มีความสามารถเพิ่มเติม"""

      def __init__(self, model_path, confidence_threshold=0.5, nms_threshold=0.45, device="CPU"):
          super().__init__(model_path, confidence_threshold, nms_threshold, device)
          self.detection_history = []

      def detect(self, frame):
          """ตรวจจับด้วยการติดตามประวัติ"""
          detections = super().detect(frame)
          self.detection_history.append(len(detections))
          if len(self.detection_history) > 10:
              self.detection_history.pop(0)
          return detections

      def get_average_detections(self):
          """คำนวณจำนวนการตรวจจับเฉลี่ย"""
          if not self.detection_history:
              return 0
          return sum(self.detection_history) / len(self.detection_history)

9.2 การเพิ่มตัวเลือกการกำหนดค่าใหม่

# utils/config_validators.py

def validate_webcam_config(config):
"""ตรวจสอบความถูกต้องของการกำหนดค่า WebCam"""
if config.get('camera', {}).get('type') == 'webcam':
webcam_source = config.get('camera', {}).get('source')
if not webcam_source or not isinstance(webcam_source, str):
raise ValueError("ต้องระบุ 'source' สำหรับการกำหนดค่า WebCam")

          if webcam_source.startswith('rtmp://'):
              wifi_config = config.get('wifi', {})
              if wifi_config.get('enabled', False) and not wifi_config.get('camera_ssid'):
                  raise ValueError("ต้องระบุ 'camera_ssid' เมื่อเปิดใช้งาน WiFi")

      return config

10. ข้อควรระวังและเทคนิค

    10.1 การจัดการแพ็คเกจพิเศษสำหรับ Raspberry Pi

การขึ้นต่อกันบางอย่างเฉพาะสำหรับ Raspberry Pi:

- python3-picamera: เฉพาะ ARM
- การรองรับ GPIO: เฉพาะ Raspberry Pi

วิธีตรวจสอบสถาปัตยกรรมใน Python:

import platform

def is_raspberry_pi():
"""ตรวจสอบว่ากำลังทำงานบน Raspberry Pi หรือไม่"""
try:
with open('/proc/device-tree/model', 'r') as f:
model = f.read()
return 'Raspberry Pi' in model
except:
return False

def get_pi_version():
"""รับเวอร์ชันของ Raspberry Pi"""
try:
with open('/proc/device-tree/model', 'r') as f:
model = f.read()
if 'Raspberry Pi 5' in model:
return 5
elif 'Raspberry Pi 4' in model:
return 4
else:
return 0
except:
return 0

10.2 การทดสอบแพ็คเกจภายใต้สภาพแวดล้อมจำลอง

ใช้ Docker เพื่อทดสอบการติดตั้ง:

# สร้าง Dockerfile

cat > Dockerfile << EOF
FROM debian:bullseye

RUN apt-get update && apt-get install -y python3 python3-pip

COPY manta-camera_0.1.0_all.deb /tmp/
RUN apt-get install -y /tmp/manta-camera_0.1.0_all.deb || true

CMD ["/bin/bash"]
EOF

# สร้างและรันคอนเทนเนอร์

docker build -t manta-test .
docker run -it manta-test

10.3 เทคนิคการ Debug

# ตรวจสอบไฟล์ในแพ็คเกจ

dpkg -c ../manta-camera_0.1.0_all.deb

# ดูข้อมูลแพ็คเกจ

dpkg -I ../manta-camera_0.1.0_all.deb

# แตกไฟล์แพ็คเกจเพื่อตรวจสอบ

mkdir -p extract
dpkg-deb -R ../manta-camera_0.1.0_all.deb extract/
ls -la extract/

# ดูสคริปต์ maintainer

cat extract/DEBIAN/postinst
cat extract/DEBIAN/postrm

ด้วยคู่มือนี้ นักพัฒนาจะสามารถเข้าใจโครงสร้างของโปรเจกต์ MANTA พัฒนาคุณสมบัติใหม่ และสร้างแพ็คเกจสำหรับการแจกจ่ายได้อย่างมีประสิทธิภาพ

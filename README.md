# MANTA - ระบบตรวจจับและวิเคราะห์การเคลื่อนไหวของบุคคล
# (Monitoring and Analytics Node for Tracking Activity)

MANTA เป็นระบบตรวจจับและติดตามบุคคลสำหรับ Raspberry Pi ที่มีน้ำหนักเบา ใช้คอมพิวเตอร์วิชันในการตรวจจับบุคคล ติดตามระหว่างเฟรม และบันทึกข้อมูลกิจกรรมเพื่อการวิเคราะห์

## คุณสมบัติ (Features)

- **ตรวจจับบุคคลแบบเรียลไทม์** โดยใช้โมเดล YOLO
- **ระบบจดจำบุคคล** เพื่อติดตามแต่ละบุคคลระหว่างเฟรม
- **ปรับแต่งสำหรับ Raspberry Pi** เพื่อประสิทธิภาพที่เหมาะสม
- **รองรับการทำงานกับ Firebase** สำหรับการจัดเก็บข้อมูลและการวิเคราะห์บนคลาวด์
- **ปรับแต่งค่าพารามิเตอร์ได้** สำหรับการติดตั้งในสถานการณ์ต่างๆ
- **บันทึกข้อมูลทั้งแบบภายในเครื่องและบนคลาวด์**
- **ระบบการตั้งค่าที่ปลอดภัย** ด้วยการเข้ารหัสข้อมูลสำคัญ

## ความต้องการของระบบ (Prerequisites)

- Raspberry Pi 5 Model B (แนะนำ 4GB RAM หรือมากกว่า)
- กล้อง Raspberry Pi Camera Module หรือกล้อง USB
- Python 3.9+
- OpenCV 4.5+

## เริ่มต้นใช้งานอย่างรวดเร็ว (Quick Start)

1. โคลนโปรเจกต์:
```bash
git clone https://github.com/BemindTech/bmt-manta-camera.git
cd bmt-manta-camera
```

2. รันสคริปต์ติดตั้ง:
```bash
./scripts/get_started.sh
```

3. เริ่มการทำงานของระบบ MANTA:
```bash
python3 camera/main.py
```

## การกำหนดค่า (Configuration)

แก้ไขไฟล์ `config/config.yaml` เพื่อปรับแต่งการตั้งค่า:

```yaml
# การกำหนดค่ากล้อง (Camera Configuration)
camera:
  id: "cam_001"  # รหัสประจำตัวกล้อง
  source: 0  # 0 สำหรับกล้องเริ่มต้น, สามารถเป็น URL RTSP หรือพาธไฟล์
  resolution:
    width: 640  # ความกว้างภาพ
    height: 480  # ความสูงภาพ
  fps: 15  # เฟรมต่อวินาที

# การกำหนดค่าการตรวจจับ (Detection Configuration)
detection:
  model_path: "models/yolov8n.onnx"  # พาธไปยังโมเดล YOLO
  confidence_threshold: 0.5  # ค่าความเชื่อมั่นขั้นต่ำ (0-1)
  classes:
    - person  # ตรวจจับเฉพาะคน
```

## ตัวเลือกคำสั่ง (Command Line Options)

- `--config PATH`: ใช้ไฟล์กำหนดค่าที่ระบุ
- `--debug`: เปิดโหมดดีบั๊กพร้อมการแสดงผลภาพ
- `--no-upload`: ปิดการอัปโหลดไปยัง Firebase
- `--encrypt-key KEY`: คีย์เข้ารหัสสำหรับข้อมูลสำคัญ
- `--encrypt-key-file PATH`: ไฟล์ที่บรรจุคีย์เข้ารหัส

## การตั้งค่ากล้อง Raspberry Pi (Raspberry Pi Camera Setup)

ระบบจะตรวจจับและใช้โมดูลกล้อง Raspberry Pi โดยอัตโนมัติหากมี สำหรับประสิทธิภาพที่ดีที่สุด:

1. เปิดใช้งานอินเตอร์เฟซกล้อง:
```bash
sudo raspi-config
```
ไปที่ "Interface Options" > "Camera" และเปิดใช้งาน

2. ทดสอบกล้อง:
```bash
raspistill -o test.jpg
```

## ความปลอดภัย (Security)

MANTA มีระบบการกำหนดค่าที่ปลอดภัยเพื่อปกป้องข้อมูลประจำตัวที่สำคัญ:

```bash
# สร้างคีย์เข้ารหัส
./utils/encrypt_config.py generate --save .secret_key

# เข้ารหัสการกำหนดค่า Firebase ของคุณ
./utils/encrypt_config.py encrypt --input firebase/firebase_config.json 

# รันระบบพร้อมการกำหนดค่าที่เข้ารหัสแล้ว
python3 camera/main.py --encrypt-key-file .secret_key
```

สำหรับรายละเอียดเพิ่มเติม ดูที่ [คู่มือการกำหนดค่าที่ปลอดภัย](docs/secure_config.md)

## การแก้ไขปัญหา (Troubleshooting)

**ปัญหา**: ระบบทำงานช้าบน Raspberry Pi
- ลดความละเอียดใน config.yaml
- ใช้โมเดลที่เล็กกว่า (yolov8n แทนรุ่นที่ใหญ่กว่า)
- เปิดใช้งานการข้ามเฟรมโดยตั้งค่า FPS ให้ต่ำลง

**ปัญหา**: ไม่สามารถเชื่อมต่อกับ Firebase
- ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต
- ตรวจสอบว่าได้กำหนดค่า firebase_config.json อย่างถูกต้อง
- รันด้วย --no-upload สำหรับการทำงานเฉพาะภายในเครื่อง

**ปัญหา**: ข้อความ "Error decrypting field"
- ตรวจสอบให้แน่ใจว่าคุณใช้คีย์เข้ารหัสที่ถูกต้อง
- เข้ารหัสไฟล์กำหนดค่าของคุณใหม่
- ตรวจสอบว่าพาธการกำหนดค่าทั้งหมดถูกต้อง

## ลิขสิทธิ์ (License)

โปรเจกต์นี้อยู่ภายใต้ลิขสิทธิ์ MIT - ดูไฟล์ LICENSE สำหรับรายละเอียด

## กิตติกรรมประกาศ (Acknowledgements)

- YOLOv8 โดย Ultralytics
- โครงการ OpenCV
- มูลนิธิ Raspberry Pi
- พัฒนาโดย BemindTech สำหรับการใช้งานในประเทศไทย
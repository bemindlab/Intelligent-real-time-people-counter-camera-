# MANTA - ระบบตรวจจับและวิเคราะห์การเคลื่อนไหวของบุคคล
# (Monitoring and Analytics Node for Tracking Activity)

MANTA เป็นระบบตรวจจับและติดตามบุคคลสำหรับ Raspberry Pi ที่มีน้ำหนักเบา ใช้คอมพิวเตอร์วิชันในการตรวจจับบุคคล ติดตามระหว่างเฟรม และบันทึกข้อมูลกิจกรรมเพื่อการวิเคราะห์

## คุณสมบัติ (Features)

- **ตรวจจับบุคคลแบบเรียลไทม์** โดยใช้โมเดล YOLO
- **ระบบจดจำบุคคล** เพื่อติดตามแต่ละบุคคลระหว่างเฟรม
- **ตรวจจับใบหน้าและเก็บข้อมูล** สำหรับการฝึกสอนโมเดล AI
- **อัปโหลดใบหน้าไปยัง Firebase Storage** เพื่อใช้ในการพัฒนาโมเดลการจดจำใบหน้า
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

### การติดตั้งด้วยแพ็คเกจ Debian (แนะนำ)

1. ดาวน์โหลดไฟล์ .deb ล่าสุดจากหน้า Releases:
```bash
wget https://github.com/BemindTech/bmt-manta-camera/releases/download/v0.1.0/manta-camera_0.1.0_all.deb
```

2. ติดตั้งแพ็คเกจ:
```bash
sudo apt install ./manta-camera_0.1.0_all.deb
```

3. รันเครื่องมือตั้งค่า:
```bash
sudo manta-setup
```

หรือเริ่มด้วยการกำหนดค่าเริ่มต้น:
```bash
sudo systemctl start manta-camera
```

สำหรับรายละเอียดเพิ่มเติม ดูที่ [คู่มือแพ็คเกจ Debian](docs/debian-package.md)

### การติดตั้งจากซอร์ส

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

## สำหรับนักพัฒนา (For Developers)

1. ติดตั้งเครื่องมือสำหรับการพัฒนา:
```bash
pip install -e ".[dev]"
# หรือ
pip install -r requirements-dev.txt
```

2. ติดตั้ง pre-commit hooks:
```bash
pre-commit install
```

3. รันการทดสอบ:
```bash
pytest tests/
```

4. ดูคำแนะนำเพิ่มเติมได้ใน [คู่มือสำหรับนักพัฒนา](docs/developer-guide.md)

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

### การใช้งานกับกล้อง Insta360 Go 3S

MANTA รองรับการเชื่อมต่อกับกล้อง Insta360 Go 3S ผ่าน WiFi:

```bash
# ใช้การกำหนดค่าสำหรับ WebCam
cp config/config.webcam.yaml config/config.yaml

# รันพร้อมโหมด WebCam
python3 camera/main.py --webcam-mode --device-url "rtmp://192.168.42.1:1935/live/stream"
```

สำหรับคำแนะนำการตั้งค่าโดยละเอียด ดูที่ [คู่มือการตั้งค่า Insta360](docs/insta360_setup.md)

## ตัวเลือกคำสั่ง (Command Line Options)

- `--config PATH`: ใช้ไฟล์กำหนดค่าที่ระบุ
- `--debug`: เปิดโหมดดีบั๊กพร้อมการแสดงผลภาพ
- `--no-upload`: ปิดการอัปโหลดไปยัง Firebase
- `--encrypt-key KEY`: คีย์เข้ารหัสสำหรับข้อมูลสำคัญ
- `--encrypt-key-file PATH`: ไฟล์ที่บรรจุคีย์เข้ารหัส
- `--webcam-mode`: ใช้โหมด WebCam Protocol สำหรับกล้องเช่น Insta360
- `--device-url URL`: กำหนด URL ของอุปกรณ์ WebCam (เช่น rtmp://192.168.42.1:1935/live/stream)
- `--enable-remote-config`: เปิดใช้งานการกำหนดค่าระยะไกลผ่าน HTTP
- `--remote-config-port PORT`: กำหนดพอร์ตสำหรับการกำหนดค่าระยะไกล (ค่าเริ่มต้น: 8080)
- `--enable-wifi-direct`: เปิดใช้งาน WiFi Direct สำหรับการเชื่อมต่อโดยตรง
- `--enable-face-detection`: เปิดใช้งานการตรวจจับใบหน้าและเก็บข้อมูลสำหรับการเทรน AI
- `--no-face-upload`: ปิดการอัปโหลดใบหน้าไปยัง Firebase Storage

## การตั้งค่า Raspberry Pi (Raspberry Pi Setup)

MANTA มีสคริปต์ตั้งค่าอัตโนมัติสำหรับ Raspberry Pi ที่จะตรวจจับรุ่นของ Pi และตั้งค่าที่เหมาะสมโดยอัตโนมัติ:

```bash
./scripts/rpi_setup.sh
```

สคริปต์นี้จะ:
- ตรวจจับว่าคุณใช้ Raspberry Pi 4 หรือ 5
- ติดตั้งแพ็คเกจที่จำเป็นทั้งหมด
- ตั้งค่าไฟล์กำหนดค่าที่เหมาะสมสำหรับรุ่นของคุณ
- เปิดใช้งานและทดสอบอินเตอร์เฟซกล้อง
- ตั้งค่าบริการ systemd สำหรับเริ่มต้นอัตโนมัติ (ทางเลือก)

นอกจากนี้คุณยังสามารถใช้ไฟล์กำหนดค่าเฉพาะรุ่นได้โดยตรง:

```bash
# สำหรับ Raspberry Pi 4
cp config/config.rpi4.yaml config/config.yaml

# สำหรับ Raspberry Pi 5
cp config/config.rpi5.yaml config/config.yaml
```

สำหรับรายละเอียดเกี่ยวกับฮาร์ดแวร์ที่รองรับและคำแนะนำในการติดตั้ง ดูที่ [คู่มือฮาร์ดแวร์](docs/hardwares.md) และ [การกำหนดค่า Raspberry Pi](docs/rpi_configurations.md)

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

## การกำหนดค่าระยะไกล (Remote Configuration)

MANTA รองรับการกำหนดค่าระยะไกลผ่าน HTTP และ WiFi Direct:

```bash
# เปิดใช้งานเว็บอินเทอร์เฟซการกำหนดค่า
python3 camera/main.py --enable-remote-config

# เปิดใช้งาน WiFi Direct สำหรับการเชื่อมต่อโดยตรง
python3 camera/main.py --enable-remote-config --enable-wifi-direct
```

หลังจากเปิดใช้งาน คุณสามารถเข้าถึงเว็บอินเทอร์เฟซการกำหนดค่าได้ที่:
- ภายในเครือข่าย: `http://<raspberry-pi-ip>:8080/`
- ผ่าน WiFi Direct: `http://192.168.42.1:8080/`

สำหรับรายละเอียดเพิ่มเติม ดูที่ [คู่มือการกำหนดค่าระยะไกล](docs/remote_config.md)

## การตรวจจับใบหน้าและการเก็บข้อมูล (Face Detection and Data Collection)

MANTA สามารถตรวจจับใบหน้าของบุคคลที่ตรวจพบ บันทึกภาพใบหน้า และอัปโหลดไปยัง Firebase Storage เพื่อใช้ในการเทรนโมเดล AI:

```bash
# เปิดใช้งานการตรวจจับใบหน้าและการอัปโหลด
python3 camera/main.py --enable-face-detection

# เปิดใช้งานการตรวจจับใบหน้าแต่ไม่อัปโหลด
python3 camera/main.py --enable-face-detection --no-face-upload
```

โดยค่าเริ่มต้น ระบบจะ:
- ตรวจจับใบหน้าของบุคคลที่ตรวจพบ
- ตัดส่วนและบันทึกภาพใบหน้าในไดเร็กทอรี `dataset/faces/`
- จำกัดจำนวนภาพใบหน้าต่อบุคคล (ค่าเริ่มต้น: 5 ภาพ)
- อัปโหลดไปยัง Firebase Storage พร้อมเมทาดาต้า (หากเปิดใช้งาน)

สำหรับรายละเอียดเพิ่มเติม ดูที่ [คู่มือการตรวจจับใบหน้า](docs/face_detection.md)

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

## การออกแบบระบบ (System Design)

MANTA มีเอกสารออกแบบระบบที่ครอบคลุมซึ่งอธิบายการทำงานของระบบ:

- [เอกสารออกแบบระบบ](docs/system_design.md): อธิบายสถาปัตยกรรมและการไหลของข้อมูล
- [ข้อมูลจำเพาะทางเทคนิค](docs/technical_specification.md): รายละเอียดทางเทคนิคของระบบ

### แผนภาพระบบ (System Diagrams)

MANTA มาพร้อมกับแผนภาพสถาปัตยกรรมระบบที่สร้างขึ้นด้วย D2 (https://d2lang.com/):

- **แผนภาพสถาปัตยกรรมระบบ**: ภาพรวมคอมโพเนนต์ทั้งหมดของระบบ MANTA
- **แผนภาพการไหลของข้อมูล**: แสดงวิธีการไหลของข้อมูลผ่านระบบ
- **แผนภาพการกำหนดค่าเครือข่าย**: แสดงการเชื่อมต่อเครือข่าย รวมถึง WiFi Direct และ WebCam
- **แผนภาพการกำหนดค่ากล้อง**: แสดงรายละเอียดระบบการกำหนดค่าระยะไกล
- **แผนภาพคอมโพเนนต์**: แสดงความสัมพันธ์ระหว่างคอมโพเนนต์ต่างๆ ในโค้ด

คุณสามารถดูแผนภาพเหล่านี้ได้ที่ [docs/d2](docs/d2/README.md) และสร้างไฟล์ SVG จากแผนภาพเหล่านี้โดยใช้คำสั่ง:

```bash
./scripts/generate_diagrams.sh
```

## กิตติกรรมประกาศ (Acknowledgements)

- YOLOv8 โดย Ultralytics
- โครงการ OpenCV
- มูลนิธิ Raspberry Pi
- พัฒนาโดย BemindTech สำหรับการใช้งานในประเทศไทย
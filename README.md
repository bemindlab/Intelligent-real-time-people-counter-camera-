
# MANTA – Monitoring and Analytics Node for Tracking Activity  
**Project Name:** MANTA  
**Version:** 1.1  
**Date:** 2025-04-11

---

## 1. Objective
สร้างระบบกล้องอัจฉริยะที่สามารถ:
- ตรวจจับและนับจำนวน “คน” แบบเรียลไทม์
- จดจำคนที่เคยผ่านกล้องแล้ว (Re-ID) เพื่อลดการนับซ้ำ
- เก็บ log ภายในกล้อง
- ส่งข้อมูล log ขึ้น Firebase Realtime Database
- ใช้ n8n เพื่อทำ workflow automation เช่น แจ้งเตือน, สรุปข้อมูล, backup log

---

## 2. Functional Requirements

### 2.1. People Detection (YOLO + NPU)
- ตรวจจับ "person" class ด้วย YOLOv8 หรือ YOLOv5
- รองรับ hardware acceleration (Coral, Jetson, Hailo, etc.)

### 2.2. Re-Identification
- แปลงภาพบุคคลเป็น feature vector
- ใช้ hash หรือ cosine similarity เพื่อเปรียบเทียบกับบุคคลที่เคยเจอ
- ถ้าไม่ใช่บุคคลซ้ำ → บันทึก log ใหม่

### 2.3. Local Logging
- เก็บ log แบบ JSON หรือ SQLite
- ตัวอย่างข้อมูล:
```json
{
  "timestamp": "2025-04-11T14:30:22",
  "person_hash": "7d82aef9",
  "camera_id": "cam_001"
}
```

### 2.4. Firebase Realtime Database Integration
- ส่งข้อมูล log จากกล้องขึ้น Firebase Realtime DB
- หากออฟไลน์ → เก็บไว้ก่อน แล้ว retry เมื่อเชื่อมต่อได้
- ใช้ `firebase-admin` SDK

### 2.5. n8n Integration
- ติดตั้ง n8n ผ่าน Docker Compose
- สร้าง workflow เช่น:
  - เมื่อมี log ใหม่ใน Firebase → แจ้งเตือน LINE/Telegram
  - สรุปจำนวนคนรายวัน → ส่ง Google Sheet หรือ Email
  - Backup ข้อมูลจาก Firebase ไปที่ Google Drive

---

## 3. Non-Functional Requirements

### 3.1. Performance
- ตรวจจับภาพ ≥ 10 FPS
- รองรับการใช้งาน 24/7 บนอุปกรณ์ edge

### 3.2. Scalability
- รองรับหลายกล้อง → คนละ Firebase node
- n8n สามารถ scale บน server กลางหรือ cloud VPS

### 3.3. Reliability
- หากการเชื่อมต่อ Firebase หรือ n8n ขัดข้อง → ระบบต้องไม่หยุดทำงานหลัก

---

## 4. Dataset Requirements
- YOLO dataset format:
```
dataset/
├── images/train/
├── images/val/
├── labels/train/
├── labels/val/
└── person.yaml
```
- class: 'person' หรือ 'face'

---

## 5. System Architecture Overview

```
[Camera + NPU Board]
        |
    YOLOv8 Inference
        |
  +-------------+             +--------------------+
  | Re-ID & Log |------------>| Firebase Realtime  |
  +-------------+             | Database           |
        |                    +--------------------+
        |                             |
        v                             v
 Local Storage                [n8n Workflow Automation]
                                   |
                                   ├── แจ้งเตือน LINE
                                   ├── สรุปลง Google Sheet
                                   └── Backup รายวัน
```

---

## 6. Docker-Compose for n8n + Firebase Ready

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    platform: linux/arm64  # ถ้าใช้บน Raspberry Pi
    restart: always
    ports:
      - 5678:5678
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=securepassword
      - WEBHOOK_URL=https://your-public-url.com/
      - GENERIC_TIMEZONE=Asia/Bangkok
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
```

---

## 7. Firebase Integration Detail
- ใช้ `firebase-admin` SDK
- โครงสร้าง database:
```json
"cameras": {
  "cam_001": {
    "logs": {
      "log_id_001": {
        "timestamp": "2025-04-11T14:30:22",
        "person_hash": "7d82aef9"
      }
    }
  }
}
```

---

## 8. Tools and Libraries
- `ultralytics`, `opencv-python`, `numpy`, `scipy`
- `firebase-admin`
- `n8n` (Dockerized automation engine)
- `LabelImg` หรือ `Roboflow` สำหรับจัดการ Dataset

---

## 9. Optional Enhancements
- Web dashboard ดู realtime จาก Firebase
- Heatmap วิเคราะห์จำนวนคนในช่วงเวลาต่าง ๆ
- Face recognition หรือ Emotion detection (อนาคต)

---

## 10. Code Repository Structure

```
manta/
├── camera/
│   ├── main.py                # โปรแกรมหลักบนกล้อง
│   ├── detection.py           # YOLO detect person
│   ├── reid.py                # Feature hashing / vector comparison
│   ├── logger.py              # เขียน log ลง local
│   └── uploader.py            # ดัน log ขึ้น Firebase
│
├── models/
│   ├── yolov8n.onnx           # YOLO model (exported)
│   ├── face_encoder.onnx      # optional: model สำหรับ vectorize ใบหน้า
│   └── requirements.txt       # ไลบรารีที่ใช้บนกล้อง
│
├── dataset/
│   ├── images/                # ภาพ dataset (ถ้าเทรนเอง)
│   ├── labels/                # YOLO format labels
│   └── dataset.yaml           # config YOLO
│
├── n8n/
│   ├── docker-compose.yml     # สำหรับรัน n8n workflow automation
│   └── workflows/             # ไฟล์ workflow JSON ของ n8n
│
├── firebase/
│   ├── firebase_config.json   # Service account key
│   └── firebase_utils.py      # ฟังก์ชันส่ง log ไปยัง Firebase
│
├── utils/
│   ├── camera_utils.py        # อ่านภาพจากกล้อง, ตั้งค่า stream
│   └── vector_utils.py        # cosine similarity, hashing
│
├── config/
│   └── config.yaml            # config เช่น camera_id, thresholds, Firebase path
│
├── logs/
│   └── local_log.json         # log ที่เก็บในเครื่อง
│
├── README.md
└── manta-spec.md              # Requirements spec
```

---

## 11. Run Instructions

### 11.1 Development Mode (Dev)
ใช้สำหรับทดสอบบนเครื่องหรือบน Raspberry Pi แบบ interactive:
```bash
# ติดตั้ง dependencies (เฉพาะครั้งแรก)
pip install -r models/requirements.txt

# รัน main script แบบ dev
python camera/main.py --debug
```

### 11.2 Debug Mode
เปิด log เพิ่มเติม, แสดง vector, และไม่ส่งข้อมูลไป Firebase:
```bash
python camera/main.py --debug --no-upload
```

### 11.3 Production Mode
ใช้กับ systemd หรือ supervisor บน Raspberry Pi:
```bash
# ตัวอย่างรันแบบ background
python camera/main.py --config config/config.yaml
```

หรือเพิ่มใน `systemd`:
```
[Unit]
Description=MANTA People Counter

[Service]
ExecStart=/usr/bin/python3 /home/pi/manta/camera/main.py --config /home/pi/manta/config/config.yaml
WorkingDirectory=/home/pi/manta
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 12. System Setup & Dependencies

### 12.1 Operating System Preparation (for Raspberry Pi 5)
1. Flash Raspberry Pi OS (64-bit) Lite using Raspberry Pi Imager
2. Enable SSH (optional): Create an empty file named `ssh` in the boot partition
3. Connect to Wi-Fi (optional): Create `wpa_supplicant.conf` in boot
4. Boot up and run:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-opencv libatlas-base-dev libjpeg-dev libtiff5 -y
sudo apt install docker.io docker-compose -y
```

### 12.2 Python Dependencies
```bash
pip3 install -r models/requirements.txt
```

### 12.3 Required Services
- **Firebase**: Create project, enable Realtime Database, download service key
- **n8n**: Run via Docker (see Section 6)
- **Camera driver**: Enable with `sudo raspi-config` → Interface → Camera

---

## 13. Project Structure by Importance

### **Core Components**
- `camera/main.py`: Real-time detection + Re-ID logic
- `detection.py`, `reid.py`: Model inference + vector matching
- `logger.py`, `uploader.py`: Log management and cloud sync

### **Support Systems**
- `firebase_utils.py`: Push to Firebase
- `n8n/`: Automation layer for alerts, reports, backups
- `config/config.yaml`: Runtime control and system parameters

### **Tools & Dataset**
- `dataset/`: For custom model training
- `models/`: YOLO and encoder models
- `utils/`: Shared helper functions
- `logs/`: Local backup of people logs

---

## 14. Open Source & Collaboration

### **MANTA is Open Source** – Commercially deployable

เราพัฒนาโปรเจกต์นี้ให้เป็น **Open Source Core** ที่ทุกคนสามารถ:
- Fork, แก้ไข, หรือปรับแต่งตามความต้องการ
- ร่วมพัฒนาใน GitHub ผ่าน issues, pull requests หรือ discussions
- ใช้งานฟรีในโครงการวิจัย การศึกษา หรือโปรเจกต์ส่วนตัว

### **Commercial Usage**
เราเปิดให้ใช้ **MANTA เป็น Solution-as-a-Service (SaaS)** หรือ On-premise solution สำหรับ:
- ร้านค้าอัจฉริยะ
- โครงการ Smart City
- ระบบความปลอดภัยอัตโนมัติ

หากสนใจ **ซื้อระบบแบบ turnkey หรือปรึกษาการติดตั้งใช้งาน**  
สามารถติดต่อผ่านหน้า GitHub หรืออีเมลใน repo ได้โดยตรง

---

## 15. Want to Contribute?

เรายินดีต้อนรับทุกคนที่อยากมีส่วนร่วม!  
สิ่งที่คุณสามารถช่วยได้:
- ปรับปรุงประสิทธิภาพ Re-ID
- ทำ Dashboard UI แบบ Real-time
- พัฒนาตัวนับ Heatmap หรือกล้องหลายตัว
- เขียนเอกสารคู่มือเพิ่มเติม
- ทดสอบบนบอร์ดต่าง ๆ

**GitHub Repo:** (ลิงก์จะใส่ภายหลัง)  
**License:** MIT License  
**Contact:** dev@manta-system.dev

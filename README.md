# System Requirements Specification  
**Project Name:** Intelligent Real-Time People Counter with Re-ID, Logging, and Firebase Sync  
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

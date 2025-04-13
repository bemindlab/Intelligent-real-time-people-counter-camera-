# การตรวจจับใบหน้าและการเก็บข้อมูลสำหรับการเทรน AI (Face Detection and Data Collection for AI Training)

เอกสารนี้อธิบายฟีเจอร์การตรวจจับใบหน้าและอัปโหลดไปยัง Firebase Storage ใน MANTA เพื่อใช้ในการเทรนโมเดล AI ต่อไป

## ภาพรวม

ระบบ MANTA มีความสามารถในการตรวจจับใบหน้าของบุคคลที่ตรวจพบในวิดีโอ ตัดส่วนใบหน้า และอัปโหลดไปยัง Firebase Storage พร้อมด้วยเมทาดาต้าที่เกี่ยวข้อง ข้อมูลนี้สามารถใช้สำหรับการฝึกสอนหรือปรับปรุงโมเดล AI ในการจดจำบุคคลได้

## คุณสมบัติหลัก

- **ตรวจจับใบหน้าอัตโนมัติ**: ตรวจจับใบหน้าในกรอบขอบเขตของบุคคลที่ตรวจพบ
- **ตัดส่วนและปรับขนาดใบหน้า**: ตัดส่วนเฉพาะใบหน้าและปรับขนาดเป็นขนาดมาตรฐาน
- **จำกัดจำนวนใบหน้าต่อบุคคล**: สามารถกำหนดจำนวนภาพใบหน้าสูงสุดที่จะเก็บสำหรับแต่ละบุคคล
- **บันทึกลงในระบบไฟล์ท้องถิ่น**: เก็บภาพใบหน้าในพาธที่กำหนดในระบบไฟล์ท้องถิ่น
- **อัปโหลดไปยัง Firebase Storage**: อัปโหลดภาพใบหน้าไปยัง Firebase Storage พร้อมเมทาดาต้า
- **บันทึกเมทาดาต้า**: บันทึกรายละเอียดเกี่ยวกับใบหน้า เช่น person_id, ตำแหน่ง, เวลาที่ตรวจพบ

## การใช้งาน

### เปิดใช้งานการตรวจจับใบหน้า

มีสองวิธีในการเปิดใช้งานการตรวจจับใบหน้า:

1. **ผ่านอาร์กิวเมนต์บรรทัดคำสั่ง**:

   ```bash
   python3 camera/main.py --enable-face-detection
   ```

   หากต้องการเปิดใช้งานการอัปโหลดไปยัง Firebase Storage:

   ```bash
   python3 camera/main.py --enable-face-detection --config=/path/to/config.yaml
   ```

   หากต้องการปิดการอัปโหลดใบหน้า:

   ```bash
   python3 camera/main.py --enable-face-detection --no-face-upload
   ```

2. **ผ่านไฟล์การกำหนดค่า** (config.yaml):

   ```yaml
   # การกำหนดค่าการตรวจจับใบหน้า (Face Detection Configuration)
   face_detection:
     enabled: true  # เปิดใช้งานการตรวจจับใบหน้า
     model_path: null  # พาธไปยังโมเดล DNN face (null สำหรับ Haar Cascade)
     confidence_threshold: 0.5  # ค่าความเชื่อมั่นขั้นต่ำสำหรับการตรวจจับ
     face_size: [224, 224]  # ขนาดของภาพใบหน้าที่ตัด [กว้าง, สูง]
     max_faces_per_person: 5  # จำนวนใบหน้าสูงสุดที่จะเก็บต่อคน
     output_dir: "dataset/faces"  # ไดเร็กทอรีสำหรับเก็บภาพใบหน้า
     upload_to_storage: true  # อัปโหลดใบหน้าไปยัง Firebase Storage
   
   # การกำหนดค่า Firebase (Firebase Configuration)
   firebase:
     enabled: true
     config_path: "firebase/firebase_config.json"
     database_url: "https://your-project-id.firebaseio.com"
     
     # การกำหนดค่า Firebase Storage
     storage:
       enabled: true  # เปิดใช้งานการอัปโหลดไปยัง Firebase Storage
       bucket: "your-project-id.appspot.com"  # Firebase Storage bucket
       thread_count: 2  # จำนวนเธรดในการอัปโหลด
   ```

### การกำหนดค่าขั้นสูง

#### การตรวจจับใบหน้าด้วย DNN

สำหรับการตรวจจับใบหน้าที่แม่นยำยิ่งขึ้น คุณสามารถใช้โมเดล DNN แทน Haar Cascade:

1. ดาวน์โหลดไฟล์โมเดล:
   - deploy.prototxt
   - res10_300x300_ssd_iter_140000.caffemodel

2. กำหนดค่าในไฟล์ config.yaml:

   ```yaml
   face_detection:
     enabled: true
     model_path: "models/face_detection/res10_300x300_ssd_iter_140000.caffemodel"
     confidence_threshold: 0.7  # ปรับตามความแม่นยำที่ต้องการ
   ```

#### การตั้งค่า Firebase Storage

ให้แน่ใจว่าคุณได้ตั้งค่า Firebase Storage ในโปรเจกต์ Firebase ของคุณ:

1. สร้างกฎความปลอดภัย (Security Rules) สำหรับ Storage:

   ```
   rules_version = '2';
   service firebase.storage {
     match /b/{bucket}/o {
       match /faces/{personId}/{filename} {
         allow read, write: if request.auth != null;
       }
     }
   }
   ```

2. อัปเดตไฟล์ firebase_config.json เพื่อให้มีสิทธิ์ในการอัปโหลดไปยัง Storage

## โครงสร้างข้อมูล

### โครงสร้างไดเร็กทอรีท้องถิ่น

ภาพใบหน้าจะถูกบันทึกในไดเร็กทอรีท้องถิ่นในรูปแบบ:

```
dataset/faces/
  └─ person_id_timestamp.jpg
```

### โครงสร้างใน Firebase Storage

ภาพใบหน้าจะถูกอัปโหลดไปยัง Firebase Storage ในรูปแบบ:

```
faces/
  └─ {person_id}/
      └─ person_id_timestamp.jpg
```

### เมทาดาต้า

เมทาดาต้าที่เก็บไว้กับไฟล์ในมี Firebase Storage ดังนี้:

```json
{
  "filename": "person_id_timestamp.jpg",
  "person_id": "unique_person_id",
  "timestamp": 1648123456789,
  "face_id": "unique_face_id",
  "source": "manta_camera",
  "detection_box": {
    "x1": 100,
    "y1": 150,
    "x2": 200,
    "y2": 250
  },
  "detection_confidence": 0.95
}
```

### บันทึกใน Firebase Realtime Database

เมื่อมีการตรวจพบใบหน้าและอัปโหลด จะมีการบันทึกในฐานข้อมูลด้วย:

```json
{
  "type": "face_detected",
  "data": {
    "timestamp": 1648123456789,
    "person_id": "unique_person_id",
    "face_id": "unique_face_id",
    "storage_path": "faces/person_id/filename.jpg",
    "metadata": {
      // เมทาดาต้าทั้งหมดตามที่กล่าวมา
    }
  }
}
```

## การนำข้อมูลไปใช้เทรนโมเดล AI

ข้อมูลใบหน้าที่เก็บไว้ใน Firebase Storage สามารถนำไปใช้เทรนโมเดล AI ได้ดังนี้:

1. **ดาวน์โหลดข้อมูลจาก Firebase Storage**:
   - ใช้ Firebase SDK เพื่อดาวน์โหลดข้อมูลภาพใบหน้าทั้งหมด
   - จัดเรียงข้อมูลตาม person_id เพื่อเตรียมสำหรับการเทรนโมเดลแบบ supervised learning

2. **เตรียมข้อมูลสำหรับการเทรน**:
   - แบ่งข้อมูลเป็นชุด training และ validation
   - แปลงข้อมูลให้อยู่ในรูปแบบที่เหมาะสมสำหรับไลบรารีที่ใช้ในการเทรน (เช่น PyTorch, TensorFlow)

3. **เทรนโมเดล**:
   - เทรนโมเดลการจดจำใบหน้าหรือการแยกประเภทใบหน้า
   - ใช้เทคนิคเช่น transfer learning จากโมเดลพื้นฐานเช่น FaceNet หรือ ArcFace

4. **อัปโหลดโมเดลที่เทรนแล้ว**:
   - แปลงโมเดลให้อยู่ในรูปแบบที่เหมาะสมสำหรับการใช้งาน (เช่น ONNX, TFLite)
   - นำกลับมาใช้งานในระบบ MANTA

## ข้อควรระวัง

1. **พื้นที่จัดเก็บข้อมูล**: การเก็บภาพใบหน้าจำนวนมากอาจใช้พื้นที่จัดเก็บมาก ควรกำหนดค่า `max_faces_per_person` ให้เหมาะสม

2. **ความเป็นส่วนตัว**: ต้องปฏิบัติตามกฎหมายเกี่ยวกับการเก็บข้อมูลส่วนบุคคล เช่น PDPA ในประเทศไทย หรือ GDPR ในยุโรป

3. **การใช้งานพลังงานและทรัพยากร**: การตรวจจับใบหน้าและอัปโหลดอาจทำให้ใช้ทรัพยากรเพิ่มขึ้น ควรคำนึงถึงข้อจำกัดของฮาร์ดแวร์ที่ใช้

4. **ความแม่นยำ**: การตรวจจับใบหน้าอาจไม่แม่นยำ 100% โดยเฉพาะในสภาพแสงน้อยหรือเมื่อใบหน้าอยู่ในมุมที่ไม่เหมาะสม

## คำถามที่พบบ่อย

### ฉันสามารถใช้โมเดลตรวจจับใบหน้าอื่นได้หรือไม่?

ใช่ ระบบถูกออกแบบให้รองรับทั้ง Haar Cascade (เร็วแต่แม่นยำน้อยกว่า) และโมเดล DNN (แม่นยำกว่าแต่ช้ากว่า) หากคุณต้องการใช้โมเดลอื่น คุณสามารถขยายคลาส `FaceDetector` ในไฟล์ `utils/face_utils.py`

### ระบบจะจัดการกับใบหน้าซ้ำอย่างไร?

ระบบจำกัดจำนวนใบหน้าที่จะเก็บต่อบุคคลด้วยพารามิเตอร์ `max_faces_per_person` ซึ่งช่วยให้แน่ใจว่าจะไม่เก็บภาพใบหน้าซ้ำมากเกินไป

### ฉันสามารถดูภาพใบหน้าที่เก็บไว้ได้อย่างไร?

คุณสามารถดูภาพใบหน้าที่เก็บไว้ในท้องถิ่นได้โดยตรงจากพาธที่กำหนดในการกำหนดค่า (`output_dir`) และสำหรับภาพที่อัปโหลดไปยัง Firebase Storage คุณสามารถใช้ Firebase Console หรือ API ของ Firebase Storage เพื่อเรียกดูได้
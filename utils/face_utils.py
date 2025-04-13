#!/usr/bin/env python3
"""
โมดูลตรวจจับและตัดส่วนใบหน้าสำหรับระบบ MANTA
(Face detection and cropping module for MANTA system)

ใช้สำหรับตัดส่วนใบหน้าในภาพและจัดการดึงข้อมูลใบหน้าเพื่อการเทรนโมเดล AI
"""

import cv2
import numpy as np
import os
import time
import uuid
from typing import List, Tuple, Optional, Union, Dict, Any

class FaceDetector:
    """
    ตัวตรวจจับใบหน้าโดยใช้ OpenCV
    """
    
    def __init__(self, 
                 confidence_threshold: float = 0.5,
                 model_path: Optional[str] = None,
                 face_size: Tuple[int, int] = (224, 224)):
        """
        เริ่มต้นตัวตรวจจับใบหน้า
        
        Args:
            confidence_threshold: ค่าความเชื่อมั่นขั้นต่ำสำหรับการตรวจจับ
            model_path: พาธไปยังโมเดล face detection ถ้าเป็น None จะใช้ Haar Cascade
            face_size: ขนาดของภาพใบหน้าที่จะตัด (กว้าง, สูง)
        """
        self.confidence_threshold = confidence_threshold
        self.face_size = face_size
        
        # ใช้ OpenCV DNN face detector ถ้ามีโมเดลที่ระบุ
        if model_path and os.path.exists(model_path):
            self.use_dnn = True
            # โหลดโมเดลตรวจจับใบหน้า
            try:
                self.face_model = cv2.dnn.readNetFromCaffe(
                    os.path.join(os.path.dirname(model_path), "deploy.prototxt"),
                    model_path
                )
            except Exception as e:
                print(f"Error loading DNN face model: {e}")
                self.use_dnn = False
                self._init_cascade()
        else:
            self.use_dnn = False
            self._init_cascade()
    
    def _init_cascade(self):
        """
        เริ่มต้นตัวตรวจจับใบหน้าด้วย Haar Cascade
        """
        # โหลด Haar Cascade สำหรับตรวจจับใบหน้า
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # ตรวจสอบว่าโหลด cascade สำเร็จหรือไม่
        if self.face_cascade.empty():
            raise RuntimeError("Error loading face cascade classifier")
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        ตรวจจับใบหน้าในเฟรม
        
        Args:
            frame: ภาพนำเข้า (รูปแบบ BGR)
            
        Returns:
            รายการใบหน้าที่ตรวจพบในรูปแบบ [x, y, width, height, confidence]
        """
        if frame is None or frame.size == 0:
            return []
        
        height, width = frame.shape[:2]
        faces = []
        
        # ใช้ DNN ในการตรวจจับ (แม่นยำกว่า)
        if self.use_dnn:
            # เตรียมข้อมูลนำเข้า
            blob = cv2.dnn.blobFromImage(
                cv2.resize(frame, (300, 300)), 1.0, (300, 300),
                (104.0, 177.0, 123.0), swapRB=False, crop=False
            )
            
            # ทำนายใบหน้า
            self.face_model.setInput(blob)
            detections = self.face_model.forward()
            
            # แปลงผลลัพธ์
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                # กรองตามความเชื่อมั่น
                if confidence < self.confidence_threshold:
                    continue
                
                # แปลงเป็นพิกัดของเฟรมเต็ม
                box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
                x1, y1, x2, y2 = box.astype("int")
                
                # ตรวจสอบว่าพิกัดอยู่ในรูป
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(width, x2)
                y2 = min(height, y2)
                
                # เพิ่มใบหน้าลงในรายการ (แปลงเป็น x, y, w, h)
                w = x2 - x1
                h = y2 - y1
                if w > 0 and h > 0:
                    faces.append((x1, y1, w, h, confidence))
        
        # ใช้ Haar Cascade ในการตรวจจับ (เร็วกว่า แต่แม่นยำน้อยกว่า)
        else:
            # แปลงเป็นภาพขาวดำเพื่อประสิทธิภาพที่ดีขึ้น
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # ตรวจจับใบหน้า
            face_rects = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            # เพิ่มใบหน้าที่ตรวจพบลงในรายการ
            for (x, y, w, h) in face_rects:
                # Haar Cascade ไม่มีคะแนนความเชื่อมั่น จึงตั้งค่าเป็น 1.0
                faces.append((x, y, w, h, 1.0))
        
        return faces
    
    def crop_face(self, frame: np.ndarray, face: Tuple[int, int, int, int, float], 
                  margin: float = 0.2) -> np.ndarray:
        """
        ตัดส่วนใบหน้าจากเฟรม
        
        Args:
            frame: ภาพต้นฉบับ
            face: พิกัดใบหน้า [x, y, width, height, confidence]
            margin: ขอบเขตเพิ่มเติมรอบใบหน้าในรูปแบบอัตราส่วน (0.2 = 20%)
            
        Returns:
            ภาพใบหน้าที่ตัดแล้ว
        """
        # แยกพิกัด
        x, y, w, h, _ = face
        
        # เพิ่มขอบ
        margin_x = int(w * margin)
        margin_y = int(h * margin)
        
        # คำนวณพิกัดด้วยขอบเพิ่มเติม
        height, width = frame.shape[:2]
        x1 = max(0, x - margin_x)
        y1 = max(0, y - margin_y)
        x2 = min(width, x + w + margin_x)
        y2 = min(height, y + h + margin_y)
        
        # ตัดส่วนใบหน้า
        face_img = frame[y1:y2, x1:x2]
        
        # ปรับขนาดเป็นขนาดมาตรฐาน
        if face_img.size > 0:
            face_img = cv2.resize(face_img, self.face_size)
        
        return face_img
    
    def process_person_for_faces(self, frame: np.ndarray, 
                                 person_box: Tuple[float, float, float, float, float, int]) -> List[np.ndarray]:
        """
        ประมวลผลคนที่ตรวจจับได้เพื่อหาใบหน้า
        
        Args:
            frame: ภาพต้นฉบับ
            person_box: กรอบคนที่ตรวจจับได้ [x1, y1, x2, y2, confidence, class_id]
            
        Returns:
            รายการภาพใบหน้าที่ตัดแล้ว
        """
        # ตัดเฉพาะส่วนของคน
        x1, y1, x2, y2, _, _ = person_box
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        height, width = frame.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)
        
        if x1 >= x2 or y1 >= y2:
            return []
        
        person_img = frame[y1:y2, x1:x2]
        
        # ตรวจจับใบหน้าในส่วนของคน
        faces = self.detect_faces(person_img)
        
        # ตัดใบหน้า
        cropped_faces = []
        for face in faces:
            face_img = self.crop_face(person_img, face)
            if face_img.size > 0:
                cropped_faces.append(face_img)
        
        return cropped_faces


class FaceDataManager:
    """
    จัดการข้อมูลใบหน้าสำหรับการฝึกสอน AI
    """
    
    def __init__(self, output_dir: str = "dataset/faces", max_faces_per_person: int = 5):
        """
        เริ่มต้นตัวจัดการข้อมูลใบหน้า
        
        Args:
            output_dir: ไดเร็กทอรีสำหรับบันทึกข้อมูลใบหน้า
            max_faces_per_person: จำนวนใบหน้าสูงสุดที่จะบันทึกต่อคน
        """
        self.output_dir = output_dir
        self.max_faces_per_person = max_faces_per_person
        
        # สร้างไดเร็กทอรีถ้ายังไม่มี
        os.makedirs(output_dir, exist_ok=True)
        
        # แคชไอดีบุคคล
        self.person_faces_count = {}
    
    def save_face(self, face_img: np.ndarray, person_id: str) -> Optional[str]:
        """
        บันทึกภาพใบหน้าสำหรับคนที่กำหนด
        
        Args:
            face_img: ภาพใบหน้า
            person_id: รหัสคนที่ตรวจจับได้
            
        Returns:
            พาธของไฟล์ที่บันทึกหรือ None ถ้าไม่บันทึก
        """
        # ตรวจสอบจำนวนใบหน้าของคนนี้
        if person_id not in self.person_faces_count:
            self.person_faces_count[person_id] = 0
        
        # ตรวจสอบว่าเกินจำนวนสูงสุดหรือไม่
        if self.person_faces_count[person_id] >= self.max_faces_per_person:
            return None
        
        # สร้างชื่อไฟล์
        timestamp = int(time.time() * 1000)
        filename = f"{person_id}_{timestamp}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        
        # บันทึกภาพ
        cv2.imwrite(filepath, face_img)
        
        # เพิ่มจำนวนใบหน้า
        self.person_faces_count[person_id] += 1
        
        return filepath
    
    def get_metadata(self, face_path: str, person_id: str) -> Dict[str, Any]:
        """
        สร้างข้อมูลเมทาดาต้าสำหรับใบหน้า
        
        Args:
            face_path: พาธของไฟล์ใบหน้า
            person_id: รหัสคนที่ตรวจจับได้
            
        Returns:
            พจนานุกรมเมทาดาต้า
        """
        filename = os.path.basename(face_path)
        
        return {
            "filename": filename,
            "person_id": person_id,
            "timestamp": int(time.time() * 1000),
            "face_id": str(uuid.uuid4()),
            "source": "manta_camera"
        }
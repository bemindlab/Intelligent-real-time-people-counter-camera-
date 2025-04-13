#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MANTA - ระบบตรวจจับและวิเคราะห์การเคลื่อนไหวของบุคคล
ไฟล์หลักสำหรับเริ่มต้นระบบกล้อง
"""

import os
import sys
import time
import argparse
import logging
import yaml
import cv2
import numpy as np
import uuid

# เพิ่มไดเร็กทอรีหลักลงในพาธ
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera.detection import PersonDetector
from camera.reid import PersonReIdentifier
from camera.logger import ActivityLogger
from camera.uploader import FirebaseUploader
from utils.camera_utils import setup_camera
from utils.config_utils import decrypt_config_fields, load_encryption_key
from utils.webcam_utils import WebcamConnection, create_insta360_connection
from utils.remote_config import setup_remote_config
from utils.face_utils import FaceDetector, FaceDataManager
from firebase.storage_utils import init_storage_uploader, upload_face_image

# ตั้งค่าการบันทึก
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/manta.log')
    ]
)
logger = logging.getLogger('manta')

def parse_arguments():
    """แยกวิเคราะห์อาร์กิวเมนต์บรรทัดคำสั่ง"""
    parser = argparse.ArgumentParser(description='MANTA - ระบบตรวจจับและวิเคราะห์การเคลื่อนไหวของบุคคล')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                        help='พาธไปยังไฟล์กำหนดค่า')
    parser.add_argument('--debug', action='store_true',
                        help='เปิดโหมดดีบั๊กพร้อมการแสดงผลภาพ')
    parser.add_argument('--no-upload', action='store_true',
                        help='ปิดการอัปโหลดไปยัง Firebase')
    parser.add_argument('--encrypt-key', type=str,
                        help='คีย์เข้ารหัสสำหรับข้อมูลสำคัญ')
    parser.add_argument('--encrypt-key-file', type=str,
                        help='ไฟล์ที่บรรจุคีย์เข้ารหัส')
    parser.add_argument('--webcam-mode', action='store_true',
                        help='ใช้โหมด WebCam Protocol (เช่น สำหรับ Insta360)')
    parser.add_argument('--device-url', type=str,
                        help='URL ของอุปกรณ์ WebCam (เช่น rtmp://192.168.42.1:1935/live/stream)')
    parser.add_argument('--enable-remote-config', action='store_true',
                        help='เปิดใช้งานการกำหนดค่าระยะไกลผ่าน HTTP')
    parser.add_argument('--remote-config-port', type=int, default=8080,
                        help='พอร์ตสำหรับการกำหนดค่าระยะไกล (ค่าเริ่มต้น: 8080)')
    parser.add_argument('--enable-wifi-direct', action='store_true',
                        help='เปิดใช้งาน WiFi Direct สำหรับการเชื่อมต่อโดยตรง')
    parser.add_argument('--enable-face-detection', action='store_true',
                        help='เปิดใช้งานการตรวจจับใบหน้าและเก็บรวบรวมข้อมูลสำหรับการเทรน AI')
    parser.add_argument('--no-face-upload', action='store_true',
                        help='ปิดการอัปโหลดใบหน้าไปยัง Firebase Storage')
    
    return parser.parse_args()

def load_config(config_path, encrypt_key=None):
    """
    โหลดการกำหนดค่าจากไฟล์ YAML
    
    Args:
        config_path (str): พาธไปยังไฟล์การกำหนดค่า
        encrypt_key (bytes, optional): คีย์เข้ารหัสสำหรับการเข้ารหัสฟิลด์
    
    Returns:
        dict: การกำหนดค่าที่โหลด
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # ถอดรหัสฟิลด์หากจำเป็น
        if encrypt_key:
            config = decrypt_config_fields(config, encrypt_key)
            
        return config
    except Exception as e:
        logger.error(f"ไม่สามารถโหลดการกำหนดค่าได้: {e}")
        return {}

def initialize_system(args, config):
    """
    เริ่มต้นระบบ MANTA
    
    Args:
        args (Namespace): อาร์กิวเมนต์บรรทัดคำสั่ง
        config (dict): การกำหนดค่า
    
    Returns:
        tuple: (cap, detector, reidentifier, activity_logger, uploader, face_detector, face_manager, storage_uploader)
    """
    # เริ่มต้นกล้อง
    try:
        if args.webcam_mode or config.get('camera', {}).get('type') == 'webcam':
            logger.info("เริ่มต้นในโหมด WebCam Protocol")
            
            # ตั้งค่า URL ของอุปกรณ์ถ้ามีการระบุในอาร์กิวเมนต์
            if args.device_url:
                config['camera']['source'] = args.device_url
            
            # ตรวจสอบว่าเป็นกล้อง Insta360 หรือไม่
            if 'insta360' in config.get('camera', {}).get('source', '').lower() or \
               'insta360' in config.get('camera', {}).get('id', '').lower():
                logger.info("ตรวจพบการตั้งค่า Insta360 Go 3S")
                cap = create_insta360_connection(config)
            else:
                logger.info("ใช้การเชื่อมต่อ WebCam ทั่วไป")
                cap = WebcamConnection(config=config)
            
            # เชื่อมต่อกับกล้อง
            if not cap.connect():
                logger.error("ไม่สามารถเชื่อมต่อกับกล้องได้")
                return None, None, None, None, None
        else:
            # ใช้กล้องปกติผ่าน OpenCV
            cap = setup_camera(config.get('camera', {}))
            
        logger.info("เริ่มต้นกล้องสำเร็จ")
    except Exception as e:
        logger.error(f"ไม่สามารถเริ่มต้นกล้องได้: {e}")
        return None, None, None, None, None
    
    # เริ่มต้น PersonDetector
    try:
        detection_config = config.get('detection', {})
        detector = PersonDetector(
            model_path=detection_config.get('model_path', 'models/yolov8n.onnx'),
            confidence_threshold=detection_config.get('confidence_threshold', 0.5),
            nms_threshold=detection_config.get('nms_threshold', 0.45),
            device=detection_config.get('device', 'CPU')
        )
        logger.info("เริ่มต้นตัวตรวจจับบุคคลสำเร็จ")
    except Exception as e:
        logger.error(f"ไม่สามารถเริ่มต้นตัวตรวจจับบุคคลได้: {e}")
        return cap, None, None, None, None
    
    # เริ่มต้น PersonReIdentifier
    try:
        reid_config = config.get('reid', {})
        reidentifier = PersonReIdentifier(
            feature_size=reid_config.get('feature_size', 128),
            similarity_threshold=reid_config.get('similarity_threshold', 0.6),
            max_stored_vectors=reid_config.get('max_stored_vectors', 1000)
        )
        logger.info("เริ่มต้นตัวจดจำบุคคลสำเร็จ")
    except Exception as e:
        logger.error(f"ไม่สามารถเริ่มต้นตัวจดจำบุคคลได้: {e}")
        return cap, detector, None, None, None
    
    # เริ่มต้น ActivityLogger
    try:
        logging_config = config.get('logging', {})
        activity_logger = ActivityLogger(
            local_path=logging_config.get('local_path', 'logs/local_log.json'),
            retention_days=logging_config.get('retention_days', 7)
        )
        logger.info("เริ่มต้นตัวบันทึกกิจกรรมสำเร็จ")
    except Exception as e:
        logger.error(f"ไม่สามารถเริ่มต้นตัวบันทึกกิจกรรมได้: {e}")
        return cap, detector, reidentifier, None, None
    
    # เริ่มต้น FirebaseUploader ถ้าเปิดใช้งาน
    uploader = None
    if not args.no_upload and config.get('firebase', {}).get('enabled', False):
        try:
            firebase_config = config.get('firebase', {})
            uploader = FirebaseUploader(
                config_path=firebase_config.get('config_path'),
                database_url=firebase_config.get('database_url'),
                path_prefix=firebase_config.get('path_prefix', 'cameras'),
                retry_interval=firebase_config.get('retry_interval', 60),
                batch_size=firebase_config.get('batch_size', 10)
            )
            logger.info("เริ่มต้นตัวอัปโหลด Firebase สำเร็จ")
        except Exception as e:
            logger.error(f"ไม่สามารถเริ่มต้นตัวอัปโหลด Firebase ได้: {e}")
    else:
        logger.info("ปิดการใช้งานการอัปโหลด Firebase")
    
    # เริ่มต้นการตรวจจับใบหน้า ถ้าเปิดใช้งาน
    face_detector = None
    face_manager = None
    storage_uploader = None
    
    face_detection_enabled = args.enable_face_detection or config.get('face_detection', {}).get('enabled', False)
    
    if face_detection_enabled:
        try:
            face_config = config.get('face_detection', {})
            
            # เริ่มต้นตัวตรวจจับใบหน้า
            face_detector = FaceDetector(
                confidence_threshold=face_config.get('confidence_threshold', 0.5),
                model_path=face_config.get('model_path'),
                face_size=tuple(face_config.get('face_size', [224, 224]))
            )
            
            # เริ่มต้นตัวจัดการข้อมูลใบหน้า
            output_dir = face_config.get('output_dir', 'dataset/faces')
            os.makedirs(output_dir, exist_ok=True)
            
            face_manager = FaceDataManager(
                output_dir=output_dir,
                max_faces_per_person=face_config.get('max_faces_per_person', 5)
            )
            
            logger.info("เริ่มต้นระบบตรวจจับใบหน้าสำเร็จ")
            
            # เริ่มต้น FirebaseStorage สำหรับอัปโหลดใบหน้า
            upload_to_storage = face_config.get('upload_to_storage', False) and not args.no_face_upload
            
            if upload_to_storage and not args.no_upload and config.get('firebase', {}).get('enabled', False):
                try:
                    firebase_config = config.get('firebase', {})
                    storage_config = firebase_config.get('storage', {})
                    
                    if storage_config.get('enabled', False):
                        storage_uploader = init_storage_uploader(
                            firebase_config.get('config_path'),
                            storage_config.get('bucket')
                        )
                        
                        if storage_uploader:
                            logger.info("เริ่มต้นตัวอัปโหลด Firebase Storage สำเร็จ")
                        else:
                            logger.warning("ไม่สามารถเริ่มต้นตัวอัปโหลด Firebase Storage ได้")
                except Exception as e:
                    logger.error(f"เกิดข้อผิดพลาดในการเริ่มต้นตัวอัปโหลด Firebase Storage: {e}")
            
        except Exception as e:
            logger.error(f"ไม่สามารถเริ่มต้นระบบตรวจจับใบหน้าได้: {e}")
            face_detector = None
            face_manager = None
    
    return cap, detector, reidentifier, activity_logger, uploader, face_detector, face_manager, storage_uploader

def process_frame(frame, detector, reidentifier, frame_skip_counter, frame_skip, 
                face_detector=None, face_manager=None):
    """
    ประมวลผลเฟรมเพื่อตรวจจับและจดจำบุคคล
    
    Args:
        frame (numpy.ndarray): เฟรมภาพที่จะประมวลผล
        detector (PersonDetector): ตัวตรวจจับบุคคล
        reidentifier (PersonReIdentifier): ตัวจดจำบุคคล
        frame_skip_counter (int): ตัวนับการข้ามเฟรม
        frame_skip (int): จำนวนเฟรมที่จะข้าม
        face_detector (FaceDetector, optional): ตัวตรวจจับใบหน้า
        face_manager (FaceDataManager, optional): ตัวจัดการข้อมูลใบหน้า
    
    Returns:
        tuple: (detections, identities, frame_with_detections, frame_skip_counter, faces_data)
    """
    # ข้ามเฟรมตามที่กำหนด
    frame_skip_counter += 1
    if frame_skip_counter <= frame_skip:
        return [], [], frame, frame_skip_counter, []
    
    frame_skip_counter = 0
    
    # ตรวจจับบุคคล
    detections = detector.detect(frame)
    
    # สร้างก๊อปปี้ของเฟรมเพื่อวาดการตรวจจับ
    frame_with_detections = frame.copy()
    
    # จดจำและติดตามบุคคล
    identities = []
    faces_data = []  # เก็บข้อมูลใบหน้าที่ตรวจพบ
    
    for i, det in enumerate(detections):
        # แยกข้อมูลการตรวจจับ
        x1, y1, x2, y2, conf, class_id = det
        
        # แยกภาพบุคคล
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        person_img = frame[y1:y2, x1:x2]
        
        # จดจำบุคคล
        is_new, person_id = reidentifier.process(person_img)
        identities.append((person_id, is_new))
        
        # วาดกรอบและข้อมูล
        color = (0, 255, 0) if is_new else (0, 0, 255)
        cv2.rectangle(frame_with_detections, (x1, y1), (x2, y2), color, 2)
        
        # แสดงข้อความ
        text = f"ID: {person_id[:8]}... {'NEW' if is_new else ''}"
        cv2.putText(frame_with_detections, text, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # ตรวจจับใบหน้า ถ้าเปิดใช้งาน
        if face_detector is not None and face_manager is not None:
            try:
                # ตรวจจับใบหน้าในภาพบุคคล
                face_images = face_detector.process_person_for_faces(frame, det)
                
                # วนลูปผ่านทุกใบหน้าที่ตรวจพบ
                for face_idx, face_img in enumerate(face_images):
                    if face_img.size > 0:
                        # บันทึกภาพใบหน้า
                        face_path = face_manager.save_face(face_img, person_id)
                        
                        if face_path:
                            # สร้างเมทาดาต้า
                            metadata = face_manager.get_metadata(face_path, person_id)
                            
                            # เพิ่มข้อมูลเกี่ยวกับตำแหน่งที่พบและความเชื่อมั่น
                            metadata.update({
                                "detection_box": {
                                    "x1": x1, "y1": y1, "x2": x2, "y2": y2
                                },
                                "detection_confidence": float(conf)
                            })
                            
                            # เพิ่มข้อมูลใบหน้าที่ตรวจพบ
                            faces_data.append((face_path, person_id, metadata))
                            
                            # วาดกรอบใบหน้าและข้อความในโหมดดีบั๊ก
                            face_color = (255, 0, 0)  # สีแดง
                            face_box = face_detector.detect_faces(person_img)[face_idx]
                            fx, fy, fw, fh, _ = face_box
                            
                            # ปรับพิกัดให้สัมพันธ์กับภาพเต็ม
                            fx1, fy1 = x1 + fx, y1 + fy
                            fx2, fy2 = fx1 + fw, fy1 + fh
                            
                            # วาดกรอบใบหน้า
                            cv2.rectangle(frame_with_detections, (fx1, fy1), (fx2, fy2), face_color, 1)
            except Exception as e:
                logger.warning(f"เกิดข้อผิดพลาดในการตรวจจับใบหน้า: {e}")
    
    return detections, identities, frame_with_detections, frame_skip_counter, faces_data

def main():
    """ฟังก์ชันหลักของโปรแกรม"""
    args = parse_arguments()
    
    # สร้างไดเร็กทอรีบันทึกถ้ายังไม่มี
    os.makedirs('logs', exist_ok=True)
    
    # โหลดคีย์เข้ารหัส (ถ้ามี)
    encrypt_key = None
    if args.encrypt_key:
        encrypt_key = args.encrypt_key.encode('utf-8')
    elif args.encrypt_key_file:
        encrypt_key = load_encryption_key(args.encrypt_key_file)
    
    # โหลดการกำหนดค่า
    config = load_config(args.config, encrypt_key)
    
    # เปลี่ยนระดับการบันทึกถ้าอยู่ในโหมดดีบั๊ก
    if args.debug or config.get('system', {}).get('debug', False):
        logger.setLevel(logging.DEBUG)
        # ตั้งค่าระดับการบันทึกสำหรับตัวบันทึกย่อยทั้งหมด
        for handler in logging.root.handlers:
            handler.setLevel(logging.DEBUG)
    
    # เริ่มต้นเซิร์ฟเวอร์การกำหนดค่าระยะไกล (ถ้าเปิดใช้งาน)
    remote_config_server = None
    if args.enable_remote_config or config.get('remote_config', {}).get('enabled', False):
        port = args.remote_config_port or config.get('remote_config', {}).get('port', 8080)
        enable_wifi_direct = args.enable_wifi_direct or config.get('wifi_direct', {}).get('enabled', False)
        
        logger.info(f"กำลังเริ่มเซิร์ฟเวอร์การกำหนดค่าระยะไกลที่พอร์ต {port}...")
        remote_config_server = setup_remote_config(
            args.config, 
            enable_wifi_direct=enable_wifi_direct,
            port=port
        )
        
        if remote_config_server:
            logger.info(f"เซิร์ฟเวอร์การกำหนดค่าระยะไกลทำงานที่ http://0.0.0.0:{port}/")
    
    # เริ่มต้นระบบ
    cap, detector, reidentifier, activity_logger, uploader, face_detector, face_manager, storage_uploader = initialize_system(args, config)
    
    if cap is None or detector is None or reidentifier is None or activity_logger is None:
        logger.error("ไม่สามารถเริ่มต้นระบบได้ กำลังออกจากโปรแกรม")
        
        # หยุดเซิร์ฟเวอร์การกำหนดค่าระยะไกล (ถ้ามี)
        if remote_config_server:
            remote_config_server.stop()
        
        sys.exit(1)
        
    # แสดงข้อความว่าการตรวจจับใบหน้าทำงานหรือไม่
    if face_detector is not None and face_manager is not None:
        logger.info("การตรวจจับใบหน้าทำงาน")
        if storage_uploader is not None:
            logger.info("การอัปโหลดใบหน้าไปยัง Firebase Storage ทำงาน")
        else:
            logger.info("การอัปโหลดใบหน้าไปยัง Firebase Storage ไม่ทำงาน")
    
    # ตั้งค่าการข้ามเฟรม
    frame_skip = config.get('detection', {}).get('frame_skip', 0)
    frame_skip_counter = 0
    
    # ตั้งค่าการแสดงวิดีโอ
    show_video = args.debug or config.get('system', {}).get('show_video', False)
    
    logger.info("MANTA กำลังทำงาน...")
    
    try:
        while True:
            # อ่านเฟรม
            if isinstance(cap, WebcamConnection):
                ret, frame = cap.read()
            else:
                ret, frame = cap.read()
            
            if not ret or frame is None:
                logger.warning("ไม่สามารถอ่านเฟรมจากกล้องได้")
                time.sleep(1)
                continue
            
            # ประมวลผลเฟรม
            detections, identities, frame_with_detections, frame_skip_counter, faces_data = process_frame(
                frame, detector, reidentifier, frame_skip_counter, frame_skip,
                face_detector, face_manager
            )
            
            # บันทึกกิจกรรม
            if detections and identities:
                for det, (person_id, is_new) in zip(detections, identities):
                    x1, y1, x2, y2, conf, class_id = det
                    
                    # สร้างรายการบันทึก
                    log_entry = {
                        'timestamp': time.time(),
                        'person_id': person_id,
                        'is_new': is_new,
                        'confidence': float(conf),
                        'location': {
                            'x1': int(x1),
                            'y1': int(y1),
                            'x2': int(x2),
                            'y2': int(y2)
                        }
                    }
                    
                    # เพิ่มข้อมูลว่ามีใบหน้าหรือไม่
                    has_face = any(pid == person_id for _, pid, _ in faces_data)
                    log_entry['has_face'] = has_face
                    
                    # บันทึกไปยัง ActivityLogger
                    activity_logger.log_activity(log_entry)
                    
                    # อัปโหลดไปยัง Firebase ถ้าเปิดใช้งาน
                    if uploader:
                        uploader.upload_log(log_entry)
            
            # อัปโหลดภาพใบหน้าไปยัง Firebase Storage
            if faces_data and storage_uploader:
                for face_path, person_id, metadata in faces_data:
                    # อัปโหลดภาพใบหน้า
                    remote_path = upload_face_image(storage_uploader, face_path, person_id, metadata)
                    
                    if remote_path:
                        logger.debug(f"อัปโหลดใบหน้าไปยัง Firebase Storage: {remote_path}")
                        
                        # บันทึกข้อมูลการอัปโหลดใบหน้าใน Firebase Database
                        if uploader:
                            # สร้างรายการบันทึกสำหรับใบหน้า
                            face_log = {
                                'timestamp': time.time(),
                                'person_id': person_id,
                                'face_id': metadata.get('face_id', str(uuid.uuid4())),
                                'storage_path': remote_path,
                                'metadata': metadata
                            }
                            
                            # อัปโหลดไปยัง Firebase
                            uploader.upload_log({
                                'type': 'face_detected',
                                'data': face_log
                            })
            
            # แสดงเฟรมถ้าเปิดใช้งาน
            if show_video:
                cv2.imshow('MANTA - Person Detection', frame_with_detections)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
            
            # หน่วงเวลาเล็กน้อยเพื่อลดการใช้ CPU
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        logger.info("ได้รับการขัดจังหวะจากผู้ใช้ กำลังออกจากโปรแกรม")
    
    finally:
        # ทำความสะอาดและปิดระบบ
        if show_video:
            cv2.destroyAllWindows()
        
        if isinstance(cap, WebcamConnection):
            cap.disconnect()
        else:
            cap.release()
        
        # ล้างข้อมูลค้างใน Firebase Realtime Database
        if uploader:
            logger.info("กำลังล้างข้อมูลค้างใน Firebase...")
            uploader.flush()
        
        # ล้างข้อมูลค้างใน Firebase Storage
        if storage_uploader:
            logger.info("กำลังล้างข้อมูลค้างใน Firebase Storage...")
            storage_uploader.flush()
            storage_uploader.stop()
        
        # หยุดเซิร์ฟเวอร์การกำหนดค่าระยะไกล (ถ้ามี)
        if remote_config_server:
            remote_config_server.stop()
        
        logger.info("MANTA ถูกปิดอย่างปลอดภัย")

if __name__ == "__main__":
    main()
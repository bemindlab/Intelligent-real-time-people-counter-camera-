#!/usr/bin/env python3
"""
โมดูลอัปโหลดสำหรับส่งข้อมูลไปยัง Firebase
(Uploader module for sending data to Firebase)

รองรับการทำงานแบบออฟไลน์และการพยายามส่งข้อมูลใหม่เมื่อกลับมาออนไลน์
สามารถกำหนดค่าผ่านไฟล์การตั้งค่าหลักของระบบ
"""

import json
import threading
import time
from typing import Dict, Any, List, Optional
import queue
import os

class FirebaseUploader:
    """
    ตัวอัปโหลดสำหรับส่งข้อมูลไปยัง Firebase
    """
    
    def __init__(self, 
                 config_path: str, 
                 database_url: str,
                 path_prefix: str,
                 camera_id: str,
                 retry_interval: int = 60,
                 batch_size: int = 10):
        """
        เริ่มต้นตัวอัปโหลด Firebase
        
        Args:
            config_path: พาธไปยังไฟล์การตั้งค่า Firebase
            database_url: URL ของฐานข้อมูล Firebase
            path_prefix: คำนำหน้าพาธสำหรับการอัปโหลด
            camera_id: รหัสกล้อง
            retry_interval: วินาทีระหว่างการลองใหม่เมื่อออฟไลน์
            batch_size: จำนวนบันทึกที่จะส่งในหนึ่งชุด
        """
        self.config_path = config_path
        self.database_url = database_url
        self.path_prefix = path_prefix
        self.camera_id = camera_id
        self.retry_interval = retry_interval
        self.batch_size = batch_size
        
        # Queue for logs to upload
        self.upload_queue = queue.Queue()
        
        # Flag to indicate if uploader is running
        self.running = False
        
        # Flag to indicate if offline mode
        self.offline_mode = False
        
        # Initialize Firebase
        self._init_firebase()
        
        # Start upload thread
        self.upload_thread = threading.Thread(target=self._upload_worker, daemon=True)
        self.running = True
        self.upload_thread.start()
    
    def _init_firebase(self) -> None:
        """
        เริ่มต้นการเชื่อมต่อ Firebase
        """
        try:
            # Check if firebase_admin module is available
            import firebase_admin
            from firebase_admin import credentials, db
            
            # Check if configuration file exists
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Firebase config not found at {self.config_path}")
            
            # Try to use secure config loading if available
            try:
                from utils.config_utils import load_firebase_config
                
                # Get directory containing main config
                main_config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                main_config_path = os.path.join(main_config_dir, 'config', 'config.yaml')
                
                # Load potentially encrypted Firebase config
                firebase_config = load_firebase_config(main_config_path, self.config_path)
                
                # Initialize with credentials from loaded config
                if firebase_config:
                    # If config has type=service_account, it's a service account key
                    if firebase_config.get('type') == 'service_account':
                        cred = credentials.Certificate(firebase_config)
                        
                        # Initialize app
                        if not firebase_admin._apps:
                            firebase_admin.initialize_app(cred, {
                                'databaseURL': self.database_url
                            })
                    else:
                        # For web config, we need the database URL from the config too
                        db_url = firebase_config.get('databaseURL', self.database_url)
                        
                        # Initialize app
                        if not firebase_admin._apps:
                            firebase_admin.initialize_app({
                                'databaseURL': db_url
                            })
                else:
                    # Fall back to standard loading
                    raise ImportError("Failed to load encrypted Firebase config")
            except ImportError:
                # Standard loading without encryption
                # Load Firebase credentials from file
                cred = credentials.Certificate(self.config_path)
                
                # Initialize app
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred, {
                        'databaseURL': self.database_url
                    })
            
            # Get database reference
            self.db_ref = db.reference(self.path_prefix)
            
            # We're online
            self.offline_mode = False
            print(f"Connected to Firebase: {self.database_url}")
            
        except ImportError:
            print("Warning: firebase_admin module not found. Running in offline mode.")
            self.offline_mode = True
        except Exception as e:
            print(f"Error connecting to Firebase: {e}. Running in offline mode.")
            self.offline_mode = True
    
    def upload_log(self, log_entry: Dict[str, Any]) -> None:
        """
        อัปโหลดบันทึกหนึ่งรายการ
        
        Args:
            log_entry: พจนานุกรมที่มีรายละเอียดบันทึก
        """
        if self.running:
            self.upload_queue.put(log_entry)
    
    def upload_batch(self, logs: List[Dict[str, Any]]) -> bool:
        """
        อัปโหลดบันทึกหลายรายการพร้อมกัน
        
        Args:
            logs: รายการบันทึกที่จะอัปโหลด
            
        Returns:
            bool: True ถ้าอัปโหลดสำเร็จ
        """
        if self.offline_mode or not logs:
            return False
        
        try:
            # Import Firebase modules
            from firebase_admin import db
            
            # Get camera reference
            camera_ref = self.db_ref.child(self.camera_id)
            
            # Upload each log entry
            for log in logs:
                # Generate unique ID using timestamp
                log_id = log.get("timestamp", "")
                if not log_id:
                    log_id = str(int(time.time() * 1000))
                
                # Add to Firebase
                camera_ref.child("logs").child(log_id).set(log)
            
            return True
        except Exception as e:
            print(f"Error uploading to Firebase: {e}")
            # Switch to offline mode on error
            self.offline_mode = True
            return False
    
    def _upload_worker(self) -> None:
        """
        กระบวนการทำงานหลักสำหรับการอัปโหลด
        จะทำงานในเธรดแยกและพยายามอัปโหลดบันทึกที่ค้างอยู่
        """
        while self.running:
            try:
                # Collect logs up to batch size
                logs = []
                for _ in range(self.batch_size):
                    try:
                        log = self.upload_queue.get(block=True, timeout=0.1)
                        logs.append(log)
                    except queue.Empty:
                        break
                
                # Upload batch if we have logs
                if logs:
                    success = self.upload_batch(logs)
                    if success:
                        for _ in range(len(logs)):
                            self.upload_queue.task_done()
                    else:
                        # Put logs back in queue if upload failed
                        for log in logs:
                            self.upload_queue.put(log)
                        # Wait before retry
                        time.sleep(self.retry_interval)
                        # Try to reconnect
                        if self.offline_mode:
                            self._init_firebase()
                else:
                    # No logs to upload, check if we need to reconnect
                    if self.offline_mode:
                        # Only try to reconnect periodically
                        time.sleep(self.retry_interval)
                        self._init_firebase()
                    else:
                        # Just a short sleep to prevent CPU spinning
                        time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in upload worker: {e}")
                time.sleep(self.retry_interval)
    
    def flush(self) -> None:
        """
        บังคับให้อัปโหลดบันทึกที่ค้างอยู่ทั้งหมด
        """
        if not self.running or self.offline_mode:
            return
        
        # If queue is not empty, upload whatever is left
        if not self.upload_queue.empty():
            # Collect remaining logs
            logs = []
            try:
                while True:
                    logs.append(self.upload_queue.get(block=False))
            except queue.Empty:
                pass
            
            # Upload remaining logs
            if logs:
                self.upload_batch(logs)
    
    def stop(self) -> None:
        """
        หยุดตัวอัปโหลดและรอให้เธรดอัปโหลดเสร็จสิ้น
        """
        self.running = False
        if self.upload_thread.is_alive():
            self.upload_thread.join(timeout=5.0)

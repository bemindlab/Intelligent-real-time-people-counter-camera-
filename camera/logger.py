#!/usr/bin/env python3
"""
โมดูลการบันทึกข้อมูลสำหรับระบบ MANTA
(Logging module for MANTA system)

ใช้สำหรับบันทึกกิจกรรมและเหตุการณ์ที่เกิดขึ้นในระบบ
รองรับการเก็บบันทึกข้อมูลทั้งในเครื่องและฐานข้อมูลออนไลน์
"""

import json
import logging
import os
import datetime
from typing import Dict, Any, List, Optional

class ActivityLogger:
    """
    ตัวบันทึกกิจกรรมของ MANTA รองรับทั้งบันทึกระบบและบันทึกกิจกรรม
    """
    
    def __init__(self, 
                 local_path: str, 
                 camera_id: str,
                 log_level: str = "INFO",
                 retention_days: int = 7):
        """
        เริ่มต้นตัวบันทึกกิจกรรม
        
        Args:
            local_path: พาธไปยังไฟล์บันทึกในเครื่อง
            camera_id: รหัสกล้อง
            log_level: ระดับการบันทึก (DEBUG, INFO, WARNING, ERROR)
            retention_days: จำนวนวันที่จะเก็บบันทึก
        """
        self.local_path = local_path
        self.camera_id = camera_id
        self.retention_days = retention_days
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(local_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Initialize Python logger
        self.logger = logging.getLogger(f"MANTA-{camera_id}")
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # Add console handler
        ch = logging.StreamHandler()
        ch.setLevel(numeric_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        # Add file handler
        fh = logging.FileHandler(os.path.join(log_dir, f"manta_system_{camera_id}.log"))
        fh.setLevel(numeric_level)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Initialize JSON log file if it doesn't exist
        if not os.path.exists(local_path):
            with open(local_path, 'w') as f:
                json.dump([], f)
        
        # Load existing logs
        try:
            with open(local_path, 'r') as f:
                self.activity_logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.activity_logs = []
        
        # Clean old logs
        self._clean_old_logs()
        
        self.info(f"Logger initialized for camera {camera_id}")
    
    def log_person(self, log_entry: Dict[str, Any]) -> None:
        """
        บันทึกเหตุการณ์การตรวจจับบุคคล
        
        Args:
            log_entry: พจนานุกรมที่มีรายละเอียดบันทึก
        """
        # Add additional information to the log entry
        log_entry["record_time"] = datetime.datetime.now().isoformat()
        if "camera_id" not in log_entry:
            log_entry["camera_id"] = self.camera_id
        
        # Add to in-memory log
        self.activity_logs.append(log_entry)
        
        # Log to system log
        self.info(f"Person detected: {log_entry['person_hash']}")
        
        # Save to file
        self._save_logs()
    
    def get_recent_logs(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        ดึงบันทึกล่าสุด
        
        Args:
            count: จำนวนบันทึกที่ต้องการ
            
        Returns:
            รายการบันทึกล่าสุด
        """
        return self.activity_logs[-count:]
    
    def _save_logs(self) -> None:
        """
        Save logs to JSON file.
        """
        try:
            with open(self.local_path, 'w') as f:
                json.dump(self.activity_logs, f, indent=2)
        except Exception as e:
            self.error(f"Failed to save logs: {e}")
    
    def _clean_old_logs(self) -> None:
        """
        Remove logs older than retention_days.
        """
        if not self.activity_logs:
            return
        
        cutoff = (datetime.datetime.now() - 
                  datetime.timedelta(days=self.retention_days)).isoformat()
        
        # Filter logs to keep only those newer than cutoff
        self.activity_logs = [
            log for log in self.activity_logs 
            if log.get("record_time", log.get("timestamp", "")) >= cutoff
        ]
        
        # Save updated logs
        self._save_logs()
    
    # Proxy methods to Python logger
    def debug(self, message: str) -> None:
        """
Log a debug message.
        """
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """
Log an info message.
        """
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """
Log a warning message.
        """
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """
Log an error message.
        """
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """
Log a critical message.
        """
        self.logger.critical(message)

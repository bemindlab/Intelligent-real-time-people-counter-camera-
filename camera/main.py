#!/usr/bin/env python3
"""
MANTA - ระบบตรวจจับและวิเคราะห์การเคลื่อนไหวของบุคคล
(Monitoring and Analytics Node for Tracking Activity)
สคริปต์หลักสำหรับการเรียกใช้ระบบตรวจจับและติดตามบุคคล

พัฒนาโดย: BemindTech
เวอร์ชัน: 1.0
สำหรับใช้กับ: Raspberry Pi 5 Model B
"""

import argparse
import os
import sys
import time
import yaml
import cv2
import numpy as np
from datetime import datetime

# Add the parent directory to sys.path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import local modules
from camera.detection import PersonDetector
from camera.reid import PersonReIdentifier
from camera.logger import ActivityLogger
from camera.uploader import FirebaseUploader
from utils.camera_utils import setup_camera


class MANTASystem:
    """
    คลาสหลักของระบบ MANTA ที่ประสานการทำงานของทุกส่วนประกอบ
    """
    
    def __init__(self, config_path=None, debug=False, no_upload=False, encryption_key=None):
        """
        เริ่มต้นระบบ MANTA
        
        Args:
            config_path (str): พาธไปยังไฟล์การตั้งค่า
            debug (bool): เปิดใช้งานโหมดดีบัก
            no_upload (bool): ปิดการอัปโหลดไปยัง Firebase
            encryption_key (str): รหัสการเข้ารหัสสำหรับข้อมูลที่สำคัญ (ถ้ามี)
        """
        self.debug = debug
        self.no_upload = no_upload
        self.encryption_key = encryption_key
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.detector = PersonDetector(
            model_path=self.config['detection']['model_path'],
            confidence_threshold=self.config['detection']['confidence_threshold'],
            nms_threshold=self.config['detection']['nms_threshold'],
            device=self.config['detection']['device'],
            classes=self.config['detection']['classes']
        )
        
        self.reidentifier = PersonReIdentifier(
            feature_size=self.config['reid']['feature_size'],
            similarity_threshold=self.config['reid']['similarity_threshold'],
            retention_period=self.config['reid']['retention_period'],
            max_stored_vectors=self.config['reid']['max_stored_vectors']
        )
        
        self.logger = ActivityLogger(
            local_path=self.config['logging']['local_path'],
            camera_id=self.config['camera']['id'],
            log_level="DEBUG" if self.debug else self.config['logging']['log_level'],
            retention_days=self.config['logging']['retention_days']
        )
        
        self.uploader = None
        if not self.no_upload and self.config['firebase']['enabled']:
            self.uploader = FirebaseUploader(
                config_path=self.config['firebase']['config_path'],
                database_url=self.config['firebase']['database_url'],
                path_prefix=self.config['firebase']['path_prefix'],
                camera_id=self.config['camera']['id'],
                retry_interval=self.config['firebase']['retry_interval'],
                batch_size=self.config['firebase']['batch_size']
            )
        
        # Setup camera
        self.camera = setup_camera(
            source=self.config['camera']['source'],
            width=self.config['camera']['resolution']['width'],
            height=self.config['camera']['resolution']['height'],
            fps=self.config['camera']['fps']
        )
        
        # Runtime variables
        self.running = False
        self.frame_count = 0
        self.person_count = 0
        self.start_time = None
        
        self.logger.info(f"MANTA system initialized. Camera ID: {self.config['camera']['id']}")
        
    def _load_config(self, config_path):
        """Load configuration from YAML file."""
        if config_path is None:
            # Default config path
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'config',
                'config.yaml'
            )
        
        try:
            # Try to import config utilities for secure loading
            try:
                from utils.config_utils import ConfigManager
                
                # Use ConfigManager to handle potential encrypted fields
                config_manager = ConfigManager(config_path, self.encryption_key)
                config = config_manager.config_data
            except ImportError:
                # Fall back to standard loading if config_utils not available
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
            
            return config
        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def run(self):
        """Run the MANTA system in continuous mode."""
        self.running = True
        self.start_time = time.time()
        self.logger.info("MANTA system started")
        
        try:
            while self.running:
                success, frame = self.camera.read()
                if not success:
                    self.logger.error("Failed to read from camera")
                    time.sleep(1)
                    continue
                
                self.frame_count += 1
                
                # Detect people in the frame
                detections = self.detector.detect(frame)
                
                # Process each detected person
                for detection in detections:
                    person_img = self._crop_person(frame, detection)
                    
                    # Generate feature vector for re-identification
                    is_new_person, person_hash = self.reidentifier.process(person_img)
                    
                    # If this is a new person, log and upload
                    if is_new_person:
                        self.person_count += 1
                        
                        # Log locally
                        log_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "person_hash": person_hash,
                            "camera_id": self.config['camera']['id']
                        }
                        self.logger.log_person(log_entry)
                        
                        # Upload to Firebase if enabled
                        if self.uploader:
                            self.uploader.upload_log(log_entry)
                
                # Display debug information if enabled
                if self.debug:
                    self._show_debug_info(frame, detections)
                
                # Process key presses
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key
                    break
                
                # Calculate FPS
                elapsed_time = time.time() - self.start_time
                fps = self.frame_count / elapsed_time
                
                # Display performance information
                if self.debug and self.frame_count % 30 == 0:
                    self.logger.debug(f"FPS: {fps:.2f}, Total persons: {self.person_count}")
            
        except KeyboardInterrupt:
            self.logger.info("MANTA system stopped by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the MANTA system."""
        self.running = False
        if self.camera is not None:
            self.camera.release()
        cv2.destroyAllWindows()
        self.logger.info("MANTA system stopped")
        
        # Final upload if enabled
        if self.uploader:
            self.uploader.flush()
    
    def _crop_person(self, frame, detection):
        """Crop the person from the frame using detection coordinates."""
        x1, y1, x2, y2, conf, class_id = detection
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Ensure coordinates are within frame boundaries
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w-1, x2), min(h-1, y2)
        
        # Crop person from frame
        person_img = frame[y1:y2, x1:x2]
        return person_img
    
    def _show_debug_info(self, frame, detections):
        """Display debug information on the frame."""
        for x1, y1, x2, y2, conf, class_id in detections:
            # Draw bounding box
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Add label
            label = f"Person: {conf:.2f}"
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Add system info
        elapsed_time = time.time() - self.start_time
        fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0
        
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, f"People: {self.person_count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        if self.no_upload:
            cv2.putText(frame, "UPLOAD DISABLED", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Show the frame
        cv2.imshow("MANTA Detection", frame)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MANTA - Monitoring and Analytics Node for Tracking Activity")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-upload", action="store_true", help="Disable uploading to Firebase")
    parser.add_argument("--encrypt-key", type=str, help="Encryption key for sensitive configuration")
    parser.add_argument("--encrypt-key-file", type=str, help="File containing encryption key")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    # Get encryption key if provided
    encryption_key = None
    if args.encrypt_key:
        encryption_key = args.encrypt_key
    elif args.encrypt_key_file:
        try:
            with open(args.encrypt_key_file, 'r') as f:
                encryption_key = f.read().strip()
        except Exception as e:
            print(f"Error reading encryption key file: {e}")
    
    # Create MANTA system
    manta = MANTASystem(
        config_path=args.config,
        debug=args.debug,
        no_upload=args.no_upload,
        encryption_key=encryption_key
    )
    
    # Run the system
    manta.run()
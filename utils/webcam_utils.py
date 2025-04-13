#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
อรรถประโยชน์สำหรับการเชื่อมต่อกับกล้องผ่าน WebCam Protocol
รองรับการเชื่อมต่อกับกล้อง Insta360 Go 3S ผ่าน WiFi
"""

import os
import time
import logging
import subprocess
import threading
import cv2
import numpy as np
import yaml
import netifaces
import wifi

logger = logging.getLogger(__name__)

class WebcamConnection:
    """จัดการการเชื่อมต่อกับกล้องผ่าน WebCam Protocol"""
    
    def __init__(self, config_path=None, config=None):
        """
        เริ่มต้นตัวจัดการการเชื่อมต่อกล้อง WebCam
        
        Args:
            config_path (str, optional): พาธไปยังไฟล์การกำหนดค่า
            config (dict, optional): การกำหนดค่าที่ระบุโดยตรง
        """
        self.config = config
        if config_path and not config:
            try:
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"ไม่สามารถโหลดการกำหนดค่าได้: {e}")
                self.config = {}
        
        # การกำหนดค่าเริ่มต้น
        self.camera_url = self.config.get('camera', {}).get('source', 'rtmp://192.168.42.1:1935/live/stream')
        self.retry_interval = self.config.get('camera', {}).get('retry_interval', 5)
        self.connection_timeout = self.config.get('camera', {}).get('connection_timeout', 10)
        
        # การกำหนดค่า WiFi
        self.wifi_config = self.config.get('wifi', {})
        self.wifi_enabled = self.wifi_config.get('enabled', False)
        self.camera_ssid = self.wifi_config.get('camera_ssid', 'Insta360GO3S_XXXX')
        self.camera_password = self.wifi_config.get('camera_password', 'Insta!360')
        self.backup_ssid = self.wifi_config.get('backup_network_ssid', '')
        self.backup_password = self.wifi_config.get('backup_network_password', '')
        
        # สถานะการเชื่อมต่อ
        self.cap = None
        self.connected = False
        self.should_reconnect = True
        self.reconnect_thread = None
        self.last_frame = None
        self.last_frame_time = 0
        
        # ตรวจสอบการติดตั้ง NetworkManager หรือ wpa_supplicant
        self._check_wifi_tools()
    
    def _check_wifi_tools(self):
        """ตรวจสอบเครื่องมือการจัดการ WiFi ที่มีอยู่"""
        self.nm_available = os.path.exists('/usr/bin/nmcli')
        self.wpa_available = os.path.exists('/usr/bin/wpa_cli')
        
        if self.wifi_enabled and not (self.nm_available or self.wpa_available):
            logger.warning("ไม่พบเครื่องมือจัดการ WiFi (NetworkManager หรือ wpa_supplicant) "
                          "การเชื่อมต่อ WiFi อัตโนมัติจะไม่สามารถใช้งานได้")
    
    def connect_to_camera_wifi(self):
        """เชื่อมต่อกับเครือข่าย WiFi ของกล้อง"""
        if not self.wifi_enabled:
            return True
        
        if not (self.nm_available or self.wpa_available):
            logger.error("ไม่สามารถเชื่อมต่อกับ WiFi ของกล้องเนื่องจากไม่มีเครื่องมือจัดการ WiFi")
            return False
        
        try:
            logger.info(f"กำลังเชื่อมต่อกับเครือข่าย WiFi ของกล้อง: {self.camera_ssid}")
            
            if self.nm_available:
                # ใช้ NetworkManager
                result = subprocess.run(
                    ['sudo', 'nmcli', 'device', 'wifi', 'connect', self.camera_ssid, 
                     'password', self.camera_password],
                    capture_output=True, text=True, timeout=30
                )
                success = "successfully activated" in result.stdout or "already connected" in result.stdout
            else:
                # ใช้ wpa_supplicant
                # สร้างไฟล์การกำหนดค่า wpa_supplicant
                wpa_config = f'''network={{
                    ssid="{self.camera_ssid}"
                    psk="{self.camera_password}"
                    key_mgmt=WPA-PSK
                }}'''
                
                with open('/tmp/wpa_supplicant.conf', 'w') as f:
                    f.write(wpa_config)
                
                # รับรายการอินเทอร์เฟซ WiFi
                wlan_interfaces = [i for i in netifaces.interfaces() if i.startswith('wlan')]
                if not wlan_interfaces:
                    logger.error("ไม่พบอินเทอร์เฟซ WiFi")
                    return False
                
                wlan_if = wlan_interfaces[0]
                
                # เชื่อมต่อโดยใช้ wpa_supplicant
                subprocess.run(['sudo', 'wpa_supplicant', '-B', '-i', wlan_if, 
                                '-c', '/tmp/wpa_supplicant.conf'], timeout=10)
                time.sleep(2)  # รอให้การเชื่อมต่อทำงาน
                
                # รับ IP จาก DHCP
                subprocess.run(['sudo', 'dhclient', wlan_if], timeout=10)
                
                # ตรวจสอบการเชื่อมต่อ
                result = subprocess.run(['iwconfig', wlan_if], capture_output=True, text=True)
                success = self.camera_ssid in result.stdout
            
            if success:
                logger.info(f"เชื่อมต่อกับ {self.camera_ssid} สำเร็จ")
                return True
            else:
                logger.error(f"ไม่สามารถเชื่อมต่อกับ {self.camera_ssid}")
                return False
                
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดขณะเชื่อมต่อกับ WiFi ของกล้อง: {e}")
            return False
    
    def connect_to_backup_wifi(self):
        """เชื่อมต่อกับเครือข่าย WiFi สำรอง"""
        if not self.wifi_enabled or not self.backup_ssid:
            return False
        
        if not (self.nm_available or self.wpa_available):
            logger.error("ไม่สามารถเชื่อมต่อกับ WiFi สำรองเนื่องจากไม่มีเครื่องมือจัดการ WiFi")
            return False
        
        try:
            logger.info(f"กำลังเชื่อมต่อกับเครือข่าย WiFi สำรอง: {self.backup_ssid}")
            
            if self.nm_available:
                # ใช้ NetworkManager
                result = subprocess.run(
                    ['sudo', 'nmcli', 'device', 'wifi', 'connect', self.backup_ssid, 
                     'password', self.backup_password],
                    capture_output=True, text=True, timeout=30
                )
                success = "successfully activated" in result.stdout or "already connected" in result.stdout
            else:
                # ใช้ wpa_supplicant (คล้ายกับ connect_to_camera_wifi)
                # ...
                success = False  # ในที่นี้จะละการเขียนโค้ดที่ซ้ำซ้อน
                
            if success:
                logger.info(f"เชื่อมต่อกับ {self.backup_ssid} สำเร็จ")
                return True
            else:
                logger.error(f"ไม่สามารถเชื่อมต่อกับ {self.backup_ssid}")
                return False
                
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดขณะเชื่อมต่อกับ WiFi สำรอง: {e}")
            return False
    
    def connect(self):
        """เชื่อมต่อกับกล้อง"""
        if self.connected and self.cap is not None and self.cap.isOpened():
            return True
        
        # เชื่อมต่อกับ WiFi ของกล้องถ้าเปิดใช้งาน
        if self.wifi_enabled:
            wifi_connected = self.connect_to_camera_wifi()
            if not wifi_connected:
                logger.warning("ไม่สามารถเชื่อมต่อกับ WiFi ของกล้อง จะใช้การตั้งค่าเครือข่ายปัจจุบัน")
        
        logger.info(f"กำลังเชื่อมต่อกับกล้องที่ URL: {self.camera_url}")
        
        try:
            # ตั้งค่า OpenCV VideoCapture สำหรับสตรีม RTMP
            self.cap = cv2.VideoCapture(self.camera_url)
            
            # ตั้งค่าคุณสมบัติเพิ่มเติม
            if self.config.get('camera', {}).get('enable_hardware_decode', False):
                # เปิดใช้การถอดรหัสด้วยฮาร์ดแวร์ถ้ามี
                self.cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
            
            # ตั้งค่าความละเอียด
            width = self.config.get('camera', {}).get('resolution', {}).get('width', 1920)
            height = self.config.get('camera', {}).get('resolution', {}).get('height', 1080)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # ตั้งค่า FPS
            fps = self.config.get('camera', {}).get('fps', 30)
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            
            # ตรวจสอบว่าการเชื่อมต่อสำเร็จหรือไม่โดยการอ่านเฟรมแรก
            start_time = time.time()
            success = False
            
            while time.time() - start_time < self.connection_timeout:
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    success = True
                    self.last_frame = frame
                    self.last_frame_time = time.time()
                    break
                time.sleep(0.5)
            
            if not success:
                logger.error(f"ไม่สามารถเชื่อมต่อกับกล้องที่ URL: {self.camera_url}")
                self.disconnect()
                return False
            
            self.connected = True
            logger.info(f"เชื่อมต่อกับกล้องสำเร็จ ความละเอียด: {int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            
            # เริ่มวงเวียนลูปเชื่อมต่อใหม่ในเธรดแยกต่างหาก
            self.should_reconnect = True
            if self.reconnect_thread is None or not self.reconnect_thread.is_alive():
                self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
                self.reconnect_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดขณะเชื่อมต่อกับกล้อง: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """ตัดการเชื่อมต่อจากกล้อง"""
        self.connected = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        logger.info("ตัดการเชื่อมต่อจากกล้องแล้ว")
    
    def _reconnect_loop(self):
        """ลูปที่ตรวจสอบการเชื่อมต่อและทำการเชื่อมต่อใหม่หากจำเป็น"""
        while self.should_reconnect:
            if not self.connected or self.cap is None or not self.cap.isOpened():
                logger.info("ตรวจพบการขาดการเชื่อมต่อ กำลังพยายามเชื่อมต่อใหม่...")
                self.disconnect()  # ตัดการเชื่อมต่อที่อาจทำงานไม่ถูกต้อง
                self.connect()
            elif time.time() - self.last_frame_time > 10:  # หากไม่ได้รับเฟรมเป็นเวลา 10 วินาที
                logger.warning("ไม่ได้รับเฟรมล่าสุดเป็นเวลา 10 วินาที กำลังเชื่อมต่อใหม่...")
                self.disconnect()
                self.connect()
            
            # ตรวจสอบการเชื่อมต่อ WiFi เป็นระยะ
            if self.wifi_enabled and self.wifi_config.get('auto_reconnect', True):
                wifi_check_interval = self.wifi_config.get('connection_check_interval', 30)
                if int(time.time()) % wifi_check_interval == 0:
                    self._check_wifi_connection()
            
            time.sleep(self.retry_interval)
    
    def _check_wifi_connection(self):
        """ตรวจสอบการเชื่อมต่อ WiFi และเชื่อมต่อใหม่ถ้าจำเป็น"""
        if not (self.nm_available or self.wpa_available):
            return
        
        try:
            # ตรวจสอบว่ากำลังเชื่อมต่อกับเครือข่ายที่ถูกต้องหรือไม่
            if self.nm_available:
                result = subprocess.run(['nmcli', '-t', '-f', 'active,ssid', 'device', 'wifi'],
                                    capture_output=True, text=True, timeout=5)
                connected_to_camera = f"yes:{self.camera_ssid}" in result.stdout
            else:
                # ใช้ wpa_supplicant
                wlan_interfaces = [i for i in netifaces.interfaces() if i.startswith('wlan')]
                if wlan_interfaces:
                    result = subprocess.run(['iwconfig', wlan_interfaces[0]], 
                                        capture_output=True, text=True, timeout=5)
                    connected_to_camera = self.camera_ssid in result.stdout
                else:
                    connected_to_camera = False
            
            if not connected_to_camera and self.connected:
                logger.warning("ขาดการเชื่อมต่อ WiFi ของกล้อง กำลังพยายามเชื่อมต่อใหม่...")
                self.disconnect()
                self.connect_to_camera_wifi()
                self.connect()
                
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดขณะตรวจสอบการเชื่อมต่อ WiFi: {e}")
    
    def read(self):
        """
        อ่านเฟรมจากกล้อง
        
        Returns:
            tuple: (success, frame) คล้ายกับ cv2.VideoCapture.read()
        """
        if not self.connected or self.cap is None or not self.cap.isOpened():
            if not self.connect():
                return False, None
        
        try:
            ret, frame = self.cap.read()
            if ret and frame is not None and frame.size > 0:
                self.last_frame = frame.copy()
                self.last_frame_time = time.time()
                return True, frame
            else:
                # เกิดข้อผิดพลาดในการอ่านเฟรม ส่งคืนเฟรมล่าสุดที่สำเร็จถ้ามี
                if self.last_frame is not None:
                    logger.warning("ไม่สามารถอ่านเฟรมใหม่ได้ ส่งคืนเฟรมล่าสุด")
                    return True, self.last_frame
                else:
                    logger.error("ไม่สามารถอ่านเฟรมได้และไม่มีเฟรมล่าสุด")
                    return False, None
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดขณะอ่านเฟรมจากกล้อง: {e}")
            # เกิดข้อผิดพลาด ส่งคืนเฟรมล่าสุดที่สำเร็จถ้ามี
            if self.last_frame is not None:
                return True, self.last_frame
            else:
                return False, None
    
    def get_camera_properties(self):
        """
        รับคุณสมบัติของกล้อง
        
        Returns:
            dict: คุณสมบัติของกล้อง (ความกว้าง, ความสูง, FPS)
        """
        if not self.connected or self.cap is None:
            return {
                'width': self.config.get('camera', {}).get('resolution', {}).get('width', 1920),
                'height': self.config.get('camera', {}).get('resolution', {}).get('height', 1080),
                'fps': self.config.get('camera', {}).get('fps', 30)
            }
        
        try:
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            return {
                'width': width,
                'height': height,
                'fps': fps
            }
        except:
            return {
                'width': 0,
                'height': 0,
                'fps': 0
            }
    
    def __del__(self):
        """ตัวทำลายออบเจ็กต์"""
        self.should_reconnect = False
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            self.reconnect_thread.join(timeout=1.0)
        self.disconnect()


def create_insta360_connection(config=None):
    """
    สร้างการเชื่อมต่อกับกล้อง Insta360 Go 3S
    
    Args:
        config (dict, optional): การกำหนดค่าที่กำหนดเอง
    
    Returns:
        WebcamConnection: อ็อบเจกต์การเชื่อมต่อ WebCam
    """
    if config is None:
        # ใช้การกำหนดค่าเริ่มต้นสำหรับ Insta360
        config = {
            'camera': {
                'source': 'rtmp://192.168.42.1:1935/live/stream',
                'resolution': {'width': 1920, 'height': 1080},
                'fps': 30,
                'retry_interval': 5,
                'connection_timeout': 10,
                'enable_hardware_decode': True
            },
            'wifi': {
                'enabled': True,
                'camera_ssid': 'Insta360GO3S_XXXX',  # ต้องแก้ไขตามกล้องของคุณ
                'camera_password': 'Insta!360',
                'connection_check_interval': 30,
                'auto_reconnect': True
            }
        }
    
    return WebcamConnection(config=config)


def test_insta360_connection(config_path=None):
    """
    ทดสอบการเชื่อมต่อกับกล้อง Insta360 Go 3S
    
    Args:
        config_path (str, optional): พาธไปยังไฟล์การกำหนดค่า
    """
    if config_path:
        connection = WebcamConnection(config_path=config_path)
    else:
        connection = create_insta360_connection()
    
    print("กำลังทดสอบการเชื่อมต่อกับ Insta360 Go 3S...")
    if connection.connect():
        print("เชื่อมต่อสำเร็จ!")
        props = connection.get_camera_properties()
        print(f"คุณสมบัติของกล้อง: ความละเอียด {props['width']}x{props['height']}, FPS: {props['fps']}")
        
        print("กำลังแสดงภาพจากกล้อง กด 'q' เพื่อออก...")
        try:
            while True:
                ret, frame = connection.read()
                if ret:
                    # ลดขนาดของเฟรมเพื่อการแสดงผล
                    scale = min(1.0, 800 / props['width'])
                    display_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
                    
                    cv2.imshow('Insta360 Go 3S Test', display_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    print("ไม่สามารถอ่านเฟรมได้ กำลังลองใหม่...")
                    time.sleep(1)
        finally:
            cv2.destroyAllWindows()
            connection.disconnect()
    else:
        print("ไม่สามารถเชื่อมต่อกับกล้องได้")


if __name__ == "__main__":
    # ตั้งค่าการบันทึก
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ทดสอบการเชื่อมต่อ
    import argparse
    parser = argparse.ArgumentParser(description='ทดสอบการเชื่อมต่อกับกล้อง Insta360 Go 3S')
    parser.add_argument('--config', help='พาธไปยังไฟล์การกำหนดค่า')
    args = parser.parse_args()
    
    test_insta360_connection(args.config)
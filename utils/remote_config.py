#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ระบบการกำหนดค่าระยะไกลสำหรับ MANTA Camera ผ่าน HTTP protocol และ WiFi Direct
"""

import os
import json
import logging
import threading
import time
import yaml
import socket
import ipaddress
import subprocess
import netifaces
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Flask สำหรับ HTTP API
try:
    from flask import Flask, request, jsonify, send_file, render_template_string
    from flask_cors import CORS
    from werkzeug.serving import make_server
    from werkzeug.utils import secure_filename
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# Zeroconf สำหรับการค้นพบอัตโนมัติ
try:
    from zeroconf import ServiceInfo, Zeroconf
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False

# ตั้งค่าการบันทึก
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("manta.remote_config")

# HTML Template สำหรับหน้า UI ง่ายๆ
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MANTA Remote Configuration</title>
    <style>
        body {
            font-family: 'Sarabun', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #008080;
            margin-top: 0;
        }
        .section {
            margin-bottom: 30px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 8px;
        }
        h2 {
            margin-top: 0;
            color: #006666;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 8px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        input[type="checkbox"] {
            width: auto;
        }
        button {
            background-color: #008080;
            color: white;
            border: none;
            padding: 10px 15px;
            cursor: pointer;
            border-radius: 4px;
            font-weight: bold;
        }
        button:hover {
            background-color: #006666;
        }
        .status {
            margin-top: 20px;
            padding: 10px;
            border-radius: 4px;
        }
        .success {
            background-color: #dff0d8;
            color: #3c763d;
        }
        .error {
            background-color: #f2dede;
            color: #a94442;
        }
        .row {
            display: flex;
            margin-bottom: 15px;
        }
        .col {
            flex: 1;
            padding-right: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .card {
            background-color: white;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .action-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .action-buttons button {
            flex: 1;
        }
        .secondary {
            background-color: #6c757d;
        }
        .secondary:hover {
            background-color: #5a6268;
        }
        .danger {
            background-color: #dc3545;
        }
        .danger:hover {
            background-color: #c82333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>MANTA Remote Configuration</h1>
        <div id="status"></div>
        
        <div class="section">
            <h2>ข้อมูลอุปกรณ์</h2>
            <div class="card">
                <p><strong>ชื่ออุปกรณ์:</strong> <span id="device-name">กำลังโหลด...</span></p>
                <p><strong>รหัสกล้อง:</strong> <span id="camera-id">กำลังโหลด...</span></p>
                <p><strong>IP Address:</strong> <span id="ip-address">กำลังโหลด...</span></p>
                <p><strong>สถานะระบบ:</strong> <span id="system-status">กำลังโหลด...</span></p>
            </div>
        </div>
        
        <div class="section">
            <h2>การตั้งค่ากล้อง</h2>
            <div class="row">
                <div class="col">
                    <label for="camera-source">แหล่งกล้อง:</label>
                    <input type="text" id="camera-source" placeholder="0 หรือ URL">
                </div>
                <div class="col">
                    <label for="camera-type">ประเภทกล้อง:</label>
                    <select id="camera-type">
                        <option value="standard">มาตรฐาน</option>
                        <option value="webcam">WebCam Protocol</option>
                        <option value="picamera">Raspberry Pi Camera</option>
                    </select>
                </div>
            </div>
            
            <div class="row">
                <div class="col">
                    <label for="camera-width">ความกว้าง:</label>
                    <input type="number" id="camera-width" placeholder="640">
                </div>
                <div class="col">
                    <label for="camera-height">ความสูง:</label>
                    <input type="number" id="camera-height" placeholder="480">
                </div>
                <div class="col">
                    <label for="camera-fps">FPS:</label>
                    <input type="number" id="camera-fps" placeholder="15">
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>การตั้งค่าการตรวจจับ</h2>
            <div class="row">
                <div class="col">
                    <label for="detection-model">โมเดล:</label>
                    <select id="detection-model">
                        <option value="models/yolov8n.onnx">YOLOv8n (เล็ก)</option>
                        <option value="models/yolov8s.onnx">YOLOv8s (กลาง)</option>
                        <option value="models/yolov8m.onnx">YOLOv8m (ใหญ่)</option>
                    </select>
                </div>
                <div class="col">
                    <label for="detection-confidence">ค่าความเชื่อมั่นขั้นต่ำ:</label>
                    <input type="number" id="detection-confidence" min="0" max="1" step="0.05" placeholder="0.5">
                </div>
            </div>
            
            <div class="row">
                <div class="col">
                    <label for="detection-device">อุปกรณ์ประมวลผล:</label>
                    <select id="detection-device">
                        <option value="CPU">CPU</option>
                        <option value="NPU">NPU (Raspberry Pi 5)</option>
                        <option value="CUDA">CUDA (NVIDIA GPU)</option>
                    </select>
                </div>
                <div class="col">
                    <label for="detection-frame-skip">การข้ามเฟรม:</label>
                    <input type="number" id="detection-frame-skip" min="0" max="10" placeholder="0">
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>การตั้งค่าเครือข่าย</h2>
            <div class="row">
                <div class="col">
                    <label for="firebase-enabled">
                        <input type="checkbox" id="firebase-enabled"> เปิดใช้งาน Firebase
                    </label>
                </div>
            </div>
            
            <div id="firebase-settings" style="display:none;">
                <div class="row">
                    <div class="col">
                        <label for="firebase-url">Firebase URL:</label>
                        <input type="text" id="firebase-url" placeholder="https://your-project.firebaseio.com">
                    </div>
                </div>
                
                <div class="row">
                    <div class="col">
                        <label for="firebase-config-file">อัปโหลดไฟล์ Firebase Config:</label>
                        <input type="file" id="firebase-config-file">
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>WiFi Direct</h2>
            <div class="row">
                <div class="col">
                    <label for="wifi-direct-enabled">
                        <input type="checkbox" id="wifi-direct-enabled"> เปิดใช้งาน WiFi Direct
                    </label>
                </div>
            </div>
            
            <div id="wifi-direct-settings" style="display:none;">
                <div class="row">
                    <div class="col">
                        <label for="wifi-direct-name">ชื่อ WiFi Direct:</label>
                        <input type="text" id="wifi-direct-name" placeholder="MANTA-Camera">
                    </div>
                    <div class="col">
                        <label for="wifi-direct-password">รหัสผ่าน:</label>
                        <input type="password" id="wifi-direct-password" placeholder="อย่างน้อย 8 ตัวอักษร">
                    </div>
                </div>
            </div>
        </div>
        
        <div class="action-buttons">
            <button id="save-config" type="button">บันทึกการตั้งค่า</button>
            <button id="restart-service" type="button" class="secondary">รีสตาร์ทบริการ</button>
            <button id="reboot-device" type="button" class="danger">รีบูตอุปกรณ์</button>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // โหลดการตั้งค่าเมื่อเริ่มต้น
            fetchSystemInfo();
            fetchCurrentConfig();
            
            // แสดง/ซ่อนการตั้งค่า Firebase
            document.getElementById('firebase-enabled').addEventListener('change', function() {
                document.getElementById('firebase-settings').style.display = 
                    this.checked ? 'block' : 'none';
            });
            
            // แสดง/ซ่อนการตั้งค่า WiFi Direct
            document.getElementById('wifi-direct-enabled').addEventListener('change', function() {
                document.getElementById('wifi-direct-settings').style.display = 
                    this.checked ? 'block' : 'none';
            });
            
            // บันทึกการตั้งค่า
            document.getElementById('save-config').addEventListener('click', saveConfig);
            
            // รีสตาร์ทบริการ
            document.getElementById('restart-service').addEventListener('click', function() {
                if (confirm('คุณแน่ใจหรือไม่ว่าต้องการรีสตาร์ทบริการ MANTA?')) {
                    restartService();
                }
            });
            
            // รีบูตอุปกรณ์
            document.getElementById('reboot-device').addEventListener('click', function() {
                if (confirm('คุณแน่ใจหรือไม่ว่าต้องการรีบูตอุปกรณ์?\\n\\nคำเตือน: การรีบูตจะทำให้อุปกรณ์ไม่สามารถใช้งานได้ชั่วคราว')) {
                    rebootDevice();
                }
            });
        });
        
        // ฟังก์ชันสำหรับโหลดข้อมูลระบบ
        function fetchSystemInfo() {
            fetch('/api/system/info')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('device-name').textContent = data.hostname;
                    document.getElementById('camera-id').textContent = data.camera_id;
                    document.getElementById('ip-address').textContent = data.ip_address;
                    document.getElementById('system-status').textContent = data.service_status;
                })
                .catch(error => {
                    showStatus('ไม่สามารถโหลดข้อมูลระบบได้: ' + error, false);
                });
        }
        
        // ฟังก์ชันสำหรับโหลดการตั้งค่าปัจจุบัน
        function fetchCurrentConfig() {
            fetch('/api/config')
                .then(response => response.json())
                .then(data => {
                    // ตั้งค่ากล้อง
                    document.getElementById('camera-source').value = data.camera.source;
                    document.getElementById('camera-type').value = data.camera.type || 'standard';
                    document.getElementById('camera-width').value = data.camera.resolution.width;
                    document.getElementById('camera-height').value = data.camera.resolution.height;
                    document.getElementById('camera-fps').value = data.camera.fps;
                    
                    // ตั้งค่าการตรวจจับ
                    document.getElementById('detection-model').value = data.detection.model_path;
                    document.getElementById('detection-confidence').value = data.detection.confidence_threshold;
                    document.getElementById('detection-device').value = data.detection.device;
                    document.getElementById('detection-frame-skip').value = data.detection.frame_skip || 0;
                    
                    // ตั้งค่า Firebase
                    const firebaseEnabled = data.firebase && data.firebase.enabled;
                    document.getElementById('firebase-enabled').checked = firebaseEnabled;
                    document.getElementById('firebase-settings').style.display = firebaseEnabled ? 'block' : 'none';
                    if (firebaseEnabled && data.firebase.database_url) {
                        document.getElementById('firebase-url').value = data.firebase.database_url;
                    }
                    
                    // ตั้งค่า WiFi Direct
                    const wifiDirectEnabled = data.wifi_direct && data.wifi_direct.enabled;
                    document.getElementById('wifi-direct-enabled').checked = wifiDirectEnabled;
                    document.getElementById('wifi-direct-settings').style.display = wifiDirectEnabled ? 'block' : 'none';
                    if (wifiDirectEnabled) {
                        document.getElementById('wifi-direct-name').value = data.wifi_direct.name || '';
                        // ไม่ตั้งค่ารหัสผ่าน WiFi Direct เพื่อความปลอดภัย
                    }
                })
                .catch(error => {
                    showStatus('ไม่สามารถโหลดการตั้งค่าได้: ' + error, false);
                });
        }
        
        // บันทึกการตั้งค่า
        function saveConfig() {
            // รวบรวมการตั้งค่าจากฟอร์ม
            const config = {
                camera: {
                    source: document.getElementById('camera-source').value,
                    type: document.getElementById('camera-type').value,
                    resolution: {
                        width: parseInt(document.getElementById('camera-width').value),
                        height: parseInt(document.getElementById('camera-height').value)
                    },
                    fps: parseInt(document.getElementById('camera-fps').value)
                },
                detection: {
                    model_path: document.getElementById('detection-model').value,
                    confidence_threshold: parseFloat(document.getElementById('detection-confidence').value),
                    device: document.getElementById('detection-device').value,
                    frame_skip: parseInt(document.getElementById('detection-frame-skip').value)
                },
                firebase: {
                    enabled: document.getElementById('firebase-enabled').checked,
                    database_url: document.getElementById('firebase-url').value
                },
                wifi_direct: {
                    enabled: document.getElementById('wifi-direct-enabled').checked,
                    name: document.getElementById('wifi-direct-name').value,
                    password: document.getElementById('wifi-direct-password').value
                }
            };
            
            // ตรวจสอบไฟล์ Firebase Config
            const firebaseConfigFile = document.getElementById('firebase-config-file').files[0];
            
            // ส่งการตั้งค่า
            if (firebaseConfigFile) {
                const formData = new FormData();
                formData.append('config', JSON.stringify(config));
                formData.append('firebase_config_file', firebaseConfigFile);
                
                fetch('/api/config', {
                    method: 'POST',
                    body: formData
                })
                .then(handleSaveResponse)
                .catch(handleSaveError);
            } else {
                fetch('/api/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(config)
                })
                .then(handleSaveResponse)
                .catch(handleSaveError);
            }
        }
        
        function handleSaveResponse(response) {
            if (response.ok) {
                showStatus('บันทึกการตั้งค่าสำเร็จ', true);
                return response.json();
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || 'เกิดข้อผิดพลาดในการบันทึกการตั้งค่า');
                });
            }
        }
        
        function handleSaveError(error) {
            showStatus(error.message, false);
        }
        
        // รีสตาร์ทบริการ
        function restartService() {
            fetch('/api/system/restart', { method: 'POST' })
                .then(response => {
                    if (response.ok) {
                        showStatus('กำลังรีสตาร์ทบริการ MANTA...', true);
                        setTimeout(fetchSystemInfo, 5000);
                    } else {
                        return response.json().then(data => {
                            throw new Error(data.error || 'ไม่สามารถรีสตาร์ทบริการได้');
                        });
                    }
                })
                .catch(error => {
                    showStatus(error.message, false);
                });
        }
        
        // รีบูตอุปกรณ์
        function rebootDevice() {
            fetch('/api/system/reboot', { method: 'POST' })
                .then(response => {
                    if (response.ok) {
                        showStatus('กำลังรีบูตอุปกรณ์... อาจใช้เวลาประมาณ 1-2 นาที', true);
                    } else {
                        return response.json().then(data => {
                            throw new Error(data.error || 'ไม่สามารถรีบูตอุปกรณ์ได้');
                        });
                    }
                })
                .catch(error => {
                    showStatus(error.message, false);
                });
        }
        
        // แสดงข้อความสถานะ
        function showStatus(message, isSuccess) {
            const statusElement = document.getElementById('status');
            statusElement.className = isSuccess ? 'status success' : 'status error';
            statusElement.textContent = message;
            
            // ซ่อนข้อความหลังจาก 5 วินาที
            setTimeout(() => {
                statusElement.textContent = '';
                statusElement.className = 'status';
            }, 5000);
        }
    </script>
</body>
</html>
"""

class RemoteConfigServer:
    """
    เซิร์ฟเวอร์สำหรับการกำหนดค่าระยะไกลของ MANTA Camera
    ให้บริการ HTTP API และหน้าเว็บสำหรับการจัดการกล้อง
    """

    def __init__(self, 
                 config_path: str, 
                 host: str = '0.0.0.0', 
                 port: int = 8080,
                 device_name: str = 'MANTA-Camera',
                 enable_zeroconf: bool = True,
                 enable_wifi_direct: bool = False,
                 wifi_direct_config: Optional[Dict[str, Any]] = None):
        """
        เริ่มต้นเซิร์ฟเวอร์การกำหนดค่าระยะไกล
        
        Args:
            config_path: พาธไปยังไฟล์การกำหนดค่า YAML
            host: โฮสต์ที่จะให้บริการ (0.0.0.0 สำหรับทุกอินเทอร์เฟซ)
            port: พอร์ตที่จะให้บริการ
            device_name: ชื่ออุปกรณ์สำหรับแสดงและการค้นพบ
            enable_zeroconf: เปิดใช้งานการค้นพบผ่าน Zeroconf/mDNS
            enable_wifi_direct: เปิดใช้งาน WiFi Direct สำหรับการเชื่อมต่อโดยตรง
            wifi_direct_config: การกำหนดค่า WiFi Direct
        """
        # ตรวจสอบว่ามี Flask หรือไม่
        if not FLASK_AVAILABLE:
            logger.error("ไม่พบ Flask ติดตั้งด้วย: pip install flask flask-cors")
            return
        
        # พาธการกำหนดค่า
        self.config_path = config_path
        self.config_backups_dir = os.path.join(os.path.dirname(config_path), "backups")
        os.makedirs(self.config_backups_dir, exist_ok=True)
        
        # การตั้งค่าเซิร์ฟเวอร์
        self.host = host
        self.port = port
        self.device_name = device_name
        
        # ตั้งค่า WiFi Direct
        self.enable_wifi_direct = enable_wifi_direct
        self.wifi_direct_config = wifi_direct_config or {
            "name": f"{device_name}-Direct",
            "password": "manta1234",
            "enabled": False
        }
        
        # โหลดการกำหนดค่าปัจจุบัน
        self.config = self._load_config()
        
        # ตั้งค่า Flask app
        self.app = Flask(__name__)
        CORS(self.app)  # อนุญาต Cross-Origin Resource Sharing
        
        # ตั้งค่าเส้นทาง (routes)
        self._setup_routes()
        
        # เตรียม Server สำหรับ Flask
        self.server = make_server(host, port, self.app)
        self.server_thread = None
        
        # ตั้งค่า Zeroconf สำหรับการค้นพบบริการ
        self.zeroconf = None
        self.zeroconf_info = None
        if enable_zeroconf and ZEROCONF_AVAILABLE:
            self._setup_zeroconf()
        elif enable_zeroconf and not ZEROCONF_AVAILABLE:
            logger.warning("ไม่พบ zeroconf ติดตั้งด้วย: pip install zeroconf")
            
        # ตั้งค่า WiFi Direct ถ้าเปิดใช้งาน
        if self.enable_wifi_direct:
            self._setup_wifi_direct()
            
        logger.info(f"เซิร์ฟเวอร์การกำหนดค่าระยะไกลพร้อมทำงานที่ http://{host}:{port}/")
    
    def _load_config(self) -> Dict[str, Any]:
        """โหลดการกำหนดค่าปัจจุบันจากไฟล์"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"ไม่สามารถโหลดการกำหนดค่าได้: {e}")
            return {}
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """บันทึกการกำหนดค่าไปยังไฟล์"""
        try:
            # สร้างสำเนาสำรอง
            if os.path.exists(self.config_path):
                backup_path = os.path.join(
                    self.config_backups_dir, 
                    f"config_{time.strftime('%Y%m%d_%H%M%S')}.yaml"
                )
                with open(self.config_path, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
            
            # บันทึกการกำหนดค่าใหม่
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            # อัปเดตการกำหนดค่าที่เก็บไว้
            self.config = config
            return True
        except Exception as e:
            logger.error(f"ไม่สามารถบันทึกการกำหนดค่าได้: {e}")
            return False
    
    def _setup_routes(self):
        """ตั้งค่าเส้นทาง API และเว็บ"""
        app = self.app
        
        # หน้าหลัก (UI)
        @app.route('/')
        def index():
            return render_template_string(HTML_TEMPLATE)
        
        # API: รับการกำหนดค่าปัจจุบัน
        @app.route('/api/config', methods=['GET'])
        def get_config():
            return jsonify(self.config)
        
        # API: อัปเดตการกำหนดค่า
        @app.route('/api/config', methods=['POST'])
        def update_config():
            try:
                if request.is_json:
                    # กรณี JSON payload
                    new_config = request.get_json()
                else:
                    # กรณี multipart/form-data
                    new_config = json.loads(request.form.get('config', '{}'))
                    
                    # จัดการการอัปโหลดไฟล์ Firebase Config
                    if 'firebase_config_file' in request.files:
                        file = request.files['firebase_config_file']
                        if file.filename:
                            filename = secure_filename(file.filename)
                            firebase_dir = os.path.join(os.path.dirname(os.path.dirname(self.config_path)), 'firebase')
                            os.makedirs(firebase_dir, exist_ok=True)
                            firebase_config_path = os.path.join(firebase_dir, 'firebase_config.json')
                            file.save(firebase_config_path)
                            
                            # อัปเดตพาธในการกำหนดค่า
                            if 'firebase' not in new_config:
                                new_config['firebase'] = {}
                            new_config['firebase']['config_path'] = firebase_config_path
                
                # ผสานการกำหนดค่าเดิมกับใหม่
                merged_config = self._merge_configs(self.config, new_config)
                
                # บันทึกการกำหนดค่า
                if self._save_config(merged_config):
                    # อัปเดต WiFi Direct ตามการกำหนดค่าใหม่
                    if self.enable_wifi_direct and merged_config.get('wifi_direct', {}).get('enabled', False):
                        wifi_config = merged_config.get('wifi_direct', {})
                        self._update_wifi_direct(wifi_config)
                    
                    return jsonify({"success": True, "message": "บันทึกการกำหนดค่าสำเร็จ"})
                else:
                    return jsonify({"success": False, "error": "ไม่สามารถบันทึกการกำหนดค่าได้"}), 500
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการอัปเดตการกำหนดค่า: {e}")
                return jsonify({"success": False, "error": str(e)}), 400
        
        # API: รับข้อมูลระบบ
        @app.route('/api/system/info', methods=['GET'])
        def get_system_info():
            try:
                # รับข้อมูลระบบพื้นฐาน
                hostname = socket.gethostname()
                ip_address = self._get_ip_address()
                camera_id = self.config.get('camera', {}).get('id', 'unknown')
                
                # ตรวจสอบสถานะบริการ
                service_status = self._check_service_status()
                
                # ตรวจสอบรุ่น Raspberry Pi
                rpi_model = self._get_rpi_model()
                
                # ข้อมูลหน่วยความจำและ CPU
                memory_info = self._get_memory_info()
                cpu_info = self._get_cpu_info()
                
                # ข้อมูลกล้อง
                camera_info = {
                    'type': self.config.get('camera', {}).get('type', 'standard'),
                    'resolution': self.config.get('camera', {}).get('resolution', {'width': 0, 'height': 0}),
                    'fps': self.config.get('camera', {}).get('fps', 0)
                }
                
                return jsonify({
                    'hostname': hostname,
                    'ip_address': ip_address,
                    'camera_id': camera_id,
                    'service_status': service_status,
                    'rpi_model': rpi_model,
                    'memory': memory_info,
                    'cpu': cpu_info,
                    'camera': camera_info
                })
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการรับข้อมูลระบบ: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        
        # API: รีสตาร์ทบริการ
        @app.route('/api/system/restart', methods=['POST'])
        def restart_service():
            try:
                result = self._restart_manta_service()
                if result:
                    return jsonify({"success": True, "message": "รีสตาร์ทบริการสำเร็จ"})
                else:
                    return jsonify({"success": False, "error": "ไม่สามารถรีสตาร์ทบริการได้"}), 500
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการรีสตาร์ทบริการ: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        
        # API: รีบูตอุปกรณ์
        @app.route('/api/system/reboot', methods=['POST'])
        def reboot_device():
            try:
                # ตรวจสอบว่าสามารถรีบูตได้หรือไม่ (ต้องมีสิทธิ์ sudo)
                if not self._can_reboot():
                    return jsonify({"success": False, "error": "ไม่มีสิทธิ์ในการรีบูตอุปกรณ์"}), 403
                
                # เริ่มการรีบูตในเธรดแยกต่างหาก
                thread = threading.Thread(target=self._reboot_system)
                thread.daemon = True
                thread.start()
                
                return jsonify({"success": True, "message": "กำลังรีบูตอุปกรณ์..."})
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการรีบูตอุปกรณ์: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        
        # API: ดาวน์โหลดการกำหนดค่า
        @app.route('/api/config/download', methods=['GET'])
        def download_config():
            try:
                return send_file(self.config_path, as_attachment=True)
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการดาวน์โหลดการกำหนดค่า: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        
        # API: อัปโหลดการกำหนดค่า
        @app.route('/api/config/upload', methods=['POST'])
        def upload_config():
            try:
                if 'config_file' not in request.files:
                    return jsonify({"success": False, "error": "ไม่พบไฟล์การกำหนดค่า"}), 400
                
                file = request.files['config_file']
                if not file or file.filename == '':
                    return jsonify({"success": False, "error": "ไม่พบไฟล์การกำหนดค่า"}), 400
                
                # ตรวจสอบว่าเป็นไฟล์ YAML
                if not file.filename.endswith(('.yaml', '.yml')):
                    return jsonify({"success": False, "error": "ไฟล์ต้องเป็น YAML"}), 400
                
                # บันทึกไฟล์ชั่วคราว
                temp_path = os.path.join(os.path.dirname(self.config_path), "temp_config.yaml")
                file.save(temp_path)
                
                # ตรวจสอบว่าเป็นการกำหนดค่าที่ถูกต้อง
                try:
                    with open(temp_path, 'r') as f:
                        new_config = yaml.safe_load(f)
                    
                    # ตรวจสอบโครงสร้างพื้นฐาน
                    if 'camera' not in new_config or 'detection' not in new_config:
                        raise ValueError("ไฟล์การกำหนดค่าไม่ถูกต้อง (ไม่พบส่วน camera หรือ detection)")
                    
                    # สร้างสำเนาสำรอง
                    backup_path = os.path.join(
                        self.config_backups_dir, 
                        f"config_{time.strftime('%Y%m%d_%H%M%S')}.yaml"
                    )
                    with open(self.config_path, 'r') as src, open(backup_path, 'w') as dst:
                        dst.write(src.read())
                    
                    # ย้ายไฟล์ชั่วคราวไปเป็นการกำหนดค่าใหม่
                    os.replace(temp_path, self.config_path)
                    
                    # โหลดการกำหนดค่าใหม่
                    self.config = self._load_config()
                    
                    return jsonify({"success": True, "message": "อัปโหลดการกำหนดค่าสำเร็จ"})
                except Exception as e:
                    # ลบไฟล์ชั่วคราวในกรณีที่มีข้อผิดพลาด
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise e
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการอัปโหลดการกำหนดค่า: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
    
    def _merge_configs(self, original: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """ผสานการกำหนดค่าเดิมกับการกำหนดค่าใหม่ โดยรักษาโครงสร้างที่ไม่ได้มีการแก้ไข"""
        result = original.copy()
        
        for key, value in update.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                # กรณีค่าเป็น dict ให้ทำการผสานแบบลึก
                result[key] = self._merge_configs(result[key], value)
            else:
                # กรณีอื่นๆ ให้แทนที่ค่าเดิมด้วยค่าใหม่
                result[key] = value
        
        return result
    
    def _setup_zeroconf(self):
        """ตั้งค่า Zeroconf สำหรับการค้นพบบริการ"""
        try:
            self.zeroconf = Zeroconf()
            
            # สร้างข้อมูลบริการ
            ip_address = self._get_ip_address()
            service_name = f"{self.device_name}._http._tcp.local."
            
            self.zeroconf_info = ServiceInfo(
                "_http._tcp.local.",
                service_name,
                addresses=[socket.inet_aton(ip_address)],
                port=self.port,
                properties={
                    'type': 'manta-camera',
                    'name': self.device_name,
                    'path': '/'
                }
            )
            
            # ลงทะเบียนบริการ
            self.zeroconf.register_service(self.zeroconf_info)
            logger.info(f"ลงทะเบียนบริการ Zeroconf: {service_name}")
        except Exception as e:
            logger.error(f"ไม่สามารถตั้งค่า Zeroconf ได้: {e}")
            if self.zeroconf:
                self.zeroconf.close()
                self.zeroconf = None
    
    def _setup_wifi_direct(self):
        """ตั้งค่า WiFi Direct สำหรับการเชื่อมต่อโดยตรง"""
        try:
            # ตรวจสอบว่ามีการเปิดใช้งาน WiFi Direct ในการกำหนดค่าหรือไม่
            wifi_direct_config = self.config.get('wifi_direct', {})
            if wifi_direct_config.get('enabled', False):
                # ใช้การกำหนดค่าจากไฟล์การกำหนดค่า
                self._update_wifi_direct(wifi_direct_config)
            else:
                # ใช้การกำหนดค่าเริ่มต้น
                logger.info("WiFi Direct ไม่ได้เปิดใช้งานในการกำหนดค่า")
        except Exception as e:
            logger.error(f"ไม่สามารถตั้งค่า WiFi Direct ได้: {e}")
    
    def _update_wifi_direct(self, config: Dict[str, Any]):
        """อัปเดตการตั้งค่า WiFi Direct"""
        try:
            if not self.enable_wifi_direct:
                logger.warning("ไม่สามารถอัปเดต WiFi Direct ได้: ฟีเจอร์ไม่ได้เปิดใช้งาน")
                return False
            
            # ตรวจสอบคำสั่งที่จำเป็น
            if not self._check_wifi_direct_commands():
                logger.error("ไม่สามารถอัปเดต WiFi Direct ได้: ไม่พบคำสั่งที่จำเป็น")
                return False
            
            # ดึงค่าจาก config
            name = config.get('name', f"{self.device_name}-Direct")
            password = config.get('password', '')
            
            # ตรวจสอบความยาวรหัสผ่าน (ต้องมีอย่างน้อย 8 ตัวอักษร)
            if password and len(password) < 8:
                logger.error("รหัสผ่าน WiFi Direct ต้องมีอย่างน้อย 8 ตัวอักษร")
                return False
            
            # ตั้งค่า WiFi Direct
            if self._is_raspberrypi():
                # สำหรับ Raspberry Pi
                self._setup_rpi_wifi_direct(name, password)
            else:
                # สำหรับระบบอื่นๆ
                logger.warning("WiFi Direct รองรับเฉพาะ Raspberry Pi")
                return False
            
            return True
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการอัปเดต WiFi Direct: {e}")
            return False
    
    def _check_wifi_direct_commands(self) -> bool:
        """ตรวจสอบว่ามีคำสั่งที่จำเป็นสำหรับ WiFi Direct หรือไม่"""
        commands = ['iw', 'wpa_supplicant', 'wpa_cli']
        missing = []
        
        for cmd in commands:
            if not self._check_command_exists(cmd):
                missing.append(cmd)
        
        if missing:
            logger.warning(f"คำสั่งที่ขาดหายไปสำหรับ WiFi Direct: {', '.join(missing)}")
            logger.warning("ติดตั้งด้วย: sudo apt install wireless-tools wpasupplicant")
            return False
            
        return True
    
    def _setup_rpi_wifi_direct(self, name: str, password: str):
        """ตั้งค่า WiFi Direct บน Raspberry Pi"""
        try:
            # หยุดบริการที่อาจขัดแย้ง
            self._run_command("sudo systemctl stop wpa_supplicant")
            self._run_command("sudo systemctl stop NetworkManager")
            
            # ค้นหาอินเทอร์เฟซ WiFi
            wlan_if = self._get_wifi_interface()
            if not wlan_if:
                logger.error("ไม่พบอินเทอร์เฟซ WiFi")
                return False
            
            # ตั้งค่า WiFi Direct (P2P)
            self._run_command(f"sudo iw dev {wlan_if} interface add p2p-dev-{wlan_if} type managed")
            
            # สร้างไฟล์กำหนดค่า wpa_supplicant.conf
            config_content = f"""
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

# WiFi Direct configuration
ap_scan=1
device_name={name}
device_type=1-0050F204-1
p2p_go_intent=15
p2p_go_ht40=1

# This is a standalone network block for P2P group formation
network={{
    ssid="{name}"
    mode=3
    frequency=2412
    key_mgmt=WPA-PSK
    proto=RSN
    pairwise=CCMP
    psk="{password}"
}}
"""
            with open('/tmp/p2p_supplicant.conf', 'w') as f:
                f.write(config_content)
            
            # รัน wpa_supplicant สำหรับ P2P
            self._run_command(f"sudo wpa_supplicant -B -i {wlan_if} -c /tmp/p2p_supplicant.conf")
            
            # ตั้งค่า IP และ DHCP
            self._run_command(f"sudo ifconfig {wlan_if} 192.168.42.1 netmask 255.255.255.0")
            
            # เริ่ม DHCP server (ถ้าต้องการ)
            if self._check_command_exists('dnsmasq'):
                dnsmasq_conf = f"""
interface={wlan_if}
dhcp-range=192.168.42.2,192.168.42.20,255.255.255.0,24h
"""
                with open('/tmp/dnsmasq.conf', 'w') as f:
                    f.write(dnsmasq_conf)
                
                self._run_command("sudo dnsmasq --conf-file=/tmp/dnsmasq.conf")
            
            logger.info(f"ตั้งค่า WiFi Direct สำเร็จ: {name}")
            return True
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการตั้งค่า WiFi Direct บน Raspberry Pi: {e}")
            return False
    
    def _get_wifi_interface(self) -> Optional[str]:
        """ค้นหาอินเทอร์เฟซ WiFi"""
        try:
            # ใช้ iw เพื่อรายการอินเทอร์เฟซ
            output = self._run_command("iw dev")
            lines = output.split('\n')
            
            for i, line in enumerate(lines):
                if 'Interface' in line:
                    interface = line.split('Interface')[1].strip()
                    return interface
            
            # ทางเลือกอื่น: ดูจากรายการอินเทอร์เฟซเครือข่าย
            for iface in netifaces.interfaces():
                if iface.startswith('wlan'):
                    return iface
            
            return None
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการค้นหาอินเทอร์เฟซ WiFi: {e}")
            return None
    
    def _get_ip_address(self) -> str:
        """รับที่อยู่ IP ของอุปกรณ์"""
        try:
            # ดึงรายการอินเทอร์เฟซเครือข่าย
            interfaces = netifaces.interfaces()
            
            # ค้นหาอินเทอร์เฟซที่ไม่ใช่ loopback และมีที่อยู่ IPv4
            for iface in interfaces:
                if iface == 'lo':
                    continue
                
                addresses = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addresses:
                    for addr_info in addresses[netifaces.AF_INET]:
                        ip = addr_info['addr']
                        # ไม่เอา localhost หรือ link-local addresses
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            return ip
            
            # ถ้าไม่พบ IP ที่เหมาะสม ใช้ localhost
            return '127.0.0.1'
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการรับที่อยู่ IP: {e}")
            return '127.0.0.1'
    
    def _check_service_status(self) -> str:
        """ตรวจสอบสถานะบริการ MANTA"""
        try:
            output = self._run_command("systemctl is-active manta-camera.service")
            output = output.strip()
            
            if output == 'active':
                return 'Running'
            elif output == 'inactive':
                return 'Stopped'
            else:
                return output.capitalize()
        except Exception:
            # อาจไม่ได้ติดตั้งเป็นบริการ
            return 'Unknown'
    
    def _restart_manta_service(self) -> bool:
        """รีสตาร์ทบริการ MANTA"""
        try:
            self._run_command("sudo systemctl restart manta-camera.service")
            return True
        except Exception as e:
            logger.error(f"ไม่สามารถรีสตาร์ทบริการได้: {e}")
            return False
    
    def _can_reboot(self) -> bool:
        """ตรวจสอบว่าสามารถรีบูตระบบได้หรือไม่"""
        try:
            output = self._run_command("sudo -n true")
            return True
        except Exception:
            return False
    
    def _reboot_system(self):
        """รีบูตระบบ"""
        try:
            time.sleep(1)  # รอเล็กน้อยเพื่อให้ส่งการตอบสนอง HTTP ไปก่อน
            self._run_command("sudo reboot")
        except Exception as e:
            logger.error(f"ไม่สามารถรีบูตระบบได้: {e}")
    
    def _get_rpi_model(self) -> str:
        """รับรุ่นของ Raspberry Pi"""
        if not self._is_raspberrypi():
            return "Not Raspberry Pi"
            
        try:
            with open('/proc/device-tree/model', 'r') as f:
                return f.read().strip('\0')
        except Exception:
            return "Unknown Raspberry Pi"
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """รับข้อมูลหน่วยความจำ"""
        try:
            # ใช้ /proc/meminfo
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # ดึงข้อมูลที่ต้องการ
            total = int(self._extract_value(meminfo, 'MemTotal:') / 1024)
            free = int(self._extract_value(meminfo, 'MemFree:') / 1024)
            available = int(self._extract_value(meminfo, 'MemAvailable:') / 1024)
            
            used = total - available
            percent_used = int((used / total) * 100)
            
            return {
                'total': total,
                'used': used,
                'free': free,
                'available': available,
                'percent_used': percent_used
            }
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการรับข้อมูลหน่วยความจำ: {e}")
            return {'error': 'ไม่สามารถรับข้อมูลหน่วยความจำได้'}
    
    def _extract_value(self, text: str, key: str) -> float:
        """สกัดค่าจากข้อความ"""
        for line in text.split('\n'):
            if key in line:
                return float(line.split()[1])
        return 0.0
    
    def _get_cpu_info(self) -> Dict[str, Any]:
        """รับข้อมูล CPU"""
        try:
            # อ่านข้อมูลจาก /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            
            # ดึงข้อมูลที่ต้องการ
            model_name = "Unknown"
            for line in cpuinfo.split('\n'):
                if 'model name' in line:
                    model_name = line.split(':')[1].strip()
                    break
                # สำหรับ ARM (Raspberry Pi)
                elif 'Model' in line:
                    model_name = line.split(':')[1].strip()
            
            # นับจำนวนคอร์
            num_cores = cpuinfo.count('processor')
            
            # อ่านค่า CPU load
            with open('/proc/loadavg', 'r') as f:
                load = f.read().split()
            
            return {
                'model': model_name,
                'cores': num_cores,
                'load_1min': float(load[0]),
                'load_5min': float(load[1]),
                'load_15min': float(load[2])
            }
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการรับข้อมูล CPU: {e}")
            return {'error': 'ไม่สามารถรับข้อมูล CPU ได้'}
    
    def _is_raspberrypi(self) -> bool:
        """ตรวจสอบว่าเครื่องเป็น Raspberry Pi หรือไม่"""
        try:
            return os.path.exists('/proc/device-tree/model') and 'raspberry pi' in open('/proc/device-tree/model', 'r').read().lower()
        except Exception:
            return False
    
    def _check_command_exists(self, command: str) -> bool:
        """ตรวจสอบว่ามีคำสั่งหรือไม่"""
        try:
            self._run_command(f"which {command}")
            return True
        except Exception:
            return False
    
    def _run_command(self, command: str) -> str:
        """รันคำสั่งและรับผลลัพธ์"""
        try:
            process = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"คำสั่งล้มเหลว ({process.returncode}): {stderr.decode('utf-8')}")
            
            return stdout.decode('utf-8')
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการรันคำสั่ง '{command}': {e}")
            raise e
    
    def start(self):
        """เริ่มการทำงานของเซิร์ฟเวอร์การกำหนดค่าระยะไกล"""
        if self.server_thread and self.server_thread.is_alive():
            logger.warning("เซิร์ฟเวอร์กำลังทำงานอยู่แล้ว")
            return
        
        def run_server():
            logger.info(f"เริ่มเซิร์ฟเวอร์การกำหนดค่าระยะไกลที่ http://{self.host}:{self.port}/")
            self.server.serve_forever()
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
    
    def stop(self):
        """หยุดการทำงานของเซิร์ฟเวอร์การกำหนดค่าระยะไกล"""
        if self.zeroconf and self.zeroconf_info:
            self.zeroconf.unregister_service(self.zeroconf_info)
            self.zeroconf.close()
            logger.info("หยุดบริการ Zeroconf")
        
        if self.server:
            self.server.shutdown()
            logger.info("หยุดเซิร์ฟเวอร์การกำหนดค่าระยะไกล")
        
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5.0)


def setup_remote_config(config_path: str, 
                        enable_wifi_direct: bool = False, 
                        port: int = 8080) -> RemoteConfigServer:
    """
    ตั้งค่าและเริ่มเซิร์ฟเวอร์การกำหนดค่าระยะไกล
    
    Args:
        config_path: พาธไปยังไฟล์การกำหนดค่า YAML
        enable_wifi_direct: เปิดใช้งาน WiFi Direct
        port: พอร์ตที่จะให้บริการ
    
    Returns:
        RemoteConfigServer: อ็อบเจกต์เซิร์ฟเวอร์
    """
    # ตรวจสอบว่ามี Flask หรือไม่
    if not FLASK_AVAILABLE:
        logger.error("ไม่สามารถเริ่มเซิร์ฟเวอร์การกำหนดค่าระยะไกลได้: ไม่พบ Flask")
        logger.error("ติดตั้ง Flask ด้วยคำสั่ง: pip install flask flask-cors")
        return None
    
    # ตรวจสอบว่ามีไฟล์การกำหนดค่าหรือไม่
    if not os.path.exists(config_path):
        logger.error(f"ไม่พบไฟล์การกำหนดค่า: {config_path}")
        return None
    
    # สร้างและเริ่มเซิร์ฟเวอร์
    server = RemoteConfigServer(config_path, 
                               enable_wifi_direct=enable_wifi_direct,
                               port=port)
    server.start()
    
    return server


def main():
    """ฟังก์ชันหลักเมื่อรันโดยตรง"""
    import argparse
    
    parser = argparse.ArgumentParser(description='เซิร์ฟเวอร์การกำหนดค่าระยะไกลสำหรับ MANTA Camera')
    parser.add_argument('--config', type=str, default='/etc/manta-camera/config.yaml',
                       help='พาธไปยังไฟล์การกำหนดค่า YAML (ค่าเริ่มต้น: /etc/manta-camera/config.yaml)')
    parser.add_argument('--port', type=int, default=8080,
                       help='พอร์ตที่จะให้บริการ (ค่าเริ่มต้น: 8080)')
    parser.add_argument('--wifi-direct', action='store_true',
                       help='เปิดใช้งาน WiFi Direct สำหรับการเชื่อมต่อโดยตรง')
    
    args = parser.parse_args()
    
    # ตั้งค่าและเริ่มเซิร์ฟเวอร์
    server = setup_remote_config(args.config, args.wifi_direct, args.port)
    
    if server:
        try:
            # แสดงข้อความแนะนำ
            ip = server._get_ip_address()
            print(f"\nเซิร์ฟเวอร์การกำหนดค่าระยะไกลเริ่มทำงานแล้ว!")
            print(f"สามารถเข้าถึงได้ที่: http://{ip}:{args.port}/")
            print("\nกด Ctrl+C เพื่อหยุดเซิร์ฟเวอร์...\n")
            
            # รันไปเรื่อยๆ จนกว่าจะถูกขัดจังหวะ
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nหยุดเซิร์ฟเวอร์การกำหนดค่าระยะไกล...")
            server.stop()


if __name__ == "__main__":
    main()
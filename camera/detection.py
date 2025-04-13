#!/usr/bin/env python3
"""
โมดูลตรวจจับบุคคลสำหรับระบบ MANTA
(People detection module for MANTA system)

รองรับการตรวจจับบุคคลด้วยโมเดล YOLO บน Raspberry Pi 5
"""

import cv2
import numpy as np
import os
from typing import List, Tuple, Union, Optional

class PersonDetector:
    """
    การตรวจจับบุคคลโดยใช้โมเดล YOLO
    """
    
    def __init__(self, 
                 model_path: str, 
                 confidence_threshold: float = 0.5, 
                 nms_threshold: float = 0.45,
                 device: str = "CPU",
                 classes: List[str] = None):
        """
        เริ่มต้นตัวตรวจจับบุคคล
        
        Args:
            model_path: พาธไปยังโมเดล YOLO ONNX
            confidence_threshold: ค่าความเชื่อมั่นขั้นต่ำสำหรับการตรวจจับ
            nms_threshold: ค่าขั้นต่ำสำหรับการกดทับที่ไม่ใช่ค่าสูงสุด
            device: อุปกรณ์ที่จะใช้ในการทำนาย ("CPU", "CUDA", เป็นต้น)
            classes: รายการคลาสที่จะตรวจจับ (ถ้าเป็น None จะตรวจจับทุกคลาส)
        """
        # Store parameters
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.classes = classes if classes else ["person"]
        
        # Load model
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        
        try:
            self.model = cv2.dnn.readNetFromONNX(model_path)
            
            # Set inference backend
            if device.upper() == "CUDA" and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self.model.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.model.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            else:
                self.model.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.model.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        except Exception as e:
            raise RuntimeError(f"Error loading model: {e}")
            
        # Get list of output layer names
        self.output_layers = self.model.getUnconnectedOutLayersNames()
        
        # Load class names
        self.class_names = ["person", "bicycle", "car"] # Placeholder - will be replaced with actual model classes
        
        # Try to load class names from common COCO dataset
        coco_names_path = os.path.join(os.path.dirname(os.path.dirname(model_path)), 
                                      "coco.names")
        if os.path.exists(coco_names_path):
            with open(coco_names_path, 'r') as f:
                self.class_names = [line.strip() for line in f.readlines()]
        
        # Find indices of classes we want to detect
        self.class_indices = []
        for cls in self.classes:
            if cls in self.class_names:
                self.class_indices.append(self.class_names.index(cls))
            else:
                # If class name not in list but is an integer index
                try:
                    index = int(cls)
                    if 0 <= index < len(self.class_names):
                        self.class_indices.append(index)
                except ValueError:
                    pass
        
        # If no valid class indices found but "person" was requested, default to COCO person index (0)
        if not self.class_indices and "person" in self.classes:
            self.class_indices = [0]  # Person is typically class 0 in COCO
    
    def detect(self, frame: np.ndarray) -> List[Tuple[float, float, float, float, float, int]]:
        """
        ตรวจจับบุคคลในเฟรมที่กำหนด
        
        Args:
            frame: ภาพนำเข้า (รูปแบบ BGR)
            
        Returns:
            รายการการตรวจจับ: [x1, y1, x2, y2, confidence, class_id]
        """
        if frame is None or frame.size == 0:
            return []
        
        # Get image dimensions
        height, width = frame.shape[:2]
        
        # Preprocess image
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640), swapRB=True, crop=False)
        
        # Forward pass
        self.model.setInput(blob)
        outputs = self.model.forward(self.output_layers)
        
        # Process outputs
        boxes = []
        confidences = []
        class_ids = []
        
        # For YOLOv8 ONNX output format (detection model)
        if len(outputs) == 1 and outputs[0].shape[1] > 5:
            # YOLOv8 detection output: [x, y, w, h, confidence, class probs...]
            output = outputs[0]
            
            for detection in output:
                scores = detection[4:]
                class_id = np.argmax(scores)
                confidence = scores[class_id] * detection[4]  # obj_conf * cls_conf
                
                # Filter by confidence and class
                if confidence > self.confidence_threshold and \
                        (len(self.class_indices) == 0 or class_id in self.class_indices):
                    # YOLO format: centers (x, y, w, h) to corners (x1, y1, x2, y2)
                    x, y, w, h = detection[0:4]
                    
                    # Convert to original image coordinates
                    x1 = int((x - w/2) * width)
                    y1 = int((y - h/2) * height)
                    x2 = int((x + w/2) * width)
                    y2 = int((y + h/2) * height)
                    
                    boxes.append([x1, y1, x2, y2])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Apply non-maximum suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.nms_threshold)
        
        # Prepare results
        detections = []
        for i in indices:
            # In OpenCV 4.5.4+, indices is a tensor rather than a list
            if isinstance(i, np.ndarray):
                i = i.item()
                
            box = boxes[i]
            confidence = confidences[i]
            class_id = class_ids[i]
            
            detections.append((box[0], box[1], box[2], box[3], confidence, class_id))
        
        return detections

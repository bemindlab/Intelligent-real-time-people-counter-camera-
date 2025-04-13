"""
โมดูลจดจำบุคคลสำหรับระบบ MANTA
(Person re-identification module for MANTA)

ใช้เวกเตอร์ลักษณะเฉพาะเพื่อระบุว่าบุคคลเคยถูกพบมาก่อนหรือไม่
เหมาะสำหรับการติดตามบุคคลที่เคลื่อนที่ในพื้นที่ที่ตรวจจับ
"""

import os
import time
import hashlib
import numpy as np
import cv2
from scipy.spatial.distance import cosine

# Try to import onnxruntime with CUDA support
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("Warning: onnxruntime not available, using fallback feature extraction")


class PersonReIdentifier:
    """
    คลาสสำหรับการระบุตัวตนบุคคลซ้ำโดยใช้เวกเตอร์ลักษณะเฉพาะ
    """
    
    def __init__(self, feature_size=128, similarity_threshold=0.6, 
                 retention_period=3600, max_stored_vectors=1000, 
                 model_path=None):
        """
        เริ่มต้นตัวระบุตัวตนบุคคลซ้ำ
        
        Args:
            feature_size (int): ขนาดของเวกเตอร์ลักษณะเฉพาะ
            similarity_threshold (float): ค่าขั้นต่ำสำหรับความคล้ายคลึงแบบโคไซน์
            retention_period (int): ระยะเวลาที่จะจดจำบุคคล (เป็นวินาที)
            max_stored_vectors (int): จำนวนเวกเตอร์ลักษณะเฉพาะสูงสุดที่จะเก็บ
            model_path (str): พาธไปยังโมเดลสกัดลักษณะเฉพาะ (ถ้ามี)
        """
        self.feature_size = feature_size
        self.similarity_threshold = similarity_threshold
        self.retention_period = retention_period
        self.max_stored_vectors = max_stored_vectors
        
        # Initialize storage for feature vectors with timestamp
        self.known_vectors = []  # List of (vector, timestamp, hash_id)
        
        # Load feature extractor model if provided
        self.model = None
        if model_path and ONNX_AVAILABLE:
            self._load_model(model_path)
    
    def _load_model(self, model_path):
        """
        โหลดโมเดลสกัดลักษณะเฉพาะ
        
        Args:
            model_path (str): พาธไปยังโมเดล ONNX
        """
        try:
            # Check if model file exists
            if not os.path.exists(model_path):
                print(f"Warning: Model file {model_path} not found")
                return
                
            # Load model with ONNX Runtime
            self.model = ort.InferenceSession(model_path)
            
            # Get model metadata
            self.input_name = self.model.get_inputs()[0].name
            self.output_name = self.model.get_outputs()[0].name
            
            # Get input shape
            input_shape = self.model.get_inputs()[0].shape
            if len(input_shape) == 4:  # NCHW format
                self.input_width = input_shape[3]
                self.input_height = input_shape[2]
            else:
                raise ValueError("Unexpected input shape")
                
            print(f"Re-ID model loaded: {model_path}")
            
        except Exception as e:
            print(f"Error loading re-identification model: {e}")
            self.model = None
    
    def process(self, person_img):
        """
        ประมวลผลภาพบุคคลและตรวจสอบว่าเป็นบุคคลใหม่หรือไม่
        
        Args:
            person_img (numpy.ndarray): ภาพของบุคคลที่ตรวจจับได้
            
        Returns:
            tuple: (is_new_person, person_hash)
        """
        # Clean up old vectors
        self._clean_old_vectors()
        
        # Extract feature vector
        vector = self._extract_features(person_img)
        
        # Generate hash ID for the person
        person_hash = self._generate_hash(vector)
        
        # Check if this is a new person
        is_new_person = True
        
        for known_vector, _, _ in self.known_vectors:
            similarity = 1 - cosine(vector, known_vector)
            if similarity >= self.similarity_threshold:
                is_new_person = False
                break
        
        # If it's a new person or we have no known vectors, add to the list
        if is_new_person or not self.known_vectors:
            self._add_vector(vector)
        
        return is_new_person, person_hash
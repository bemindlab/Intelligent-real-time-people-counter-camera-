#!/usr/bin/env python3
"""
ฟังก์ชันอรรถประโยชน์สำหรับการดำเนินการกับเวกเตอร์
(Utility functions for vector operations)

ใช้ในระบบการจดจำบุคคลและการคำนวณความคล้ายคลึงระหว่างลักษณะเฉพาะ
พัฒนาสำหรับโปรเจค MANTA บน Raspberry Pi 5
"""

import numpy as np
from typing import List, Tuple, Union, Optional

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity value (0-1)
    """
    # Check for zero vectors
    if np.all(a == 0) or np.all(b == 0):
        return 0.0
        
    # Calculate dot product and magnitudes
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    # Avoid division by zero
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    # Calculate similarity
    similarity = dot_product / (norm_a * norm_b)
    
    # Ensure value is in range [0, 1]
    return max(0.0, min(1.0, similarity))

def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """
    Calculate Euclidean distance between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Euclidean distance value
    """
    return np.linalg.norm(a - b)

def vector_to_bytes(vector: np.ndarray) -> bytes:
    """
    Convert a vector to bytes for storage or transmission.
    
    Args:
        vector: NumPy vector to convert
        
    Returns:
        Byte representation of the vector
    """
    return vector.tobytes()

def bytes_to_vector(data: bytes, dtype=np.float32, shape=None) -> np.ndarray:
    """
    Convert bytes back to a vector.
    
    Args:
        data: Byte representation of the vector
        dtype: NumPy data type of the vector
        shape: Shape of the resulting vector (inferred if None)
        
    Returns:
        NumPy vector
    """
    vector = np.frombuffer(data, dtype=dtype)
    if shape is not None:
        vector = vector.reshape(shape)
    return vector

def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """
    Normalize a vector to unit length.
    
    Args:
        vector: Input vector
        
    Returns:
        Normalized vector
    """
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm

def average_vectors(vectors: List[np.ndarray]) -> Optional[np.ndarray]:
    """
    Compute the average of multiple vectors.
    
    Args:
        vectors: List of vectors to average
        
    Returns:
        Average vector, or None if the list is empty
    """
    if not vectors:
        return None
        
    # Ensure all vectors have the same shape
    shapes = [v.shape for v in vectors]
    if len(set(shapes)) > 1:
        raise ValueError("All vectors must have the same shape")
    
    # Compute average
    avg = np.mean(vectors, axis=0)
    return avg

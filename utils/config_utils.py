#!/usr/bin/env python3
"""
อรรถประโยชน์สำหรับการจัดการการกำหนดค่าที่ปลอดภัยในระบบ MANTA
(Utilities for secure configuration management in MANTA system)

รองรับการเข้ารหัสข้อมูลสำคัญเช่นรหัสผ่านและข้อมูลประจำตัว
พัฒนาสำหรับการใช้งานบน Raspberry Pi 5 Model B
"""

import os
import yaml
import json
import logging
import base64
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Secure configuration manager for MANTA system.
    Provides encryption for sensitive information like credentials.
    """
    
    def __init__(self, config_path: str, encryption_key: Optional[str] = None):
        """
        Initialize the config manager.
        
        Args:
            config_path: Path to the configuration file
            encryption_key: Optional encryption key for sensitive data
        """
        self.config_path = config_path
        self.config_data = {}
        self.encrypted_fields = {}
        
        # Set up encryption
        self.encryption_key = encryption_key
        if encryption_key:
            self._setup_encryption(encryption_key)
        else:
            self.cipher = None
        
        # Load configuration
        self.load_config()
    
    def _setup_encryption(self, key: str) -> None:
        """Set up encryption with the given key."""
        try:
            # Derive a proper encryption key using PBKDF2
            salt = b'manta_secure_config'  # Fixed salt for deterministic key derivation
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
            self.cipher = Fernet(derived_key)
        except Exception as e:
            logger.error(f"Error setting up encryption: {e}")
            self.cipher = None
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Loaded configuration dictionary
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config_data = yaml.safe_load(f) or {}
                    
                # Decrypt any encrypted fields
                if self.cipher:
                    self._decrypt_sensitive_fields()
            else:
                logger.warning(f"Config file {self.config_path} not found. Using empty config.")
                self.config_data = {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config_data = {}
        
        return self.config_data
    
    def save_config(self) -> bool:
        """
        Save configuration to YAML file.
        
        Returns:
            True if saving was successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Encrypt sensitive fields if encryption is enabled
            config_to_save = self.config_data.copy()
            if self.cipher:
                for section, fields in self.encrypted_fields.items():
                    for field in fields:
                        path = section.split('.')
                        self._encrypt_field(config_to_save, path, field)
            
            # Save to file
            with open(self.config_path, 'w') as f:
                yaml.dump(config_to_save, f, default_flow_style=False)
            
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Key in dot notation (e.g., 'firebase.credentials')
            default: Default value if key not found
            
        Returns:
            Configuration value or default if not found
        """
        try:
            parts = key.split('.')
            value = self.config_data
            for part in parts:
                value = value.get(part, {})
            
            # If we got an empty dict but the path should lead to a value,
            # return the default instead
            if value == {} and len(parts) > 0:
                return default
                
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any, sensitive: bool = False) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Key in dot notation (e.g., 'firebase.credentials')
            value: Value to set
            sensitive: Whether this field contains sensitive information
        """
        parts = key.split('.')
        
        # Navigate to the correct part of the config
        current = self.config_data
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value
        current[parts[-1]] = value
        
        # Mark as sensitive if needed
        if sensitive and self.cipher:
            section = '.'.join(parts[:-1]) if len(parts) > 1 else ''
            field = parts[-1]
            
            if section not in self.encrypted_fields:
                self.encrypted_fields[section] = []
            
            if field not in self.encrypted_fields[section]:
                self.encrypted_fields[section].append(field)
    
    def _encrypt_field(self, config: Dict[str, Any], path: list, field: str) -> None:
        """
        Encrypt a field in the configuration.
        
        Args:
            config: Configuration dictionary to modify
            path: Path to the section containing the field
            field: Field name to encrypt
        """
        if not self.cipher:
            return
        
        try:
            # Navigate to the correct section
            section = config
            for part in path:
                if part and part in section:
                    section = section[part]
                else:
                    # Path doesn't exist, nothing to encrypt
                    return
            
            # Encrypt the field if it exists and is a string
            if field in section and isinstance(section[field], str):
                encrypted = self.cipher.encrypt(section[field].encode()).decode()
                section[field] = f"ENC:{encrypted}"
        except Exception as e:
            logger.error(f"Error encrypting field {'.'.join(path)}.{field}: {e}")
    
    def _decrypt_sensitive_fields(self) -> None:
        """Decrypt all sensitive fields in the loaded configuration."""
        if not self.cipher:
            return
        
        # Build list of encrypted fields from the config
        for section in self.config_data:
            self._find_encrypted_fields(self.config_data[section], section)
        
        # Decrypt fields
        for section, fields in self.encrypted_fields.items():
            for field in fields:
                path = section.split('.') if section else []
                self._decrypt_field(self.config_data, path, field)
    
    def _find_encrypted_fields(self, config: Dict[str, Any], path: str = '') -> None:
        """
        Find encrypted fields in the configuration.
        
        Args:
            config: Configuration dictionary to search
            path: Current path in dot notation
        """
        if isinstance(config, dict):
            for key, value in config.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, str) and value.startswith('ENC:'):
                    # This is an encrypted field
                    section = path
                    if section not in self.encrypted_fields:
                        self.encrypted_fields[section] = []
                    if key not in self.encrypted_fields[section]:
                        self.encrypted_fields[section].append(key)
                elif isinstance(value, dict):
                    # Recurse into nested dictionaries
                    self._find_encrypted_fields(value, current_path)
    
    def _decrypt_field(self, config: Dict[str, Any], path: list, field: str) -> None:
        """
        Decrypt a field in the configuration.
        
        Args:
            config: Configuration dictionary to modify
            path: Path to the section containing the field
            field: Field name to decrypt
        """
        if not self.cipher:
            return
        
        try:
            # Navigate to the correct section
            section = config
            for part in path:
                if part and part in section:
                    section = section[part]
                else:
                    # Path doesn't exist, nothing to decrypt
                    return
            
            # Decrypt the field if it exists and is encrypted
            if field in section and isinstance(section[field], str) and section[field].startswith('ENC:'):
                encrypted = section[field][4:]  # Remove 'ENC:' prefix
                decrypted = self.cipher.decrypt(encrypted.encode()).decode()
                section[field] = decrypted
        except Exception as e:
            logger.error(f"Error decrypting field {'.'.join(path)}.{field}: {e}")

def load_firebase_config(config_path: str, firebase_config_path: str, encryption_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Load Firebase configuration with potential encryption.
    
    Args:
        config_path: Path to the main MANTA configuration file
        firebase_config_path: Path to Firebase configuration file
        encryption_key: Optional encryption key
        
    Returns:
        Firebase configuration dictionary
    """
    # First, check if Firebase config path is specified
    if not firebase_config_path:
        # Try to get it from the main config
        config_manager = ConfigManager(config_path, encryption_key)
        firebase_config = config_manager.get('firebase', {})
        firebase_config_path = firebase_config.get('config_path', '')
    
    # If we still don't have a path, return empty config
    if not firebase_config_path or not os.path.exists(firebase_config_path):
        logger.warning(f"Firebase config not found at {firebase_config_path}")
        return {}
    
    # Load Firebase config
    try:
        with open(firebase_config_path, 'r') as f:
            firebase_config = json.load(f)
        
        # Decrypt if needed (e.g., private key might be encrypted)
        if encryption_key and any(key.startswith('ENC:') for key in firebase_config.values() if isinstance(key, str)):
            # Set up encryption
            salt = b'manta_secure_config'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
            cipher = Fernet(derived_key)
            
            # Decrypt encrypted fields
            for key, value in firebase_config.items():
                if isinstance(value, str) and value.startswith('ENC:'):
                    encrypted = value[4:]  # Remove 'ENC:' prefix
                    firebase_config[key] = cipher.decrypt(encrypted.encode()).decode()
        
        return firebase_config
    
    except Exception as e:
        logger.error(f"Error loading Firebase config: {e}")
        return {}

def encrypt_firebase_config(input_path: str, output_path: str, encryption_key: str) -> bool:
    """
    Encrypt sensitive information in Firebase configuration.
    
    Args:
        input_path: Path to the input Firebase configuration file
        output_path: Path to save the encrypted configuration
        encryption_key: Encryption key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load the input configuration
        with open(input_path, 'r') as f:
            config = json.load(f)
        
        # Set up encryption
        salt = b'manta_secure_config'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        cipher = Fernet(derived_key)
        
        # Fields to encrypt (sensitive information)
        sensitive_fields = [
            'private_key', 'private_key_id', 'client_email', 'client_id', 'auth_uri',
            'token_uri', 'auth_provider_x509_cert_url', 'client_x509_cert_url', 'apiKey'
        ]
        
        # Encrypt sensitive fields
        for field in sensitive_fields:
            if field in config and isinstance(config[field], str):
                encrypted = cipher.encrypt(config[field].encode()).decode()
                config[field] = f"ENC:{encrypted}"
        
        # Save the encrypted configuration
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    
    except Exception as e:
        logger.error(f"Error encrypting Firebase config: {e}")
        return False

def generate_encryption_key() -> str:
    """
    Generate a new encryption key.
    
    Returns:
        Base64-encoded encryption key
    """
    try:
        key = Fernet.generate_key()
        return key.decode()
    except Exception as e:
        logger.error(f"Error generating encryption key: {e}")
        return ""
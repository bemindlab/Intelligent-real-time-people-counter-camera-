#!/usr/bin/env python3
"""
Firebase utilities for MANTA system.
"""

import json
import os
import time
from typing import Dict, Any, Optional, List

class FirebaseClient:
    """
    Firebase client wrapper for MANTA system.
    """
    
    def __init__(self, config_path: str, database_url: Optional[str] = None):
        """
        Initialize the Firebase client.
        
        Args:
            config_path: Path to Firebase config file
            database_url: Optional database URL override
        """
        self.config_path = config_path
        self.database_url = database_url
        self.firebase_app = None
        self.db_ref = None
        
        # Initialize Firebase
        self._init_firebase()
    
    def _init_firebase(self) -> bool:
        """
        Initialize Firebase connection.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Check if firebase_admin module is available
            import firebase_admin
            from firebase_admin import credentials, db
            
            # Check if configuration file exists
            if not os.path.exists(self.config_path):
                print(f"Firebase config not found at {self.config_path}")
                return False
            
            # Load Firebase configuration
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Use provided database URL or get from config
            if not self.database_url and 'databaseURL' in config:
                self.database_url = config['databaseURL']
            
            if not self.database_url:
                print("Database URL not provided and not found in config")
                return False
            
            # Initialize Firebase app if not already initialized
            if not firebase_admin._apps:
                # If config has type=service_account, it's a service account key
                if config.get('type') == 'service_account':
                    cred = credentials.Certificate(self.config_path)
                    self.firebase_app = firebase_admin.initialize_app(cred, {
                        'databaseURL': self.database_url
                    })
                # Otherwise it's a web config
                else:
                    # For web config, we need to create a credential from the config values
                    self.firebase_app = firebase_admin.initialize_app({
                        'databaseURL': self.database_url
                    })
            else:
                # Get the default app
                self.firebase_app = firebase_admin.get_app()
            
            # Get database reference
            self.db_ref = db.reference()
            return True
            
        except ImportError:
            print("firebase_admin module not found. Please install with: pip install firebase-admin")
            return False
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            return False
    
    def get_data(self, path: str) -> Any:
        """
        Get data from Firebase at the specified path.
        
        Args:
            path: Path to the data
            
        Returns:
            Data at the path, or None if not found or error
        """
        if not self.db_ref:
            return None
        
        try:
            from firebase_admin import db
            return db.reference(path).get()
        except Exception as e:
            print(f"Error getting data from Firebase: {e}")
            return None
    
    def set_data(self, path: str, data: Any) -> bool:
        """
        Set data in Firebase at the specified path.
        
        Args:
            path: Path to set the data
            data: Data to set
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_ref:
            return False
        
        try:
            from firebase_admin import db
            db.reference(path).set(data)
            return True
        except Exception as e:
            print(f"Error setting data in Firebase: {e}")
            return False
    
    def push_data(self, path: str, data: Any) -> Optional[str]:
        """
        Push data to Firebase at the specified path.
        
        Args:
            path: Path to push the data
            data: Data to push
            
        Returns:
            Key of the pushed data if successful, None otherwise
        """
        if not self.db_ref:
            return None
        
        try:
            from firebase_admin import db
            result = db.reference(path).push(data)
            return result.key
        except Exception as e:
            print(f"Error pushing data to Firebase: {e}")
            return None
    
    def update_data(self, path: str, data: Dict[str, Any]) -> bool:
        """
        Update data in Firebase at the specified path.
        
        Args:
            path: Path to update the data
            data: Dictionary of updates
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_ref:
            return False
        
        try:
            from firebase_admin import db
            db.reference(path).update(data)
            return True
        except Exception as e:
            print(f"Error updating data in Firebase: {e}")
            return False
    
    def delete_data(self, path: str) -> bool:
        """
        Delete data from Firebase at the specified path.
        
        Args:
            path: Path to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_ref:
            return False
        
        try:
            from firebase_admin import db
            db.reference(path).delete()
            return True
        except Exception as e:
            print(f"Error deleting data from Firebase: {e}")
            return False
    
    def close(self) -> None:
        """
        Close the Firebase connection.
        """
        if self.firebase_app:
            try:
                import firebase_admin
                firebase_admin.delete_app(self.firebase_app)
                self.firebase_app = None
                self.db_ref = None
            except Exception as e:
                print(f"Error closing Firebase connection: {e}")


# Helper functions

def init_firebase(config_path: str, database_url: Optional[str] = None) -> Optional[FirebaseClient]:
    """
    Initialize a Firebase client.
    
    Args:
        config_path: Path to Firebase config file
        database_url: Optional database URL override
        
    Returns:
        FirebaseClient instance or None if initialization failed
    """
    client = FirebaseClient(config_path, database_url)
    if client.db_ref:
        return client
    return None


def get_camera_ref(client: FirebaseClient, camera_id: str, path_prefix: str = "cameras") -> str:
    """
    Get the reference path for a camera.
    
    Args:
        client: FirebaseClient instance
        camera_id: ID of the camera
        path_prefix: Prefix path for cameras
        
    Returns:
        Full path to the camera reference
    """
    return f"{path_prefix}/{camera_id}"


def log_person_detection(client: FirebaseClient, camera_id: str, log_entry: Dict[str, Any], 
                         path_prefix: str = "cameras") -> bool:
    """
    Log a person detection event to Firebase.
    
    Args:
        client: FirebaseClient instance
        camera_id: ID of the camera
        log_entry: Log entry data
        path_prefix: Prefix path for cameras
        
    Returns:
        True if successful, False otherwise
    """
    camera_path = get_camera_ref(client, camera_id, path_prefix)
    log_path = f"{camera_path}/logs"
    
    # Add timestamp if not present
    if "timestamp" not in log_entry:
        log_entry["timestamp"] = time.time() * 1000  # milliseconds
        
    # Add camera_id if not present
    if "camera_id" not in log_entry:
        log_entry["camera_id"] = camera_id
    
    # Push the log entry
    key = client.push_data(log_path, log_entry)
    return key is not None
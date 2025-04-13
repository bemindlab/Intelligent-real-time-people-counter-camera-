#!/usr/bin/env python3
"""
Firebase Storage utilities for MANTA system.
Utility functions for uploading files to Firebase Storage.
"""

import os
import time
import json
import uuid
import threading
import queue
from typing import Dict, Any, Optional, List, Tuple

class FirebaseStorageUploader:
    """
    Firebase Storage uploader for MANTA system.
    Handles uploading files to Firebase Storage with retry capability.
    """
    
    def __init__(self, 
                 config_path: str, 
                 storage_bucket: str,
                 retry_interval: int = 60,
                 thread_count: int = 1):
        """
        Initialize the Firebase Storage uploader.
        
        Args:
            config_path: Path to Firebase config file
            storage_bucket: Firebase Storage bucket name
            retry_interval: Seconds between retries when offline
            thread_count: Number of upload threads
        """
        self.config_path = config_path
        self.storage_bucket = storage_bucket
        self.retry_interval = retry_interval
        self.thread_count = thread_count
        
        # Queue for files to upload
        self.upload_queue = queue.Queue()
        
        # Flag to indicate if uploader is running
        self.running = False
        
        # Flag to indicate if offline mode
        self.offline_mode = False
        
        # Initialize Firebase
        self._init_firebase()
        
        # Start upload threads
        self.upload_threads = []
        self.running = True
        for _ in range(self.thread_count):
            thread = threading.Thread(target=self._upload_worker, daemon=True)
            thread.start()
            self.upload_threads.append(thread)
    
    def _init_firebase(self) -> None:
        """
        Initialize Firebase Storage connection.
        """
        try:
            # Check if firebase_admin module is available
            import firebase_admin
            from firebase_admin import credentials, storage
            
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
                        
                        # Initialize app if not already initialized
                        if not firebase_admin._apps:
                            firebase_admin.initialize_app(cred, {
                                'storageBucket': self.storage_bucket
                            })
                        # Get existing app
                        else:
                            for app in firebase_admin._apps.values():
                                if app.project_id == firebase_config.get('project_id'):
                                    break
                            else:
                                name = f'storage-{uuid.uuid4().hex}'
                                firebase_admin.initialize_app(cred, {
                                    'storageBucket': self.storage_bucket
                                }, name=name)
                    else:
                        # For web config, we need storage bucket too
                        if not firebase_admin._apps:
                            firebase_admin.initialize_app({
                                'storageBucket': self.storage_bucket
                            })
                else:
                    # Fall back to standard loading
                    raise ImportError("Failed to load encrypted Firebase config")
            except ImportError:
                # Standard loading without encryption
                # Load Firebase credentials from file
                cred = credentials.Certificate(self.config_path)
                
                # Initialize app if not already initialized
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': self.storage_bucket
                    })
            
            # Get storage bucket
            self.bucket = storage.bucket()
            
            # We're online
            self.offline_mode = False
            print(f"Connected to Firebase Storage: {self.storage_bucket}")
            
        except ImportError:
            print("Warning: firebase_admin module not found. Running in offline mode.")
            self.offline_mode = True
        except Exception as e:
            print(f"Error connecting to Firebase Storage: {e}. Running in offline mode.")
            self.offline_mode = True
    
    def upload_file(self, local_path: str, remote_path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Queue a file for upload to Firebase Storage.
        
        Args:
            local_path: Local path to the file
            remote_path: Remote path in Firebase Storage
            metadata: Optional metadata for the file
        """
        if self.running:
            self.upload_queue.put((local_path, remote_path, metadata))
    
    def _do_upload(self, local_path: str, remote_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Upload a file to Firebase Storage.
        
        Args:
            local_path: Local path to the file
            remote_path: Remote path in Firebase Storage
            metadata: Optional metadata for the file
            
        Returns:
            True if successful, False otherwise
        """
        if self.offline_mode or not os.path.exists(local_path):
            return False
        
        try:
            # Import Firebase modules
            from firebase_admin import storage
            
            # Upload file
            blob = self.bucket.blob(remote_path)
            
            # Set metadata if provided
            if metadata:
                blob.metadata = metadata
            
            # Upload file
            blob.upload_from_filename(local_path)
            
            # Get public URL
            blob.make_public()
            url = blob.public_url
            
            print(f"Uploaded file to Firebase Storage: {remote_path} ({url})")
            return True
        except Exception as e:
            print(f"Error uploading to Firebase Storage: {e}")
            # Switch to offline mode on error
            self.offline_mode = True
            return False
    
    def _upload_worker(self) -> None:
        """
        Upload worker thread function.
        Continuously processes the upload queue.
        """
        while self.running:
            try:
                # Get next file to upload
                try:
                    local_path, remote_path, metadata = self.upload_queue.get(block=True, timeout=1.0)
                except queue.Empty:
                    # Check if we need to reconnect
                    if self.offline_mode:
                        time.sleep(self.retry_interval)
                        self._init_firebase()
                    continue
                
                # Upload file
                success = self._do_upload(local_path, remote_path, metadata)
                if success:
                    self.upload_queue.task_done()
                else:
                    # Put file back in queue if upload failed
                    self.upload_queue.put((local_path, remote_path, metadata))
                    # Wait before retry
                    time.sleep(self.retry_interval)
                    # Try to reconnect
                    if self.offline_mode:
                        self._init_firebase()
                
            except Exception as e:
                print(f"Error in upload worker: {e}")
                time.sleep(self.retry_interval)
    
    def flush(self) -> None:
        """
        Force upload of all pending files.
        """
        if not self.running or self.offline_mode:
            return
        
        # Wait for queue to empty
        self.upload_queue.join()
    
    def stop(self) -> None:
        """
        Stop the uploader and wait for upload threads to finish.
        """
        self.running = False
        for thread in self.upload_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)


def init_storage_uploader(config_path: str, storage_bucket: str) -> Optional[FirebaseStorageUploader]:
    """
    Initialize a Firebase Storage uploader.
    
    Args:
        config_path: Path to Firebase config file
        storage_bucket: Firebase Storage bucket name
        
    Returns:
        FirebaseStorageUploader instance or None if initialization failed
    """
    try:
        uploader = FirebaseStorageUploader(config_path, storage_bucket)
        return uploader
    except Exception as e:
        print(f"Failed to initialize Firebase Storage uploader: {e}")
        return None


def upload_face_image(uploader: FirebaseStorageUploader, 
                     image_path: str, 
                     person_id: str,
                     metadata: Dict[str, Any]) -> Optional[str]:
    """
    Upload a face image to Firebase Storage.
    
    Args:
        uploader: FirebaseStorageUploader instance
        image_path: Path to image file
        person_id: Person ID for folder structure
        metadata: Metadata for the face image
        
    Returns:
        Remote path if queued for upload, None otherwise
    """
    if uploader is None or not os.path.exists(image_path):
        return None
    
    # Generate remote path
    filename = os.path.basename(image_path)
    remote_path = f"faces/{person_id}/{filename}"
    
    # Queue for upload
    uploader.upload_file(image_path, remote_path, metadata)
    
    return remote_path
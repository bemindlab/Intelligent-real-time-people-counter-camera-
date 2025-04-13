#!/usr/bin/env python3
"""
Test script for Firebase integration in MANTA system.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Firebase utilities
from firebase.firebase_utils import FirebaseClient, log_person_detection

def test_firebase_connection(config_path, database_url=None):
    """Test basic Firebase connection."""
    print(f"Testing Firebase connection with config: {config_path}")
    
    # Initialize client
    client = FirebaseClient(config_path, database_url)
    
    if client.db_ref:
        print("✅ Firebase connection successful!")
        print(f"   Database URL: {client.database_url}")
        return client
    else:
        print("❌ Firebase connection failed.")
        return None

def test_firebase_write(client, camera_id='test_camera'):
    """Test writing data to Firebase."""
    if not client or not client.db_ref:
        print("❌ Firebase client not initialized. Skipping write test.")
        return False
    
    print(f"Testing Firebase write with camera_id: {camera_id}")
    
    # Create test data
    test_data = {
        "test_id": f"test_{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "message": "This is a test message from MANTA"
    }
    
    # Set data
    path = f"cameras/{camera_id}/test"
    result = client.set_data(path, test_data)
    
    if result:
        print(f"✅ Successfully wrote test data to {path}")
        return True
    else:
        print(f"❌ Failed to write test data to {path}")
        return False

def test_firebase_read(client, camera_id='test_camera'):
    """Test reading data from Firebase."""
    if not client or not client.db_ref:
        print("❌ Firebase client not initialized. Skipping read test.")
        return False
    
    print(f"Testing Firebase read with camera_id: {camera_id}")
    
    # Read data
    path = f"cameras/{camera_id}/test"
    data = client.get_data(path)
    
    if data:
        print(f"✅ Successfully read data from {path}")
        print(f"   Data: {json.dumps(data, indent=2)}")
        return True
    else:
        print(f"❌ Failed to read data from {path} or no data found")
        return False

def test_log_person(client, camera_id='test_camera'):
    """Test the person detection logging functionality."""
    if not client or not client.db_ref:
        print("❌ Firebase client not initialized. Skipping person logging test.")
        return False
    
    print(f"Testing person detection logging with camera_id: {camera_id}")
    
    # Create test person detection log
    log_entry = {
        "person_hash": f"person_{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "detection_type": "test_detection",
        "confidence": 0.95
    }
    
    # Log the person detection
    result = log_person_detection(client, camera_id, log_entry)
    
    if result:
        print(f"✅ Successfully logged person detection")
        return True
    else:
        print(f"❌ Failed to log person detection")
        return False

def main():
    """Main function to run Firebase tests."""
    parser = argparse.ArgumentParser(description='Test Firebase integration for MANTA system')
    parser.add_argument('--config', type=str, default='../firebase/firebase_config.json',
                        help='Path to Firebase configuration file')
    parser.add_argument('--url', type=str, default=None,
                        help='Firebase database URL (overrides the one in config file)')
    parser.add_argument('--camera', type=str, default='test_camera',
                        help='Camera ID to use for tests')
    args = parser.parse_args()
    
    # Resolve relative path if needed
    config_path = os.path.abspath(args.config)
    
    print("\n===== MANTA Firebase Integration Test =====\n")
    
    # Test connection
    client = test_firebase_connection(config_path, args.url)
    
    if client:
        # Test write
        if test_firebase_write(client, args.camera):
            # Test read
            test_firebase_read(client, args.camera)
        
        # Test person logging
        test_log_person(client, args.camera)
        
        # Clean up
        client.close()
    
    print("\n===== Test Complete =====\n")

if __name__ == "__main__":
    main()
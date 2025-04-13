#!/usr/bin/env python3
"""
Send a test event to Firebase to simulate a person detection.
This script is useful for testing the Firebase integration without running the full camera system.
"""

import os
import sys
import json
import time
import random
import argparse
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Firebase utilities
from firebase.firebase_utils import init_firebase, log_person_detection

def load_config(config_path):
    """Load MANTA configuration file."""
    import yaml
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def send_test_event(config_path=None, camera_id=None, event_type='detection'):
    """Send a test event to Firebase."""
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'config.yaml'
        )
    
    # Load configuration
    config = load_config(config_path)
    if not config:
        print("Failed to load configuration. Exiting.")
        return False
    
    # Use camera_id from arguments or from config
    if camera_id is None:
        camera_id = config.get('camera', {}).get('id', 'test_camera')
    
    # Check if Firebase is enabled
    firebase_config = config.get('firebase', {})
    if not firebase_config.get('enabled', False):
        print("Firebase is not enabled in the configuration. Enabling it for this test.")
    
    # Get Firebase configuration
    firebase_config_path = firebase_config.get('config_path')
    if firebase_config_path and not os.path.isabs(firebase_config_path):
        firebase_config_path = os.path.abspath(os.path.join(
            os.path.dirname(config_path), firebase_config_path
        ))
    
    database_url = firebase_config.get('database_url')
    path_prefix = firebase_config.get('path_prefix', 'cameras')
    
    # Check if Firebase config exists
    if not firebase_config_path or not os.path.exists(firebase_config_path):
        print(f"Firebase config not found at {firebase_config_path}")
        return False
    
    print(f"Using Firebase config from: {firebase_config_path}")
    print(f"Database URL: {database_url}")
    print(f"Camera ID: {camera_id}")
    
    # Initialize Firebase
    client = init_firebase(firebase_config_path, database_url)
    if not client:
        print("Failed to initialize Firebase. Exiting.")
        return False
    
    # Create test event
    timestamp = datetime.now().isoformat()
    person_hash = f"test_person_{random.randint(10000, 99999)}"
    
    event_data = {
        "event_type": event_type,
        "person_hash": person_hash,
        "timestamp": timestamp,
        "camera_id": camera_id,
        "confidence": round(random.uniform(0.75, 0.99), 2),
        "is_test": True
    }
    
    print(f"\nSending test event to Firebase:")
    print(f"  Event type: {event_type}")
    print(f"  Person hash: {person_hash}")
    print(f"  Timestamp: {timestamp}")
    
    # Send the event
    result = log_person_detection(client, camera_id, event_data, path_prefix)
    
    if result:
        print("\n✅ Successfully sent test event to Firebase!")
        return True
    else:
        print("\n❌ Failed to send test event to Firebase.")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Send a test event to Firebase')
    parser.add_argument('--config', type=str, 
                        help='Path to MANTA configuration file')
    parser.add_argument('--camera', type=str,
                        help='Camera ID to use (overrides the one in config)')
    parser.add_argument('--type', type=str, default='detection',
                        choices=['detection', 'offline', 'error'],
                        help='Type of event to send')
    args = parser.parse_args()
    
    print("\n===== MANTA Firebase Test Event =====\n")
    
    success = send_test_event(args.config, args.camera, args.type)
    
    if success:
        print("\nCheck your Firebase console to see the event data.")
    
    print("\n===== Test Complete =====\n")

if __name__ == "__main__":
    main()
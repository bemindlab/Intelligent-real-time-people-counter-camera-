#!/usr/bin/env python3
"""
Helper script for running MANTA tests on macOS
"""

import sys
import os

def setup_macos_testing():
    """Setup environment for macOS testing"""
    
    # Check if running on macOS
    if sys.platform != 'darwin':
        return False
    
    # Get the project root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Add the mock directory to path
    mock_dir = os.path.join(root_dir, 'tests', 'mock')
    if not os.path.exists(mock_dir):
        os.makedirs(mock_dir)
    
    # Add the root directory to path
    sys.path.insert(0, root_dir)
    
    # Import the patch module
    try:
        sys.path.insert(0, mock_dir)
        from patch_picamera import patch_picamera
        patch_picamera()
        print("✅ macOS test environment setup complete")
        return True
    except ImportError:
        print("⚠️ Could not import patch_picamera module. Make sure it exists in the tests/mock directory.")
        return False
    except Exception as e:
        print(f"❌ Error setting up macOS test environment: {e}")
        return False

if __name__ == "__main__":
    setup_macos_testing()
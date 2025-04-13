#!/usr/bin/env python3
"""
Script to run MANTA tests on macOS
"""

import os
import sys
import subprocess
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the macOS test helper
from tests.macos_test_helper import setup_macos_testing

def run_tests(tests_to_run=None, save_output=None, display=True):
    """
    Run the MANTA tests on macOS
    
    Args:
        tests_to_run: List of tests to run ('webcam', 'streaming', 'firebase')
        save_output: Directory to save test output
        display: Whether to display visual output
    """
    
    # Setup macOS testing environment
    if not setup_macos_testing():
        print("❌ Failed to setup macOS test environment")
        return False
    
    print("\n===== Running MANTA Tests on macOS =====\n")
    
    # Default to all tests if none specified
    if not tests_to_run:
        tests_to_run = ['webcam', 'streaming']
    
    # Build command arguments
    display_arg = [] if display else ["--no-display"]
    save_arg = ["--save", save_output] if save_output else []
    
    # Define the tests
    all_tests = []
    
    if 'webcam' in tests_to_run:
        all_tests.append(["python", "tests/camera/test_camera.py", "--test", "webcam"] + display_arg + save_arg)
    
    if 'streaming' in tests_to_run:
        all_tests.append(["python", "tests/camera/test_camera.py", "--test", "streaming", "--duration", "3"] + display_arg + save_arg)
    
    if 'firebase' in tests_to_run:
        all_tests.append(["python", "tests/firebase/test_firebase.py"])
    
    # Run the tests
    success = True
    for cmd in all_tests:
        print(f"\nRunning: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"❌ Test failed: {' '.join(cmd)}")
            success = False
    
    if success:
        print("\n✅ All tests completed successfully")
    else:
        print("\n❌ Some tests failed")
    
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run MANTA tests on macOS')
    parser.add_argument('--tests', nargs='+', choices=['webcam', 'streaming', 'firebase', 'all'],
                        default=['webcam', 'streaming'],
                        help='Tests to run (default: webcam streaming)')
    parser.add_argument('--save', type=str, default=None,
                        help='Directory to save test output')
    parser.add_argument('--no-display', action='store_true',
                        help='Disable visual output')
    
    args = parser.parse_args()
    
    # Handle 'all' option
    if 'all' in args.tests:
        tests_to_run = ['webcam', 'streaming', 'firebase']
    else:
        tests_to_run = args.tests
    
    run_tests(tests_to_run, args.save, not args.no_display)
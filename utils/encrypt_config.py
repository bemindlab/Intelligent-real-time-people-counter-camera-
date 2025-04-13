#!/usr/bin/env python3
"""
สคริปต์อรรถประโยชน์สำหรับเข้ารหัสไฟล์การกำหนดค่าที่มีข้อมูลสำคัญ
(Utility script to encrypt configuration files with sensitive information)

สคริปต์นี้เข้ารหัสฟิลด์ที่สำคัญในไฟล์การกำหนดค่าเพื่อปกป้อง
ข้อมูลประจำตัวและข้อมูลสำคัญอื่นๆ สำหรับระบบ MANTA บน Raspberry Pi 5
"""

import os
import sys
import argparse
import logging
from getpass import getpass

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration utilities
from utils.config_utils import ConfigManager, encrypt_firebase_config, generate_encryption_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def encrypt_config(args):
    """Encrypt a configuration file."""
    # Get encryption key
    key = args.key
    if not key:
        key = getpass("Enter encryption key: ")
    
    # Get input and output paths
    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output) if args.output else input_path
    
    # Check if input file exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return False
    
    # Determine config type based on file extension
    if input_path.endswith('.json'):
        # Firebase config
        logger.info(f"Encrypting Firebase config: {input_path}")
        success = encrypt_firebase_config(input_path, output_path, key)
    else:
        # YAML config
        logger.info(f"Encrypting YAML config: {input_path}")
        
        # Create config manager
        config_manager = ConfigManager(input_path, key)
        
        # Mark sensitive fields
        sensitive_fields = []
        
        # Firebase section
        if 'firebase' in config_manager.config_data:
            firebase = config_manager.config_data.get('firebase', {})
            if 'database_url' in firebase:
                config_manager.set('firebase.database_url', firebase['database_url'], sensitive=True)
                sensitive_fields.append('firebase.database_url')
            if 'apiKey' in firebase:
                config_manager.set('firebase.apiKey', firebase['apiKey'], sensitive=True)
                sensitive_fields.append('firebase.apiKey')
        
        # Save with encryption
        success = config_manager.save_config()
        
        if success:
            logger.info(f"Encrypted sensitive fields: {', '.join(sensitive_fields)}")
    
    # Log result
    if success:
        logger.info(f"Config encrypted successfully: {output_path}")
    else:
        logger.error(f"Failed to encrypt config")
    
    return success

def generate_key(args):
    """Generate a new encryption key."""
    key = generate_encryption_key()
    if key:
        print(f"\nGenerated encryption key: {key}")
        print("\nIMPORTANT: Save this key securely! Without it, you will not be able to decrypt the data.")
        
        # Save to file if requested
        if args.save:
            try:
                with open(args.save, 'w') as f:
                    f.write(key)
                print(f"Key saved to: {args.save}")
            except Exception as e:
                logger.error(f"Error saving key to file: {e}")
        
        return True
    else:
        logger.error("Failed to generate encryption key")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Encrypt configuration files for MANTA system')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Encrypt command
    encrypt_parser = subparsers.add_parser('encrypt', help='Encrypt a configuration file')
    encrypt_parser.add_argument('--input', '-i', required=True,
                        help='Path to the input configuration file')
    encrypt_parser.add_argument('--output', '-o',
                        help='Path to save the encrypted configuration (defaults to overwriting input)')
    encrypt_parser.add_argument('--key', '-k',
                        help='Encryption key (if not provided, will prompt)')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate a new encryption key')
    generate_parser.add_argument('--save', '-s',
                          help='Save the generated key to file')
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'encrypt':
        encrypt_config(args)
    elif args.command == 'generate':
        generate_key(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
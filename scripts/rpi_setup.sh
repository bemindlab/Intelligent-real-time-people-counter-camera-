#!/bin/bash
#
# MANTA - Raspberry Pi Setup Script
# สคริปต์ตั้งค่าอัตโนมัติสำหรับ Raspberry Pi
#

set -e

# สี ANSI สำหรับผลลัพธ์
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ตรวจสอบว่ากำลังรันบน Raspberry Pi
function check_raspberry_pi() {
    if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        return 0
    else
        echo -e "${RED}สคริปต์นี้ออกแบบสำหรับ Raspberry Pi เท่านั้น${NC}"
        echo -e "${YELLOW}หากต้องการทดสอบบนแพลตฟอร์มอื่น โปรดดู docs/macos_testing.md${NC}"
        exit 1
    fi
}

# ตรวจสอบรุ่น Raspberry Pi และเลือกไฟล์กำหนดค่าที่เหมาะสม
function detect_pi_version() {
    local model=$(tr -d '\0' < /proc/device-tree/model)
    
    echo -e "${BLUE}ตรวจพบ: ${model}${NC}"
    
    if [[ $model == *"Raspberry Pi 5"* ]]; then
        echo -e "${GREEN}ตรวจพบ Raspberry Pi 5${NC}"
        PI_VERSION="5"
        CONFIG_FILE="config.rpi5.yaml"
    elif [[ $model == *"Raspberry Pi 4"* ]]; then
        echo -e "${GREEN}ตรวจพบ Raspberry Pi 4${NC}"
        PI_VERSION="4"
        CONFIG_FILE="config.rpi4.yaml"
    else
        echo -e "${YELLOW}ไม่พบ Raspberry Pi 4 หรือ 5 จะใช้การกำหนดค่าของ Pi 4${NC}"
        PI_VERSION="legacy"
        CONFIG_FILE="config.rpi4.yaml"
    fi
}

# ติดตั้งแพ็คเกจที่จำเป็น
function install_dependencies() {
    echo -e "${BLUE}กำลังติดตั้งแพ็คเกจที่จำเป็น...${NC}"
    
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        python3-opencv \
        python3-picamera \
        libatlas-base-dev \
        libhdf5-dev \
        libharfbuzz-dev \
        libwebp-dev \
        libtiff5 \
        libjasper-dev \
        libilmbase-dev \
        libopenexr-dev \
        libgstreamer1.0-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libqtgui4 \
        libqt4-test
    
    echo -e "${GREEN}การติดตั้งแพ็คเกจสำเร็จ${NC}"
}

# ติดตั้งแพ็คเกจ Python
function install_python_packages() {
    echo -e "${BLUE}กำลังติดตั้งแพ็คเกจ Python...${NC}"
    
    pip3 install --upgrade pip
    pip3 install -r models/requirements.txt
    
    echo -e "${GREEN}การติดตั้งแพ็คเกจ Python สำเร็จ${NC}"
}

# ตั้งค่าไฟล์กำหนดค่า
function setup_config() {
    echo -e "${BLUE}กำลังตั้งค่าไฟล์กำหนดค่าสำหรับ Raspberry Pi ${PI_VERSION}...${NC}"
    
    # ตรวจสอบว่ามีไฟล์กำหนดค่าสำหรับรุ่นนี้หรือไม่
    if [ ! -f "config/${CONFIG_FILE}" ]; then
        echo -e "${RED}ไม่พบไฟล์กำหนดค่าสำหรับ Raspberry Pi ${PI_VERSION}${NC}"
        exit 1
    fi
    
    # ถ้ามีไฟล์กำหนดค่าอยู่แล้ว ให้สำรองไว้
    if [ -f "config/config.yaml" ]; then
        cp config/config.yaml config/config.yaml.backup
        echo -e "${YELLOW}ไฟล์กำหนดค่าเดิมถูกสำรองไว้เป็น config.yaml.backup${NC}"
    fi
    
    # คัดลอกไฟล์กำหนดค่าสำหรับรุ่นนี้
    cp config/${CONFIG_FILE} config/config.yaml
    
    echo -e "${GREEN}ตั้งค่าไฟล์กำหนดค่าสำเร็จ${NC}"
}

# ตั้งค่า Camera Interface
function setup_camera() {
    echo -e "${BLUE}กำลังตรวจสอบและตั้งค่ากล้อง...${NC}"
    
    # ตรวจสอบว่า Camera Interface เปิดใช้งานหรือไม่
    if ! raspi-config nonint get_camera; then
        echo -e "${YELLOW}Camera Interface ยังไม่เปิดใช้งาน กำลังเปิดใช้งาน...${NC}"
        sudo raspi-config nonint do_camera 0
        echo -e "${GREEN}เปิดใช้งาน Camera Interface สำเร็จ${NC}"
        echo -e "${YELLOW}จำเป็นต้องรีบูต Raspberry Pi${NC}"
        read -p "รีบูตเดี๋ยวนี้? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}กำลังรีบูต...${NC}"
            sudo reboot
        fi
    else
        echo -e "${GREEN}Camera Interface เปิดใช้งานอยู่แล้ว${NC}"
    fi
    
    # ทดสอบกล้อง
    echo -e "${BLUE}กำลังทดสอบกล้อง...${NC}"
    
    if command -v raspistill &> /dev/null; then
        mkdir -p tests/output
        if raspistill -o tests/output/camera_test.jpg; then
            echo -e "${GREEN}การทดสอบกล้องสำเร็จ ภาพถูกบันทึกไว้ที่ tests/output/camera_test.jpg${NC}"
        else
            echo -e "${RED}การทดสอบกล้องล้มเหลว${NC}"
            echo -e "${YELLOW}ตรวจสอบว่ากล้องเชื่อมต่ออย่างถูกต้องและทำงานได้${NC}"
        fi
    else
        echo -e "${YELLOW}ไม่พบคำสั่ง raspistill ข้ามการทดสอบกล้อง${NC}"
    fi
}

# ตั้งค่าบริการ systemd
function setup_service() {
    echo -e "${BLUE}กำลังตั้งค่าบริการ systemd สำหรับการเริ่มอัตโนมัติ...${NC}"
    
    # สร้างไฟล์บริการ
    sudo tee /etc/systemd/system/manta.service > /dev/null << EOL
[Unit]
Description=MANTA Camera Person Detection Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/camera/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL
    
    # เปิดใช้งานบริการ
    sudo systemctl daemon-reload
    sudo systemctl enable manta.service
    
    echo -e "${GREEN}ตั้งค่าบริการ systemd สำเร็จ${NC}"
    echo -e "${BLUE}คุณสามารถควบคุมบริการด้วยคำสั่งเหล่านี้:${NC}"
    echo -e "  ${YELLOW}เริ่มบริการ:${NC} sudo systemctl start manta.service"
    echo -e "  ${YELLOW}หยุดบริการ:${NC} sudo systemctl stop manta.service"
    echo -e "  ${YELLOW}ตรวจสอบสถานะ:${NC} sudo systemctl status manta.service"
}

# ฟังก์ชันหลัก
function main() {
    echo -e "${BLUE}=== MANTA - สคริปต์ตั้งค่า Raspberry Pi ===${NC}"
    echo
    
    check_raspberry_pi
    detect_pi_version
    install_dependencies
    install_python_packages
    setup_config
    setup_camera
    
    # ถามผู้ใช้ว่าต้องการตั้งค่าบริการหรือไม่
    read -p "ต้องการตั้งค่าบริการ systemd สำหรับการเริ่มอัตโนมัติหรือไม่? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_service
    fi
    
    echo
    echo -e "${GREEN}=== การตั้งค่า MANTA สำหรับ Raspberry Pi ${PI_VERSION} เสร็จสมบูรณ์ ===${NC}"
    echo
    echo -e "${BLUE}คุณสามารถเริ่มใช้งาน MANTA ได้ด้วยคำสั่ง:${NC}"
    echo -e "  ${YELLOW}python3 camera/main.py${NC}"
    echo
}

# เริ่มการทำงาน
main
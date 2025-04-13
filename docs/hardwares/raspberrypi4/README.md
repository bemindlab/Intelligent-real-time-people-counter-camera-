# Raspberry Pi 4 Model B

## ข้อมูลทั่วไป

- **โปรเซสเซอร์**: Broadcom BCM2711, Quad core Cortex-A72 (ARM v8) 64-bit SoC @ 1.5GHz
- **RAM**: 2GB, 4GB, หรือ 8GB LPDDR4-3200 SDRAM
- **การเชื่อมต่อเครือข่าย**:
  - Gigabit Ethernet
  - Dual-band IEEE 802.11ac wireless
  - Bluetooth 5.0, BLE
- **พอร์ต USB**:
  - 2x USB 3.0
  - 2x USB 2.0
- **พอร์ต Video**:
  - 2x micro-HDMI ports (รองรับ 4Kp60)
  - 2-lane MIPI DSI display port
  - 2-lane MIPI CSI camera port
- **การ์ด SD**: Micro SD card slot
- **อื่นๆ**:
  - GPIO 40-pin header
  - 5V DC via USB-C connector
  - PoE capability (via separate PoE HAT)

## คุณสมบัติเด่น

1. **ประสิทธิภาพสูง**

   - CPU 4 คอร์ ความเร็ว 1.5GHz
   - GPU VideoCore VI
   - RAM เร็ว LPDDR4-3200

2. **การเชื่อมต่อครบครัน**

   - Gigabit Ethernet
   - WiFi 5GHz
   - Bluetooth 5.0
   - USB 3.0

3. **ความสามารถในการแสดงผล**
   - รองรับ 2 จอ 4K
   - MIPI DSI สำหรับจอ LCD
   - MIPI CSI สำหรับกล้อง

## การติดตั้งระบบ MANTA

1. **เตรียมการ**

   ```bash
   # อัพเดทระบบ
   sudo apt update
   sudo apt upgrade -y

   # ติดตั้ง dependencies
   sudo apt install -y python3-pip python3-venv
   ```

2. **ตั้งค่า Python Virtual Environment**

   ```bash
   # สร้าง virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # ติดตั้ง packages
   pip install -r requirements.txt
   ```

3. **ตั้งค่ากล้อง**

   ```bash
   # เปิดใช้งานกล้อง
   sudo raspi-config
   # เลือก Interface Options > Camera > Enable

   # ตรวจสอบการทำงาน
   vcgencmd get_camera
   ```

## การตั้งค่าพิเศษ

1. **Overclock (ถ้าต้องการ)**

   ```bash
   # แก้ไขไฟล์ config.txt
   sudo nano /boot/config.txt

   # เพิ่มบรรทัด:
   over_voltage=2
   arm_freq=1750
   gpu_freq=600
   ```

2. **เพิ่ม Swap Space**

   ```bash
   # สร้าง swap file
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile

   # เพิ่มใน /etc/fstab
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

## ข้อแนะนำในการใช้งาน

1. **การระบายความร้อน**

   - ใช้ heatsink
   - ใช้พัดลมระบายความร้อน
   - หลีกเลี่ยงการใช้งานในที่อุณหภูมิสูง

2. **การจ่ายไฟ**

   - ใช้ power supply อย่างน้อย 5.1V 3A
   - หลีกเลี่ยงการใช้ USB hub ที่ไม่มีไฟเลี้ยง
   - ตรวจสอบไฟ LED แสดงสถานะ

3. **การอัพเดท**
   - อัพเดทระบบเป็นประจำ
   - สำรองข้อมูลก่อนอัพเดท
   - ตรวจสอบ compatibility

## การแก้ไขปัญหาที่พบบ่อย

1. **ร้อนเกินไป**

   - ตรวจสอบ heatsink
   - ตรวจสอบพัดลม
   - ลดการใช้งาน CPU/GPU

2. **WiFi ไม่เสถียร**

   - ตรวจสอบระยะห่างจาก router
   - เปลี่ยนช่อง WiFi
   - อัพเดท firmware

3. **USB 3.0 มีปัญหา**
   - ตรวจสอบ power supply
   - ใช้ USB 2.0 แทน
   - อัพเดท firmware

## ข้อมูลเพิ่มเติม

- [เอกสารทางการจาก Raspberry Pi](https://www.raspberrypi.org/documentation/hardware/raspberrypi4/README.md)
- [คู่มือการใช้งาน](https://www.raspberrypi.org/documentation/usage/README.md)

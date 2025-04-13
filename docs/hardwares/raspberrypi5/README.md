# Raspberry Pi 5

## ข้อมูลทั่วไป

- **โปรเซสเซอร์**: Broadcom BCM2712, Quad core Cortex-A76 (ARM v8) 64-bit SoC @ 2.4GHz
- **RAM**: 4GB หรือ 8GB LPDDR4X-4267 SDRAM
- **การเชื่อมต่อเครือข่าย**:
  - Gigabit Ethernet
  - Dual-band IEEE 802.11ac wireless
  - Bluetooth 5.0, BLE
- **พอร์ต USB**:
  - 2x USB 3.0 (5Gbps)
  - 2x USB 2.0
- **พอร์ต Video**:
  - 1x micro-HDMI port (รองรับ 4Kp60)
  - 1x DisplayPort 1.4 (รองรับ 4Kp60)
  - 2-lane MIPI DSI display port
  - 2-lane MIPI CSI camera port
- **การ์ด SD**: Micro SD card slot
- **อื่นๆ**:
  - GPIO 40-pin header
  - 5V DC via USB-C connector
  - PoE capability (via separate PoE HAT)
  - PCIe 2.0 x1 interface

## คุณสมบัติเด่น

1. **ประสิทธิภาพสูงมาก**

   - CPU 4 คอร์ ความเร็ว 2.4GHz
   - GPU VideoCore VII
   - RAM เร็ว LPDDR4X-4267
   - PCIe 2.0 support

2. **การเชื่อมต่อล่าสุด**

   - USB 3.0 5Gbps
   - DisplayPort 1.4
   - PCIe 2.0
   - WiFi 6

3. **ความสามารถในการแสดงผล**
   - รองรับ 4K 60Hz
   - DisplayPort 1.4
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
   arm_freq=2400
   gpu_freq=750
   ```

2. **เพิ่ม Swap Space**

   ```bash
   # สร้าง swap file
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile

   # เพิ่มใน /etc/fstab
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

## ข้อแนะนำในการใช้งาน

1. **การระบายความร้อน**

   - ใช้ heatsink คุณภาพสูง
   - ใช้พัดลมระบายความร้อน
   - หลีกเลี่ยงการใช้งานในที่อุณหภูมิสูง
   - ตรวจสอบอุณหภูมิเป็นประจำ

2. **การจ่ายไฟ**

   - ใช้ power supply อย่างน้อย 5V 5A
   - หลีกเลี่ยงการใช้ USB hub ที่ไม่มีไฟเลี้ยง
   - ตรวจสอบไฟ LED แสดงสถานะ
   - ใช้ USB-C cable คุณภาพดี

3. **การอัพเดท**
   - อัพเดทระบบเป็นประจำ
   - สำรองข้อมูลก่อนอัพเดท
   - ตรวจสอบ compatibility
   - ติดตาม firmware updates

## การแก้ไขปัญหาที่พบบ่อย

1. **ร้อนเกินไป**

   - ตรวจสอบ heatsink
   - ตรวจสอบพัดลม
   - ลดการใช้งาน CPU/GPU
   - ใช้ thermal paste คุณภาพดี

2. **WiFi ไม่เสถียร**

   - ตรวจสอบระยะห่างจาก router
   - เปลี่ยนช่อง WiFi
   - อัพเดท firmware
   - ใช้ Ethernet แทน

3. **USB 3.0 มีปัญหา**
   - ตรวจสอบ power supply
   - ใช้ USB 2.0 แทน
   - อัพเดท firmware
   - ตรวจสอบ USB cable

## ข้อมูลเพิ่มเติม

- [เอกสารทางการจาก Raspberry Pi](https://www.raspberrypi.org/documentation/hardware/raspberrypi5/README.md)
- [คู่มือการใช้งาน](https://www.raspberrypi.org/documentation/usage/README.md)

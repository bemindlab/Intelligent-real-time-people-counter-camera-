# การกำหนดค่าระยะไกลสำหรับ MANTA Camera

คู่มือนี้อธิบายวิธีการใช้ระบบการกำหนดค่าระยะไกลของ MANTA ที่ทำงานผ่าน HTTP และ WiFi Direct โดยจะช่วยให้คุณสามารถกำหนดค่าและควบคุม MANTA Camera จากระยะไกลได้โดยไม่ต้องเชื่อมต่อโดยตรงกับเครื่อง Raspberry Pi

## 1. ภาพรวม

ระบบการกำหนดค่าระยะไกลประกอบด้วย:

- **เว็บเซิร์ฟเวอร์ HTTP**: ให้บริการ API และเว็บอินเทอร์เฟซสำหรับการกำหนดค่า
- **WiFi Direct**: เปิดใช้งานการเชื่อมต่อโดยตรงกับกล้องโดยไม่ต้องใช้เราเตอร์
- **Zeroconf/mDNS**: ช่วยให้ค้นพบอุปกรณ์ในเครือข่ายโดยอัตโนมัติ

## 2. การเปิดใช้งาน

### 2.1 ติดตั้งแพ็คเกจที่จำเป็น

```bash
# ติดตั้งแพ็คเกจที่จำเป็น
pip install flask flask-cors zeroconf
```

### 2.2 การเปิดใช้งานผ่านคำสั่ง

```bash
# เปิดใช้งาน HTTP การกำหนดค่าระยะไกลเท่านั้น
python camera/main.py --enable-remote-config

# กำหนดพอร์ตที่แตกต่าง
python camera/main.py --enable-remote-config --remote-config-port 8181

# เปิดใช้งาน WiFi Direct ด้วย
python camera/main.py --enable-remote-config --enable-wifi-direct
```

### 2.3 การเปิดใช้งานในไฟล์การกำหนดค่า

แก้ไขไฟล์ `config.yaml` เพื่อเปิดใช้งานถาวร:

```yaml
# การกำหนดค่าการกำหนดค่าระยะไกล (Remote Configuration)
remote_config:
  enabled: true
  port: 8080
  device_name: "MANTA-Camera-1"  # ชื่อที่จะแสดงในการค้นพบอุปกรณ์

# การกำหนดค่า WiFi Direct (WiFi Direct Configuration)
wifi_direct:
  enabled: true
  name: "MANTA-Direct"
  password: "manta1234"  # อย่างน้อย 8 ตัวอักษร
```

## 3. การเข้าถึงเว็บอินเทอร์เฟซ

หลังจากเปิดใช้งานระบบการกำหนดค่าระยะไกล คุณสามารถเข้าถึงเว็บอินเทอร์เฟซได้ดังนี้:

### 3.1 เข้าถึงผ่านเครือข่ายเดียวกัน

1. ตรวจสอบไอพีของ Raspberry Pi ในเครือข่าย
2. เปิดเบราว์เซอร์และเข้าไปที่ `http://<raspberry-pi-ip>:8080/`

### 3.2 เข้าถึงผ่าน WiFi Direct

1. ค้นหาเครือข่าย WiFi ชื่อ "MANTA-Direct" (หรือชื่อที่คุณกำหนด) ในอุปกรณ์ของคุณ
2. เชื่อมต่อกับเครือข่าย WiFi โดยใช้รหัสผ่านที่กำหนด
3. เปิดเบราว์เซอร์และเข้าไปที่ `http://192.168.42.1:8080/`

### 3.3 การค้นพบอัตโนมัติ

หากคุณมีซอฟต์แวร์ที่รองรับ Zeroconf/mDNS คุณสามารถค้นพบกล้อง MANTA ได้โดยอัตโนมัติ:

- บน macOS/iOS: กล้องจะปรากฏในเมนู Safari > Bonjour Bookmarks
- บน Windows: ใช้โปรแกรมที่รองรับ mDNS เช่น Bonjour Browser
- บน Android: ใช้แอป mDNS Browser

## 4. การใช้เว็บอินเทอร์เฟซ

เว็บอินเทอร์เฟซประกอบด้วยส่วนต่างๆ ต่อไปนี้:

### 4.1 ข้อมูลอุปกรณ์

แสดงข้อมูลพื้นฐานของกล้อง:
- ชื่ออุปกรณ์
- รหัสกล้อง
- IP Address
- สถานะระบบ

### 4.2 การตั้งค่ากล้อง

- แหล่งกล้อง (0 สำหรับกล้องเริ่มต้น, URL สำหรับสตรีม RTSP)
- ประเภทกล้อง (มาตรฐาน, WebCam Protocol, Raspberry Pi Camera)
- ความละเอียดและ FPS

### 4.3 การตั้งค่าการตรวจจับ

- เลือกโมเดล YOLO
- ค่าความเชื่อมั่นขั้นต่ำ
- อุปกรณ์ประมวลผล (CPU, NPU, CUDA)
- การข้ามเฟรม

### 4.4 การตั้งค่าเครือข่าย

- Firebase (เปิด/ปิด)
- URL Firebase
- อัปโหลดไฟล์การกำหนดค่า Firebase

### 4.5 WiFi Direct

- เปิด/ปิดการใช้งาน WiFi Direct
- ชื่อเครือข่าย
- รหัสผ่าน

### 4.6 การดำเนินการ

- บันทึกการตั้งค่า
- รีสตาร์ทบริการ
- รีบูตอุปกรณ์

## 5. การใช้ API

MANTA Camera มี HTTP API ที่คุณสามารถใช้เพื่อควบคุมอุปกรณ์จากระยะไกลได้:

### 5.1 รับข้อมูลระบบ

```
GET /api/system/info
```

### 5.2 ดูการกำหนดค่าปัจจุบัน

```
GET /api/config
```

### 5.3 อัปเดตการกำหนดค่า

```
POST /api/config
Content-Type: application/json

{
  "camera": {
    "source": 0,
    "resolution": {
      "width": 640,
      "height": 480
    },
    "fps": 15
  },
  "detection": {
    "confidence_threshold": 0.5
  }
}
```

### 5.4 รีสตาร์ทบริการ

```
POST /api/system/restart
```

### 5.5 รีบูตอุปกรณ์

```
POST /api/system/reboot
```

### 5.6 ดาวน์โหลดการกำหนดค่า

```
GET /api/config/download
```

### 5.7 อัปโหลดการกำหนดค่า

```
POST /api/config/upload
Content-Type: multipart/form-data
```

## 6. การตั้งค่า WiFi Direct

คุณสมบัติ WiFi Direct ช่วยให้คุณเชื่อมต่อกับกล้อง MANTA โดยตรงโดยไม่ต้องใช้เราเตอร์หรือจุดเชื่อมต่อ:

### 6.1 ข้อกำหนด

- Raspberry Pi เท่านั้นที่รองรับ WiFi Direct
- ต้องติดตั้งแพ็คเกจ: `wireless-tools`, `wpasupplicant`, `dnsmasq`

### 6.2 การเปิดใช้งาน

1. เปิดใช้งานในไฟล์การกำหนดค่า:
   ```yaml
   wifi_direct:
     enabled: true
     name: "MANTA-Direct"
     password: "manta1234"  # อย่างน้อย 8 ตัวอักษร
   ```

2. หรือเปิดใช้งานด้วยคำสั่ง:
   ```bash
   python camera/main.py --enable-remote-config --enable-wifi-direct
   ```

### 6.3 การเชื่อมต่อ

1. ค้นหาเครือข่าย WiFi ชื่อ "MANTA-Direct" (หรือชื่อที่คุณกำหนด)
2. เชื่อมต่อโดยใช้รหัสผ่านที่กำหนด
3. เข้าถึงเว็บอินเทอร์เฟซที่ `http://192.168.42.1:8080/`

### 6.4 การแก้ไขปัญหา

หากไม่เห็นเครือข่าย WiFi Direct:
1. ตรวจสอบว่าเปิดใช้งาน WiFi บน Raspberry Pi แล้ว
2. ตรวจสอบว่ามีการติดตั้งแพ็คเกจที่จำเป็น:
   ```bash
   sudo apt install wireless-tools wpasupplicant dnsmasq
   ```
3. รีบูต Raspberry Pi และลองอีกครั้ง

## 7. ความปลอดภัย

ควรระมัดระวังเมื่อเปิดใช้งานการกำหนดค่าระยะไกล:

1. **จำกัดการเข้าถึง**: ควรใช้งานระบบการกำหนดค่าระยะไกลเฉพาะในเครือข่ายส่วนตัวหรือเครือข่ายที่เชื่อถือได้

2. **รหัสผ่าน WiFi Direct**: ใช้รหัสผ่านที่แข็งแกร่งสำหรับการเชื่อมต่อ WiFi Direct (อย่างน้อย 12 ตัวอักษร)

3. **การเปิดพอร์ต**: หากต้องการเข้าถึงจากอินเทอร์เน็ต ควรใช้ reverse proxy ที่มีการรับรองความถูกต้องและการเข้ารหัส

4. **การอนุญาต**: ระบบปฏิบัติการอาจขอสิทธิ์ในการเปิดพอร์ตหรือจัดการ WiFi

## 8. ตัวเลือกเพิ่มเติม

### 8.1 รันเป็นเซิร์ฟเวอร์แยกต่างหาก

คุณสามารถรันเซิร์ฟเวอร์การกำหนดค่าระยะไกลแยกต่างหากได้:

```bash
python -m utils.remote_config --config /path/to/config.yaml
```

### 8.2 การติดตั้งเพิ่มเติมสำหรับการค้นพบอัตโนมัติ

```bash
# บน Raspberry Pi
sudo apt install avahi-daemon
```

## 9. การแก้ไขปัญหา

### 9.1 ไม่สามารถเข้าถึงเว็บอินเทอร์เฟซได้

1. ตรวจสอบว่ามีการเปิดใช้งานการกำหนดค่าระยะไกล:
   ```bash
   # ตรวจสอบว่าพอร์ตเปิดอยู่
   netstat -tuln | grep 8080
   ```

2. ตรวจสอบไฟร์วอลล์:
   ```bash
   # อนุญาตพอร์ต
   sudo ufw allow 8080/tcp
   ```

### 9.2 WiFi Direct ไม่ทำงาน

1. ติดตั้งแพ็คเกจที่จำเป็น:
   ```bash
   sudo apt install wireless-tools wpasupplicant dnsmasq
   ```

2. ตรวจสอบว่า WiFi กำลังทำงาน:
   ```bash
   rfkill list
   # ถ้าถูกบล็อก ให้ปลดบล็อก
   rfkill unblock wifi
   ```

3. ตรวจสอบบันทึกระบบ:
   ```bash
   sudo journalctl -u manta-camera -n 100
   ```

### 9.3 การแก้ไขปัญหาทั่วไป

1. รีสตาร์ทบริการ MANTA:
   ```bash
   sudo systemctl restart manta-camera
   ```

2. ตรวจสอบสถานะ:
   ```bash
   sudo systemctl status manta-camera
   ```

3. ตรวจสอบบันทึก:
   ```bash
   tail -f /var/log/manta-camera/manta.log
   ```
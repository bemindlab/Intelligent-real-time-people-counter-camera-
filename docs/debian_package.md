# การติดตั้ง MANTA ผ่านแพ็คเกจ Debian

เอกสารนี้อธิบายวิธีการสร้าง ติดตั้ง และจัดการแพ็คเกจ Debian ของระบบ MANTA

## การติดตั้งด้วยแพ็คเกจ Debian

วิธีนี้เป็นวิธีที่แนะนำสำหรับการติดตั้ง MANTA บน Raspberry Pi และระบบ Debian/Ubuntu อื่นๆ

### วิธีติดตั้ง

1. ดาวน์โหลดไฟล์ .deb ล่าสุดจาก [หน้าปล่อย](https://github.com/BemindTech/bmt-manta-camera/releases)

2. ติดตั้งแพ็คเกจ:
   ```bash
   sudo apt install ./manta-camera_0.1.0_all.deb
   ```

3. ในระหว่างการติดตั้ง สคริปต์จะตรวจจับรุ่น Raspberry Pi โดยอัตโนมัติและตั้งค่าที่เหมาะสมให้

4. เริ่มการปรับแต่งค่า:
   ```bash
   sudo manta-setup
   ```

### สิ่งที่แพ็คเกจทำในระหว่างการติดตั้ง

1. ติดตั้งไบนารีและสคริปต์ลงในตำแหน่งที่เหมาะสม:
   - `/usr/share/manta-camera/`: ไฟล์โปรแกรมและสคริปต์
   - `/etc/manta-camera/`: ไฟล์การกำหนดค่า
   - `/var/log/manta-camera/`: ไฟล์บันทึก

2. ตั้งค่า Raspberry Pi อัตโนมัติ:
   - เปิดใช้งาน Camera Interface
   - ตั้งค่าที่เหมาะสมสำหรับ Pi 4 หรือ Pi 5

3. ติดตั้งและเปิดใช้งานบริการ systemd:
   - `manta-camera.service`: เริ่มต้นและจัดการ MANTA

## การสร้างแพ็คเกจ Debian เอง

หากต้องการสร้างแพ็คเกจด้วยตนเอง มีขั้นตอนดังนี้:

### ความต้องการเบื้องต้น

```bash
sudo apt install build-essential debhelper devscripts dh-python
```

### การสร้างแพ็คเกจ

1. โคลนรีโพสิทอรี:
   ```bash
   git clone https://github.com/BemindTech/bmt-manta-camera.git
   cd bmt-manta-camera
   ```

2. สร้างแพ็คเกจ:
   ```bash
   dpkg-buildpackage -us -uc -b
   ```

3. แพ็คเกจจะถูกสร้างในไดเร็กทอรีแม่:
   ```bash
   ls -l ../manta-camera_*.deb
   ```

## การจัดการแพ็คเกจ

### การอัปเกรด

เมื่อมีเวอร์ชันใหม่ออกมา คุณสามารถอัปเกรดได้ด้วย:

```bash
sudo apt install ./manta-camera_new-version_all.deb
```

### การถอนการติดตั้ง

ถอนการติดตั้ง MANTA:

```bash
sudo apt remove manta-camera
```

ถอนการติดตั้งพร้อมลบไฟล์การกำหนดค่า:

```bash
sudo apt purge manta-camera
```

### การตรวจสอบเวอร์ชัน

ตรวจสอบเวอร์ชันที่ติดตั้ง:

```bash
dpkg -l manta-camera
```

## การแก้ไขปัญหาการติดตั้ง

### บันทึกการติดตั้ง

ตรวจสอบบันทึกการติดตั้ง:

```bash
cat /var/log/dpkg.log | grep manta-camera
```

### ปัญหาที่พบบ่อย

1. **การเข้าถึงกล้องล้มเหลว**
   ```bash
   sudo raspi-config
   ```
   เลือก "Interface Options" > "Camera" และเปิดใช้งาน จากนั้นรีบูต

2. **บริการไม่เริ่มทำงาน**
   ```bash
   sudo systemctl status manta-camera
   ```
   ตรวจสอบข้อความผิดพลาดและวิธีแก้ไข

3. **ข้อผิดพลาดการติดตั้งแพ็คเกจ**
   ```bash
   sudo apt --fix-broken install
   ```
   จากนั้นลองติดตั้งแพ็คเกจอีกครั้ง

## คำแนะนำสำหรับผู้ดูแลแพ็คเกจ

### การอัปเดตแพ็คเกจ

1. แก้ไขเวอร์ชันใน `debian/changelog`:
   ```
   dch -i "รายละเอียดการเปลี่ยนแปลง"
   ```

2. อัปเดตส่วนที่ขึ้นอยู่กับ:
   ```
   dch -i "อัปเดตการขึ้นต่อกันของแพ็คเกจ"
   ```

3. สร้างแพ็คเกจใหม่:
   ```
   dpkg-buildpackage -us -uc -b
   ```

### การทดสอบแพ็คเกจ

ทดสอบการติดตั้งในสภาพแวดล้อมสะอาด:

```bash
sudo debootstrap --variant=minbase bullseye ./chroot-test
sudo chroot ./chroot-test
apt install /path/to/manta-camera_*.deb
```

## เนื้อหาแพ็คเกจ

รายการไฟล์ในแพ็คเกจ:

```bash
dpkg -L manta-camera
```

### ไฟล์การกำหนดค่า

- `/etc/manta-camera/config.yaml`: การกำหนดค่าหลัก
- `/etc/manta-camera/config.rpi4.yaml`: การกำหนดค่าเฉพาะสำหรับ Pi 4
- `/etc/manta-camera/config.rpi5.yaml`: การกำหนดค่าเฉพาะสำหรับ Pi 5

### สคริปต์

- `/usr/bin/manta-setup`: เครื่องมือตั้งค่าอินเทอร์แอคทีฟ

### บริการ

- `/lib/systemd/system/manta-camera.service`: บริการระบบ
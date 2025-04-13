# การกำหนดค่าที่ปลอดภัยสำหรับ MANTA (Secure Configuration for MANTA)

เอกสารนี้อธิบายวิธีการจัดการข้อมูลการกำหนดค่าที่สำคัญอย่างปลอดภัย เช่น ข้อมูลประจำตัว Firebase ในระบบ MANTA

## ภาพรวม (Overview)

ระบบ MANTA มีระบบการกำหนดค่าที่ปลอดภัยซึ่งสามารถเข้ารหัสข้อมูลสำคัญ เช่น:
- ข้อมูลประจำตัว Firebase (Firebase credentials)
- คีย์ API (API keys)
- URL ฐานข้อมูล (Database URLs)
- โทเค็นการยืนยันตัวตน (Authentication tokens)

การเข้ารหัสใช้อัลกอริธึมการเข้ารหัสแบบสมมาตร Fernet ซึ่งให้ความปลอดภัยระดับสูงสำหรับข้อมูลประจำตัวที่จัดเก็บ

## การสร้างคีย์เข้ารหัส (Generating an Encryption Key)

เพื่อปกป้องข้อมูลการกำหนดค่าที่สำคัญของคุณ คุณจำเป็นต้องสร้างคีย์เข้ารหัสก่อน:

```bash
# สร้างคีย์เข้ารหัสใหม่
./utils/encrypt_config.py generate

# บันทึกคีย์ลงในไฟล์ (ทางเลือก)
./utils/encrypt_config.py generate --save my_key.txt
```

**สำคัญ**: เก็บคีย์นี้ไว้อย่างปลอดภัย! ผู้ที่มีสิทธิ์เข้าถึงคีย์สามารถถอดรหัสข้อมูลการกำหนดค่าที่สำคัญของคุณได้

## การเข้ารหัสไฟล์กำหนดค่า (Encrypting Configuration Files)

### การกำหนดค่า Firebase (Firebase Configuration)

ไฟล์การกำหนดค่า Firebase มีข้อมูลประจำตัวที่สำคัญ เพื่อเข้ารหัส:

```bash
# เข้ารหัสไฟล์การกำหนดค่า Firebase
./utils/encrypt_config.py encrypt --input firebase/firebase_config.json
```

การดำเนินการนี้จะแก้ไขไฟล์ในตำแหน่งเดิม โดยเข้ารหัสฟิลด์ที่สำคัญเช่น `private_key`, `client_email` และ `apiKey`

### ไฟล์การกำหนดค่าหลัก (Main Configuration File)

คุณยังสามารถเข้ารหัสฟิลด์ที่สำคัญในไฟล์การกำหนดค่าหลัก:

```bash
# เข้ารหัสไฟล์การกำหนดค่าหลัก
./utils/encrypt_config.py encrypt --input config/config.yaml
```

การดำเนินการนี้จะเข้ารหัสฟิลด์เช่น URL ฐานข้อมูลและคีย์ API

## Running MANTA with Encrypted Configuration

To use the encrypted configuration, you need to provide the encryption key when running MANTA:

```bash
# Provide the key directly
python camera/main.py --encrypt-key "your-encryption-key"

# Or provide the key in a file
python camera/main.py --encrypt-key-file my_key.txt
```

## Securing the Encryption Key

For production deployments, you should securely manage the encryption key:

1. **Environment Variables**: Store the key in an environment variable instead of in a file.
2. **Key Management Service**: Use a cloud key management service if available.
3. **Secure Storage**: On Raspberry Pi, consider using encrypted storage for the key.

## Example: Setting Up Secure Firebase Configuration

1. Generate an encryption key:
   ```bash
   ./utils/encrypt_config.py generate --save .secret_key
   ```

2. Encrypt your Firebase configuration:
   ```bash
   ./utils/encrypt_config.py encrypt --input firebase/firebase_config.json --key $(cat .secret_key)
   ```

3. Update your `.gitignore` to exclude the key:
   ```
   # Add to .gitignore
   .secret_key
   ```

4. Run MANTA with the encrypted configuration:
   ```bash
   python camera/main.py --encrypt-key-file .secret_key
   ```

## Using Environment Variables

For production deployments, you can use environment variables:

```bash
# Store the key in an environment variable
export MANTA_ENCRYPTION_KEY="your-encryption-key"

# Run with the key from the environment variable
python camera/main.py --encrypt-key "$MANTA_ENCRYPTION_KEY"
```

## Security Considerations

- Never commit encryption keys to version control
- Regularly rotate your encryption keys
- Use separate keys for development and production
- Consider using hardware security modules (HSMs) for production keys
- Apply appropriate file permissions to configuration files
import os
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

# 📍 URL สตรีมตรง (.m3u8)
TARGET_URL = "https://cdn-fr1-eu.lncoperations.ee/hls/cnbc_live/index.m3u8" 
RECORD_DURATION = 7200  # ⏱️ บันทึก 2 ชั่วโมง (2 * 60 * 60 = 7200 วินาที)

# 📍 บังคับใช้เวลาประเทศไทย (UTC+7)
th_time = datetime.now(ZoneInfo("Asia/Bangkok"))
filename = f"./cnbc_radio_{th_time.strftime('%Y%m%d_%H%M%S')}.mp3"

print("🤖 เริ่มต้นทำงานระบบบันทึกเสียงอัตโนมัติ...")
print(f"🎙️ กำลังบันทึกเสียงสดเป็นเวลา 2 ชั่วโมง: {filename}")

# 📍 ใช้ ffmpeg ดึงสตรีม m3u8 แปลงเป็น MP3
cmd = [
    'ffmpeg', '-y',
    '-i', TARGET_URL,
    '-t', str(RECORD_DURATION),
    '-vn',                  # ตัดภาพออก เอาเฉพาะเสียง
    '-acodec', 'libmp3lame', # แปลงเป็นรหัส MP3
    filename
]

try:
    # 📍 เผื่อ Timeout ไว้ 7320 วินาที (2 ชั่วโมง 2 นาที) ให้ ffmpeg ทำงานจบสมบูรณ์
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=RECORD_DURATION + 120)
    
    if result.returncode == 0 and os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"🎉 บันทึกสำเร็จ! ไฟล์ขนาด: {os.path.getsize(filename)} ไบต์")
    else:
        print(f"❌ เกิดข้อผิดพลาด (Exit code: {result.returncode})")
        print(f"Log จากระบบ:\n{result.stderr}")

except subprocess.TimeoutExpired:
    print("❌ สคริปต์ทำงานเกินเวลาที่กำหนด (Timeout)")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดอื่น ๆ: {e}")

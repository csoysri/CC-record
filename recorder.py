import os
import subprocess
from datetime import datetime

TARGET_URL = "https://livenewschat.eu/cnbc-live-stream/"
RECORD_DURATION = 7200  # 2 ชั่วโมง (2 * 60 * 60 = 7,200 วินาที)
filename = f"./cnbc_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"

print("🤖 เริ่มต้นทำงานระบบบันทึกเสียงอัตโนมัติ...")
print(f"🎙️ กำลังดึงสัญญาณและบันทึกเสียงระยะเวลา 2 ชั่วโมง: {filename}")

# ใช้ yt-dlp ดึงสตรีมจากหน้าเว็บ แล้วส่งให้ ffmpeg อัดเฉพาะเสียง (-vn)
cmd = [
    'yt-dlp',
    '--downloader', 'ffmpeg',
    '--downloader-args', f'ffmpeg:-t {RECORD_DURATION} -vn -acodec libmp3lame',
    '-o', filename,
    TARGET_URL
]

try:
    # เพิ่ม timeout เผื่อเวลาประมวลผลไฟล์เสร็จสิ้นอีก 180 วินาที
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=RECORD_DURATION + 180)
    
    if result.returncode == 0 and os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"🎉 บันทึกเสียงสำเร็จ! ขนาดไฟล์: {os.path.getsize(filename)} ไบต์")
    else:
        print(f"❌ เกิดข้อผิดพลาดในการบันทึก (Exit code: {result.returncode})")
        print(f"Log จากระบบ:\n{result.stderr}")

except subprocess.TimeoutExpired:
    print("❌ สคริปต์ทำงานเกินเวลาที่กำหนด (Timeout)")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดอื่น ๆ: {e}")

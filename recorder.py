import os
import subprocess
from datetime import datetime

TARGET_URL = "https://livenewschat.eu/cnbc-live-stream/"
RECORD_DURATION = 5  # ⏱️ ทดสอบบันทึก 5 วินาที
filename = f"./cnbc_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"

print("🤖 เริ่มต้นทดสอบระบบบันทึกเสียงอัตโนมัติ...")
print(f"🎙️ กำลังทดลองบันทึกเสียง 5 วินาที: {filename}")

# ใช้ yt-dlp ดึงสตรีมและตัดเฉพาะเสียง
cmd = [
    'yt-dlp',
    '--downloader', 'ffmpeg',
    '--downloader-args', f'ffmpeg:-t {RECORD_DURATION} -vn -acodec libmp3lame',
    '-o', filename,
    TARGET_URL
]

try:
    # ตั้ง timeout ไว้ 60 วินาที เผื่อเวลาเตรียมการเชื่อมต่อ
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0 and os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"🎉 ทดสอบสำเร็จ! ไฟล์ขนาด: {os.path.getsize(filename)} ไบต์")
    else:
        print(f"❌ เกิดข้อผิดพลาด (Exit code: {result.returncode})")
        print(f"Log จากระบบ:\n{result.stderr}")

except subprocess.TimeoutExpired:
    print("❌ สคริปต์ทำงานเกินเวลา (Timeout)")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดอื่น ๆ: {e}")

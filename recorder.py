import os
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

TARGET_URL = "https://cdn-fr1-eu.lncoperations.ee/hls/cnbc_live/index.m3u8" 
RECORD_DURATION = 7200  # บันทึก 2 ชั่วโมง

th_time = datetime.now(ZoneInfo("Asia/Bangkok"))
filename = f"./cnbc_radio_{th_time.strftime('%Y%m%d_%H%M%S')}.mp3"

print("🤖 เริ่มต้นทำงานระบบบันทึกเสียงอัตโนมัติ...")
print(f"🎙️ กำลังบันทึกเสียงสดเป็นเวลา 2 ชั่วโมง: {filename}")

# 📍 เพิ่ม Header ป้องกันโดน Access Denied
cmd = [
    'ffmpeg', '-y',
    '-headers', 'Referer: https://livenewschat.eu/\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n',
    '-i', TARGET_URL,
    '-t', str(RECORD_DURATION),
    '-vn',
    '-acodec', 'libmp3lame',
    filename
]

try:
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

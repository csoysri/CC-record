import os
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

TARGET_URL = "https://cdn-fr1-eu.lncoperations.ee/hls/cnbc_live/index.m3u8"

# 💡 แนะนำ: ทดสอบด้วยเวลาสั้นๆ ก่อน เช่น 30 วินาที แล้วค่อยเปลี่ยนกลับเป็น 7200
RECORD_DURATION = 30  # วินาที (เปลี่ยนเป็น 7200 เมื่อทดสอบผ่านแล้ว)

th_time = datetime.now(ZoneInfo("Asia/Bangkok"))
filename = f"./cnbc_radio_{th_time.strftime('%Y%m%d_%H%M%S')}.mp3"

print("🤖 เริ่มต้นทำงานระบบบันทึกเสียงอัตโนมัติ...")
print(f"🎙️ กำลังบันทึกเสียงเป็นเวลา {RECORD_DURATION} วินาที: {filename}")

# Header และ Option สำหรับป้องกัน Stream หลุด/ค้าง
headers = (
    "Referer: https://livenewschat.eu/\r\n"
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n"
)

cmd = [
    'ffmpeg', '-y',
    # จัดการ network หาก stream สะดุด
    '-reconnect', '1',
    '-reconnect_streamed', '1',
    '-reconnect_delay_max', '5',
    '-headers', headers,
    '-i', TARGET_URL,
    '-t', str(RECORD_DURATION),
    '-vn',
    '-acodec', 'libmp3lame',
    '-ab', '128k',
    filename
]

try:
    # นำ capture_output=True ออก เพื่อให้แสดง log ของ ffmpeg บนหน้าจอ terminal ทันที
    result = subprocess.run(cmd, timeout=RECORD_DURATION + 60)
    
    if result.returncode == 0 and os.path.exists(filename) and os.path.getsize(filename) > 0:
        file_size_kb = os.path.getsize(filename) / 1024
        print(f"\n🎉 บันทึกสำเร็จ! ไฟล์: {filename} (ขนาด: {file_size_kb:.2f} KB)")
    else:
        print(f"\n❌ เกิดข้อผิดพลาด (Exit code: {result.returncode})")

except subprocess.TimeoutExpired:
    print("\n❌ สคริปต์ทำงานเกินเวลาที่กำหนด (Timeout)")
except Exception as e:
    print(f"\n❌ เกิดข้อผิดพลาดอื่น ๆ: {e}")

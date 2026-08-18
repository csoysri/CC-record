import os
import time
from datetime import datetime
import subprocess

# 🌟 สลับมาดึงสัญญาณวิทยุจากพอร์ตสตรีมมิ่งที่เปิดรับไอพีต่างประเทศโดยเฉพาะ
STREAM_URL = "https://radio12.plathong.net/7356/;stream.mp3" 
RECORD_DURATION = 2100  # อัดเสียง 35 นาที (หน่วยวินาที)
filename = f"./kcs_radio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"

print("🤖 เริ่มต้นทำงานระบบบันทึกเสียงอัตโนมัติ...")
print(f"🎙️ กำลังดึงสัญญาณตรงและส่งต่อให้ ffmpeg บันทึก: {filename}")

# ใช้พารามิเตอร์แบบเบสิกที่สุดเพื่อป้องกันอาการเปิดพอร์ตล้มเหลวบน GitHub Actions
cmd = [
    'ffmpeg', '-y',
    '-i', STREAM_URL,
    '-t', str(RECORD_DURATION),
    '-c:a', 'copy',
    filename
]

try:
    # เพิ่ม timeout ป้องกันสคริปต์ค้างเผื่อกรณีเซิร์ฟเวอร์ล่ม (บวกเผื่อให้ ffmpeg ทำงานเสร็จ 60 วินาที)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=RECORD_DURATION + 60)
    
    if result.returncode == 0:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            print(f"🎉 บันทึกเสียงสำเร็จ! ขนาดไฟล์: {os.path.getsize(filename)} ไบต์")
        else:
            print("⚠️ ffmpeg ทำงานจบ แต่ไฟล์ที่ได้ขนาด 0 ไบต์")
    else:
        print(f"❌ ffmpeg แจ้งข้อผิดพลาด (Exit code: {result.returncode})")
        print(f"Log จากระบบ:\n{result.stderr}")

except subprocess.TimeoutExpired:
    print("❌ สคริปต์ทำงานเกินเวลาที่กำหนด (Timeout)")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดอื่น ๆ: {e}")

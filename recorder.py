import os
import subprocess
import glob
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai

TARGET_URL = "https://cdn-fr1-eu.lncoperations.ee/hls/cnbc_live/index.m3u8" 
RECORD_DURATION = 30   # เวลาบันทึกรวม: 7200 วินาที (2 ชั่วโมง)
SEGMENT_DURATION = 15  # เวลาตัดแบ่งแต่ละไฟล์: 420 วินาที (7 นาที)

# ดึง API Key จาก Environment Variable ของระบบ (ปลอดภัยกว่าใส่ตรงๆ)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def record_stream(output_filename, duration):
    """ฟังก์ชันอัดเสียงสดจาก CNBC"""
    print("🤖 เริ่มต้นทำงานระบบบันทึกเสียงอัตโนมัติ...")
    print(f"🎙️ กำลังบันทึกเสียงเป็นเวลา {duration} วินาที...")
    
    headers = (
        "Referer: https://livenewschat.eu/\r\n"
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n"
    )

    cmd = [
        'ffmpeg', '-y',
        '-reconnect', '1',
        '-reconnect_streamed', '1',
        '-reconnect_delay_max', '5',
        '-headers', headers,
        '-i', TARGET_URL,
        '-t', str(duration),
        '-vn',
        '-acodec', 'libmp3lame',
        '-ab', '128k',
        output_filename
    ]
    
    result = subprocess.run(cmd)
    return result.returncode == 0 and os.path.exists(output_filename) and os.path.getsize(output_filename) > 0

def split_audio(input_file, date_prefix, segment_time=420):
    """ฟังก์ชันตัดไฟล์เสียงออกเป็นท่อนๆ ละ 7 นาที"""
    print(f"\n✂️ กำลังตัดแบ่งไฟล์ '{input_file}' เป็นท่อนละ 7 นาที...")
    output_pattern = f"./{date_prefix}_part_%03d.mp3"
    
    cmd = [
        'ffmpeg', '-y',
        '-i', input_file,
        '-f', 'segment',
        '-segment_time', str(segment_time),
        '-c', 'copy',
        output_pattern
    ]
    subprocess.run(cmd, check=True)
    segments = sorted(glob.glob(f"./{date_prefix}_part_*.mp3"))
    print(f"🎉 ตัดไฟล์สำเร็จ! ได้ทั้งหมด {len(segments)} ไฟล์")
    return segments

def transcribe_and_translate(audio_path):
    """ฟังก์ชันส่งไฟล์เสียงไปให้ Gemini ถอดความและแปลไทย"""
    if not client:
        print("⚠️ ไม่พบ GEMINI_API_KEY ข้ามการแปลภาษา")
        return None

    print(f"🤖 กำลังให้ AI ฟังและแปลไฟล์: {audio_path}...")
    try:
        # อัปโหลดไฟล์เสียงไปที่ Gemini
        audio_file = client.files.upload(file=audio_path)
        
        prompt = """
        คุณเป็นนักแปลข่าวเศรษฐกิจและการเงินมืออาชีพ:
        1. กรุณาถอดความสิ่งที่ผู้พูดในเสียงพูด
        2. แปลและสรุปเนื้อหาสำคัญออกมาเป็น 'ภาษาไทย' ที่เข้าใจง่าย แบ่งเป็นหัวข้อย่อย (Bullet points) ชัดเจน
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[audio_file, prompt]
        )
        
        # ลบไฟล์ออกจากเซิร์ฟเวอร์ Gemini ชั่วคราวหลังประมวลผลเสร็จ
        client.files.delete(name=audio_file.name)
        
        return response.text
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการแปลไฟล์ {audio_path}: {e}")
        return None

# ==================== ลำดับการทำงานหลัก ====================
if __name__ == "__main__":
    th_time = datetime.now(ZoneInfo("Asia/Bangkok"))
    date_str = th_time.strftime('%Y%m%d_%H%M%S')
    main_file = f"./raw_cnbc_{date_str}.mp3"

    # 1. บันทึกเสียง
    success = record_stream(main_file, RECORD_DURATION)

    if success:
        print(f"✅ บันทึกไฟล์หลักสำเร็จ: {main_file}")
        
        # 2. ตัดแบ่งไฟล์ท่อนละ 7 นาที
        segment_files = split_audio(main_file, date_str, SEGMENT_DURATION)
        
        # 3. วนลูปส่งแต่ละไฟล์ไปแปลไทย และเซฟเป็นไฟล์ .txt
        print("\n🌐 เริ่มต้นการแปลภาษาด้วย Gemini...")
        for seg in segment_files:
            th_text = transcribe_and_translate(seg)
            if th_text:
                txt_filename = seg.replace(".mp3", "_แปลไทย.txt")
                with open(txt_filename, "w", encoding="utf-8") as f:
                    f.write(th_text)
                print(f"💾 บันทึกคำแปลเรียบร้อย: {txt_filename}")
            
            # พัก 3 วินาที เพื่อไม่ให้ยิงคำขอถี่เกินไป
            time.sleep(3)
            
        print("\n✨ ประมวลผลเสร็จสิ้นครบทุกขั้นตอน!")
    else:
        print("❌ การบันทึกเสียงล้มเหลว")

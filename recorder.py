import os
import subprocess
import glob
import time
import asyncio
import edge_tts
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai

TARGET_URL = "https://cdn-fr1-eu.lncoperations.ee/hls/cnbc_live/index.m3u8" 

# 🛠️ ตั้งค่าเวลาใช้งานจริง: อัด 2 ชั่วโมง (7200 วินาที) / ตัดท่อนละ 7 นาที (420 วินาที)
RECORD_DURATION = 10800   # (หากต้องการทดสอบ ให้แก้เป็น 30)
SEGMENT_DURATION = 420  # (หากต้องการทดสอบ ให้แก้เป็น 15)

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
    """ฟังก์ชันตัดแบ่งไฟล์เสียง"""
    print(f"\n✂️ กำลังตัดแบ่งไฟล์ '{input_file}' เป็นท่อนละ {segment_time} วินาที...")
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

def transcribe_and_translate(audio_path, max_retries=3):
    """ฟังก์ชันส่งไฟล์เสียงไปแปลไทย (ภาษาไทยล้วน) พร้อมระบบลองใหม่อัตโนมัติ"""
    if not client:
        print("⚠️ ไม่พบ GEMINI_API_KEY ข้ามการแปลภาษา")
        return None

    print(f"🤖 กำลังให้ AI ฟังและแปลไฟล์: {audio_path}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            audio_file = client.files.upload(file=audio_path)
            
            prompt = """
            คุณเป็นนักแปลและผู้ประกาศข่าวเศรษฐกิจมืออาชีพ:
            1. แปลและสรุปเนื้อหาข่าวทั้งหมดออกมาเป็น "ภาษาไทยล้วนเท่านั้น"
            2. ห้ามใส่ข้อความภาษาอังกฤษต้นฉบับ ห้ามเขียนอังกฤษกำกับ (ยกเว้นชื่อเฉพาะหรือชื่อบริษัท/หุ้น)
            3. เรียบเรียงเป็นประโยคที่สละสลวย กระชับ เหมาะสำหรับการอ่านออกเสียงให้ผู้ฟังเข้าใจทันที
            """
            
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[audio_file, prompt]
            )
            
            client.files.delete(name=audio_file.name)
            return response.text
            
        except Exception as e:
            print(f"⚠️ ครั้งที่ {attempt} พบปัญหา ({e})")
            if attempt < max_retries:
                wait_sec = attempt * 5
                print(f"⏳ กำลังรอ {wait_sec} วินาทีก่อนลองใหม่อัตโนมัติ...")
                time.sleep(wait_sec)
            else:
                print(f"❌ แปลไฟล์ {audio_path} ล้มเหลวหลังจากลองครบ {max_retries} ครั้ง")
                return None

async def text_to_speech_thai(text, output_audio_path):
    """ฟังก์ชัน AI สังเคราะห์เสียงอ่านข่าวภาษาไทย (ใช้เสียงพากย์ผู้ประกาศข่าว)"""
    print(f"🗣️ กำลังสร้างเสียง AI อ่านข่าวไทย: {output_audio_path}...")
    try:
        # ใช้เสียงพากย์ Neural: 'th-TH-PremwadeeNeural' (เสียงผู้หญิง) หรือ 'th-TH-NiwatNeural' (เสียงผู้ชาย)
        voice = "th-TH-PremwadeeNeural"
        tts = edge_tts.Communicate(text, voice)
        await tts.save(output_audio_path)
        print(f"✅ บันทึกไฟล์เสียงพากย์ไทยสำเร็จ: {output_audio_path}")
    except Exception as e:
        print(f"❌ สังเคราะห์เสียงอ่านข่าวล้มเหลว: {e}")

# ==================== ลำดับการทำงานหลัก ====================
if __name__ == "__main__":
    th_time = datetime.now(ZoneInfo("Asia/Bangkok"))
    date_str = th_time.strftime('%Y%m%d_%H%M%S')
    main_file = f"./raw_cnbc_{date_str}.mp3"

    # 1. อัดเสียง
    success = record_stream(main_file, RECORD_DURATION)

    if success:
        print(f"✅ บันทึกไฟล์หลักสำเร็จ: {main_file}")
        
        # 2. ตัดแบ่งไฟล์
        segment_files = split_audio(main_file, date_str, SEGMENT_DURATION)
        
        # 3. แปลภาษาไทย + สร้างเสียงอ่านข่าวภาษาไทย
        print("\n🌐 เริ่มต้นกระบวนการแปลและสร้างเสียงอ่านข่าวไทย...")
        for seg in segment_files:
            th_text = transcribe_and_translate(seg)
            if th_text:
                # 3.1 บันทึกเป็นไฟล์ข้อความ .txt
                txt_filename = seg.replace(".mp3", "_แปลไทย.txt")
                with open(txt_filename, "w", encoding="utf-8") as f:
                    f.write(th_text)
                print(f"💾 บันทึกคำแปลเรียบร้อย: {txt_filename}")
                
                # 3.2 สร้างไฟล์เสียงอ่านข่าวภาษาไทย .mp3
                tts_filename = seg.replace(".mp3", "_อ่านข่าวไทย.mp3")
                asyncio.run(text_to_speech_thai(th_text, tts_filename))
            
            time.sleep(2)
            
        print("\n✨ ประมวลผลครบทุกขั้นตอน พร้อมฟังใน Google Drive ทันที!")
    else:
        print("❌ การบันทึกเสียงล้มเหลว")

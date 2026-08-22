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

# 🛠️ ตั้งค่าเวลาใช้งานจริง: อัด 3 ชั่วโมง (10800 วินาที) / ตัดท่อนละ 7 นาที (420 วินาที)
RECORD_DURATION = 10800   # (หากต้องการทดสอบ ให้แก้เป็น 30)
SEGMENT_DURATION = 420    # (หากต้องการทดสอบ ให้แก้เป็น 15)

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
    print(f"🎉 ตัดไฟล์สำเร็จ! ได้ทั้งหมด {len(segments)} ไฟล์\n")
    return segments

def transcribe_and_translate(audio_path, max_retries=3):
    """ฟังก์ชันส่งไฟล์เสียงไปแปลไทย (ภาษาไทยล้วน) พร้อมระบบลองใหม่อัตโนมัติ"""
    if not client:
        print("  ⚠️ ไม่พบ GEMINI_API_KEY ข้ามการแปลภาษา")
        return None

    print(f"  🤖 [1/3] กำลังส่งเสียงให้ Gemini ฟังและแปลไทย...")
    
    for attempt in range(1, max_retries + 1):
        try:
            audio_file = client.files.upload(file=audio_path)
            
            prompt = """
            คำสั่งสำคัญที่สุด: ผลลัพธ์ของคุณต้องเป็น "ภาษาไทยล้วน 100%" เท่านั้น
            ข้อกำหนดที่ต้องทำตามอย่างเคร่งครัด:
            1. ฟังเสียงพูดภาษาอังกฤษทั้งหมด แล้วแปลบทพูดทุกประโยคออกมาเป็นภาษาไทยโดยตรง
            2. ห้ามพิมพ์ภาษาอังกฤษต้นฉบับออกมาเด็ดขาด
            3. ห้ามทำรูปแบบประโยคภาษาอังกฤษสลับกับภาษาไทย (Bilingual)
            4. ห้ามสรุปย่อ ให้แปลถ่ายทอดเนื้อหาคำพูดและบทวิเคราะห์ให้ครบถ้วนทุกประโยคตั้งแต่ต้นจนจบ
            5. ไม่ต้องใส่ตัวเลขเวลา (Timestamp)
            6. ให้ส่งออกเฉพาะข้อความภาษาไทยที่อ่านได้อย่างต่อเนื่อง สละสลวย เท่านั้น
            7. เอาภาษาอังกฤษออกให้หมด
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[audio_file, prompt]
            )
            
            # ลบไฟล์ออกจากระบบหลังประมวลผลเสร็จ
            client.files.delete(name=audio_file.name)
            return response.text
            
        except Exception as e:
            print(f"  ⚠️ ครั้งที่ {attempt} พบปัญหา ({e})")
            if attempt < max_retries:
                wait_sec = attempt * 5
                print(f"  ⏳ กำลังรอ {wait_sec} วินาทีก่อนลองใหม่...")
                time.sleep(wait_sec)
            else:
                print(f"  ❌ แปลไฟล์ล้มเหลวหลังจากลองครบ {max_retries} ครั้ง")
                return None

async def text_to_speech_thai(text, output_audio_path):
    """ฟังก์ชัน AI สังเคราะห์เสียงอ่านข่าวภาษาไทย"""
    print(f"  🗣️ [3/3] กำลังสร้างไฟล์เสียงอ่านข่าวไทย: {output_audio_path}...")
    try:
        # ใช้เสียงพากย์ Neural: 'th-TH-PremwadeeNeural' (เสียงผู้หญิง) หรือ 'th-TH-NiwatNeural' (เสียงผู้ชาย)
        voice = "th-TH-PremwadeeNeural"
        tts = edge_tts.Communicate(text, voice)
        await tts.save(output_audio_path)
        print(f"  ✅ บันทึกเสียงพากย์ไทยสำเร็จ!")
    except Exception as e:
        print(f"  ❌ สังเคราะห์เสียงอ่านข่าวล้มเหลว: {e}")

def process_single_file(seg_path, current_idx, total_files):
    """ประมวลผลจบครบวงจรในไฟล์เดียว: ถอดความ -> แปล -> บันทึก txt -> สร้างเสียงพากย์ไทย"""
    print(f"==================================================")
    print(f"🔄 กำลังประมวลผลไฟล์ [{current_idx}/{total_files}]: {os.path.basename(seg_path)}")
    print(f"==================================================")

    # ขั้นตอนที่ 1: ถอดความและแปลเป็นภาษาไทย
    th_text = transcribe_and_translate(seg_path)
    
    if not th_text:
        print(f"⚠️ ข้ามไฟล์ {seg_path} เนื่องจากไม่ได้รับผลลัพธ์คำแปล\n")
        return

    # ขั้นตอนที่ 2: บันทึกเป็นไฟล์ข้อความ .txt
    txt_filename = seg_path.replace(".mp3", "_แปลไทย.txt")
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(th_text)
    print(f"  💾 [2/3] บันทึกคำแปลข้อความ: {txt_filename}")

    # ขั้นตอนที่ 3: สังเคราะห์เสียงอ่านข่าวภาษาไทย .mp3
    tts_filename = seg_path.replace(".mp3", "_อ่านข่าวไทย.mp3")
    asyncio.run(text_to_speech_thai(th_text, tts_filename))

    print(f"🎉 เสร็จสิ้นขั้นตอนของไฟล์ [{current_idx}/{total_files}]\n")

# ==================== ลำดับการทำงานหลัก ====================
if __name__ == "__main__":
    th_time = datetime.now(ZoneInfo("Asia/Bangkok"))
    date_str = th_time.strftime('%Y%m%d_%H%M%S')
    main_file = f"./raw_cnbc_{date_str}.mp3"

    # 1. อัดเสียงสด
    success = record_stream(main_file, RECORD_DURATION)

    if success:
        print(f"✅ บันทึกไฟล์หลักสำเร็จ: {main_file}")
        
        # 2. ตัดแบ่งไฟล์เป็นท่อนย่อย
        segment_files = split_audio(main_file, date_str, SEGMENT_DURATION)
        total_segments = len(segment_files)
        
        # 3. วนลูปทำทีละไฟล์ (ถอดความ -> แปล -> สร้างเสียงพากย์)
        print("🌐 เริ่มต้นกระบวนการประมวลผลทีละไฟล์ตามลำดับ...")
        for idx, seg in enumerate(segment_files, start=1):
            process_single_file(seg, idx, total_segments)
            time.sleep(2) # หน่วงเวลาเล็กน้อยระหว่างไฟล์
            
        print("✨ ประมวลผลครบทุกไฟล์เรียบร้อยแล้ว!")
    else:
        print("❌ การบันทึกเสียงล้มเหลว")

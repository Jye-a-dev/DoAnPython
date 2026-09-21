import os
import asyncio
from pathlib import Path
import edge_tts
from gtts import gTTS


async def generate_audio(text: str, output_path: str, voice: str = "vi-VN-HoaiMyNeural") -> str:
    """
    Chuỗi sinh âm thanh 3 tầng:
    Tầng 1: edge-tts (chất lượng cao)
    Tầng 2: gTTS (Google Cloud fallback)
    Tầng 3: pyttsx3 (Offline cục bộ hoàn toàn)
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    clean_text = text.strip() if text and text.strip() else "Không có nội dung nhận diện."

    # Tầng 1: Edge-TTS (Chất lượng cao, Microsoft Neural Voice)
    try:
        communicate = edge_tts.Communicate(text=clean_text, voice=voice)
        await communicate.save(output_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
    except Exception:
        pass

    # Tầng 2: gTTS (Google Cloud API fallback)
    try:
        tts = gTTS(text=clean_text, lang="vi", slow=False)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, tts.save, output_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
    except Exception:
        pass

    # Tầng 3: pyttsx3 (Ngoại tuyến hoàn toàn, không phụ thuộc mạng)
    try:
        def run_offline_tts():
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 150)
            engine.save_to_file(clean_text, output_path)
            engine.runAndWait()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, run_offline_tts)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
    except Exception as ex:
        raise RuntimeError(f"Tất cả các engine TTS (kể cả pyttsx3 offline) đều thất bại: {str(ex)}")

    return output_path

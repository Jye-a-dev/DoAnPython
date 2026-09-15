import os
from pathlib import Path
import edge_tts
from gtts import gTTS


async def generate_audio(text: str, output_path: str, voice: str = "vi-VN-HoaiMyNeural") -> str:
    """
    Synthesizes speech from text asynchronously using edge-tts.
    Automatically falls back to Google TTS (gTTS) if edge-tts fails or network is restricted.
    """
    output_dir = Path(output_path).parent
    os.makedirs(output_dir, exist_ok=True)

    if not text.strip():
        text = "Không có nội dung mô tả đối tượng."

    try:
        # High quality neural voice synthesis
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(output_path)
    except Exception:
        # Resilient fallback to gTTS
        try:
            tts = gTTS(text=text, lang="vi", slow=False)
            tts.save(output_path)
        except Exception as fallback_error:
            raise RuntimeError(f"All TTS synthesis engines failed: {fallback_error}") from fallback_error

    return output_path


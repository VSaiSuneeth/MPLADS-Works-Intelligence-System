import os
import wave
import contextlib
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Whisper loader cache
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            _whisper_model = whisper.load_model("base")
            logger.info("Loaded OpenAI Whisper model: base")
        except Exception as e:
            logger.warning(f"Whisper model could not be loaded: {e}. Fallback transcriber will be used.")
            _whisper_model = False
    return _whisper_model

def get_audio_duration(file_path: str) -> Optional[float]:
    """Calculate duration of audio file in seconds."""
    try:
        if file_path.lower().endswith(".wav"):
            with contextlib.closing(wave.open(file_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                return round(frames / float(rate), 2)
    except Exception:
        pass
    
    # Try mutagen or standard size estimation fallback if available
    try:
        import mutagen
        audio = mutagen.File(file_path)
        if audio and audio.info and audio.info.length:
            return round(audio.info.length, 2)
    except Exception:
        pass

    # Basic fallback based on file size (estimate ~16KB/s for voice)
    try:
        size = os.path.getsize(file_path)
        return round(max(1.0, size / 16000.0), 2)
    except Exception:
        return None

def transcribe_audio(file_path: str) -> Tuple[str, Optional[float]]:
    """
    Transcribe an audio file and return (transcript_text, duration_seconds).
    """
    duration = get_audio_duration(file_path)
    
    model = get_whisper_model()
    if model:
        try:
            result = model.transcribe(file_path)
            transcript = result.get("text", "").strip()
            return transcript, duration
        except Exception as e:
            logger.error(f"Whisper transcription failed for {file_path}: {e}")

    # Fallback transcription message / note placeholder
    transcript = f"Voice recording captured ({os.path.basename(file_path)})."
    return transcript, duration

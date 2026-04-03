"""
Speech-to-text using OpenAI Whisper (runs fully local).
Requires: pip install openai-whisper pydub
Also requires ffmpeg on PATH.
"""
import os
import tempfile
from loguru import logger
from app.config import WHISPER_MODEL

_model = None


def _load_model():
    global _model
    if _model is None:
        import whisper
        logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
        _model = whisper.load_model(WHISPER_MODEL)
    return _model


def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio file and return the text."""
    try:
        model = _load_model()
        result = model.transcribe(file_path)
        return result.get("text", "").strip()
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return ""


def transcribe_ogg(ogg_bytes: bytes) -> str:
    """Convert Telegram voice OGG to WAV then transcribe."""
    try:
        from pydub import AudioSegment

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_file:
            ogg_file.write(ogg_bytes)
            ogg_path = ogg_file.name

        wav_path = ogg_path.replace(".ogg", ".wav")
        AudioSegment.from_ogg(ogg_path).export(wav_path, format="wav")

        text = transcribe_audio(wav_path)

        os.unlink(ogg_path)
        os.unlink(wav_path)

        return text
    except Exception as e:
        logger.error(f"OGG conversion failed: {e}")
        return ""

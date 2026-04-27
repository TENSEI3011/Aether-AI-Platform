"""
============================================================
Text-to-Speech (TTS) Module — Real gTTS implementation
============================================================
Converts text → base64-encoded MP3 audio using Google TTS.
No API key required — uses Google's free public TTS endpoint.
============================================================
"""

import io
import base64
from typing import Dict, Any

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


def synthesize_speech(text: str, lang: str = "en") -> Dict[str, Any]:
    """
    Convert text to speech using gTTS.

    Returns:
        {
            "audio_b64": str,       # base64-encoded MP3
            "duration_seconds": float,
            "stub": bool
        }
    """
    if not text or not text.strip():
        return {"audio_b64": None, "duration_seconds": 0, "stub": True}

    if not GTTS_AVAILABLE:
        return {
            "audio_b64":        None,
            "duration_seconds": len(text) * 0.06,
            "stub":             True,
            "error":            "gTTS not installed",
        }

    try:
        max_chars = 1000
        was_truncated = len(text) > max_chars
        tts  = gTTS(text=text[:max_chars], lang=lang, slow=False)
        buf  = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        audio_b64 = base64.b64encode(buf.read()).decode("utf-8")

        # Rough estimate: ~130 words/min spoken, 5 chars/word
        spoken_text = text[:max_chars]
        words = len(spoken_text.split())
        duration = round(words / 130 * 60, 1)

        return {
            "audio_b64":        audio_b64,
            "duration_seconds": duration,
            "stub":             False,
            "truncated":        was_truncated,
        }
    except Exception as exc:
        return {
            "audio_b64":        None,
            "duration_seconds": len(text) * 0.06,
            "stub":             True,
            "error":            str(exc),
        }

"""
============================================================
Text-to-Speech (TTS) Module — Converts text → audio
============================================================
STUB: In production, uses pyttsx3 or gTTS.
Currently returns a mock audio file path.
============================================================
"""

import os
from typing import Dict, Any


def synthesize_speech(text: str, output_dir: str = "../datasets") -> Dict[str, Any]:
    """
    Convert text to speech and save as an audio file.

    Parameters:
        text: The text to convert to speech
        output_dir: Directory to save the audio file

    Returns:
        {"audio_path": str, "duration_seconds": float}

    PRODUCTION IMPLEMENTATION:
        import pyttsx3
        engine = pyttsx3.init()
        output_path = os.path.join(output_dir, "response.wav")
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        return {"audio_path": output_path, "duration_seconds": len(text) * 0.06}
    """
    # Stub: return a mock response
    return {
        "audio_path": None,  # No actual file generated in stub mode
        "duration_seconds": len(text) * 0.06,
        "text": text,
        "stub": True,
    }

"""
============================================================
Voice API — Speech-to-Text and Text-to-Speech endpoints
============================================================
Endpoints:
  POST /api/voice/transcribe  → Convert audio → text
  POST /api/voice/synthesize  → Convert text → audio
============================================================
"""

import os
import tempfile

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel

from auth.jwt_handler import get_current_user
from database.models import User
from voice.stt import transcribe_audio
from voice.tts import synthesize_speech

router = APIRouter()


class TTSRequest(BaseModel):
    text: str


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
):
    """
    Receive an audio file and return the transcript.
    Accepts .wav, .webm, .mp3, .ogg formats.
    """
    # ── Save uploaded audio to temp file ──────────────────
    suffix = os.path.splitext(audio.filename or ".wav")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await audio.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = transcribe_audio(tmp_path)
        return {
            "transcript": result.get("transcript", ""),
            "confidence": result.get("confidence", 0.0),
            "language": result.get("language", "en"),
        }
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/synthesize")
def synthesize(
    req: TTSRequest,
    _current_user: User = Depends(get_current_user),
):
    """
    Convert text to speech using gTTS.
    Returns a base64-encoded MP3 that the browser can play directly.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    result = synthesize_speech(req.text)
    return {
        "text":             req.text,
        "audio_b64":        result.get("audio_b64"),          # base64 MP3 for browser playback
        "duration_seconds": result.get("duration_seconds", 0),
        "stub":             result.get("stub", True),
        "error":            result.get("error"),
    }

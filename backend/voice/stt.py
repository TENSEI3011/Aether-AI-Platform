"""
============================================================
Speech-to-Text (STT) Module — Converts audio → text
============================================================
Uses the SpeechRecognition library with Google's free
web API for real audio transcription.

Fallback: if SpeechRecognition isn't installed, returns
a helpful error message.
============================================================
"""

import os
from typing import Dict, Any


def transcribe_audio(audio_filepath: str) -> Dict[str, Any]:
    """
    Transcribe an audio file to text using SpeechRecognition.

    Parameters:
        audio_filepath: Path to the audio file (.wav, .webm, .mp3)

    Returns:
        {"transcript": str, "confidence": float, "language": str}
    """
    if not os.path.exists(audio_filepath):
        return {
            "transcript": "",
            "confidence": 0.0,
            "language": "en",
            "error": "Audio file not found",
        }

    # ── Try real transcription with SpeechRecognition ─────
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        # SpeechRecognition needs WAV format. For webm/other, convert first.
        file_ext = os.path.splitext(audio_filepath)[1].lower()

        if file_ext in (".wav",):
            # Direct WAV support
            with sr.AudioFile(audio_filepath) as source:
                audio = recognizer.record(source)
        else:
            # For non-WAV (webm, mp3, ogg), try pydub conversion
            try:
                from pydub import AudioSegment
                import tempfile

                if file_ext == ".webm":
                    audio_segment = AudioSegment.from_file(audio_filepath, format="webm")
                elif file_ext == ".mp3":
                    audio_segment = AudioSegment.from_file(audio_filepath, format="mp3")
                elif file_ext == ".ogg":
                    audio_segment = AudioSegment.from_file(audio_filepath, format="ogg")
                else:
                    audio_segment = AudioSegment.from_file(audio_filepath)

                # Export as WAV to a temp file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    wav_path = tmp.name
                    audio_segment.export(wav_path, format="wav")

                with sr.AudioFile(wav_path) as source:
                    audio = recognizer.record(source)

                os.remove(wav_path)

            except ImportError:
                return {
                    "transcript": "",
                    "confidence": 0.0,
                    "language": "en",
                    "error": "pydub required for non-WAV audio. Install: pip install pydub",
                }
            except Exception as e:
                return {
                    "transcript": "",
                    "confidence": 0.0,
                    "language": "en",
                    "error": f"Audio conversion failed: {str(e)}",
                }

        # ── Recognize with Google (free, no API key) ──────
        try:
            transcript = recognizer.recognize_google(audio)
            return {
                "transcript": transcript,
                "confidence": 0.90,
                "language": "en",
            }
        except sr.UnknownValueError:
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": "en",
                "error": "Could not understand audio. Try speaking more clearly.",
            }
        except sr.RequestError as e:
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": "en",
                "error": f"Speech recognition service error: {str(e)}",
            }

    except ImportError:
        # SpeechRecognition not installed — return helpful message
        return {
            "transcript": "",
            "confidence": 0.0,
            "language": "en",
            "error": "SpeechRecognition not installed. Install: pip install SpeechRecognition",
        }

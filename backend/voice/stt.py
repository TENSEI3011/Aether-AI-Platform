"""
============================================================
Speech-to-Text (STT) Module — Converts audio → text
============================================================
PRIMARY:  OpenAI Whisper (local DL model, no API key needed)
          DL Concept: Transformer Seq2Seq Encoder-Decoder model
          trained on 680k hours of audio. Much more accurate
          than Google's STT, especially for:
            - Technical terms (PM2.5, AQI, regression)
            - Indian English / non-native accents
            - Domain-specific vocabulary
          Models: tiny (39MB), base (74MB), small (244MB)

FALLBACK: Google SpeechRecognition (if Whisper not installed)
FALLBACK2: Error with install instructions

Install Whisper: pip install openai-whisper
============================================================
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def transcribe_audio(audio_filepath: str) -> Dict[str, Any]:
    """
    Transcribe an audio file to text.

    Tries in order:
    1. OpenAI Whisper (local DL model — best accuracy)
    2. Google SpeechRecognition (web API — fallback)

    Parameters:
        audio_filepath: Path to the audio file (.wav, .webm, .mp3, .ogg)

    Returns:
        {"transcript": str, "confidence": float, "language": str, "model": str}
    """
    if not os.path.exists(audio_filepath):
        return {
            "transcript": "",
            "confidence": 0.0,
            "language": "en",
            "model": "none",
            "error": "Audio file not found",
        }

    # ── Try Whisper first (best accuracy) ────────────────
    result = _transcribe_whisper(audio_filepath)
    if result.get("transcript"):
        return result

    # ── Fallback: Google SpeechRecognition ───────────────
    if "not_installed" not in result.get("error", ""):
        # Whisper was installed but failed for another reason — don't fallback
        return result

    return _transcribe_google(audio_filepath)


# ─────────────────────────────────────────────────────────
# Whisper (Primary — DL Transformer)
# ─────────────────────────────────────────────────────────

# Singleton: load Whisper model once and reuse
_whisper_model = None
_whisper_model_size = "base"  # Options: tiny, base, small, medium, large


def _get_whisper_model():
    """Lazy-load the Whisper model (only once per process)."""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            logger.info("STT-Whisper: Loading '%s' model...", _whisper_model_size)
            _whisper_model = whisper.load_model(_whisper_model_size)
            logger.info("STT-Whisper: Model loaded successfully")
        except ImportError:
            return None, "not_installed"
        except Exception as e:
            return None, str(e)
    return _whisper_model, None


def _transcribe_whisper(audio_filepath: str) -> Dict[str, Any]:
    """
    Use OpenAI Whisper for transcription.

    DL Concept: Whisper is a Transformer-based encoder-decoder model.
    The audio is converted to a mel spectrogram, encoded by the
    encoder, then decoded into text tokens by the decoder.
    """
    model, error = _get_whisper_model()
    if model is None:
        return {
            "transcript": "",
            "confidence": 0.0,
            "language": "en",
            "model": "whisper",
            "error": f"not_installed: {error}. Run: pip install openai-whisper",
        }

    try:
        import whisper

        # Whisper handles .wav, .mp3, .ogg, .webm natively
        result = model.transcribe(
            audio_filepath,
            language="en",       # Force English for speed; remove for auto-detect
            fp16=False,          # Use float32 (works on CPU without CUDA)
            temperature=0.0,     # Deterministic output
            best_of=1,
            verbose=False,
        )

        transcript = result.get("text", "").strip()
        detected_lang = result.get("language", "en")

        # Whisper doesn't return a confidence score directly;
        # we use a fixed high score as it's the superior model
        return {
            "transcript": transcript,
            "confidence": 0.95,
            "language": detected_lang,
            "model": f"whisper-{_whisper_model_size}",
        }

    except Exception as e:
        return {
            "transcript": "",
            "confidence": 0.0,
            "language": "en",
            "model": "whisper",
            "error": f"Whisper transcription failed: {str(e)}",
        }


# ─────────────────────────────────────────────────────────
# Google SpeechRecognition (Fallback)
# ─────────────────────────────────────────────────────────

def _transcribe_google(audio_filepath: str) -> Dict[str, Any]:
    """
    Fallback: Google Web Speech API via SpeechRecognition library.
    Lower accuracy than Whisper, especially for technical terms.
    """
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        file_ext = os.path.splitext(audio_filepath)[1].lower()

        if file_ext in (".wav",):
            with sr.AudioFile(audio_filepath) as source:
                audio = recognizer.record(source)
        else:
            # Convert non-WAV via pydub
            try:
                from pydub import AudioSegment
                import tempfile

                format_map = {".webm": "webm", ".mp3": "mp3", ".ogg": "ogg"}
                fmt = format_map.get(file_ext, None)
                audio_segment = (
                    AudioSegment.from_file(audio_filepath, format=fmt)
                    if fmt
                    else AudioSegment.from_file(audio_filepath)
                )
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
                    "model": "google-stt",
                    "error": "pydub required for non-WAV. Run: pip install pydub",
                }
            except Exception as e:
                return {
                    "transcript": "",
                    "confidence": 0.0,
                    "language": "en",
                    "model": "google-stt",
                    "error": f"Audio conversion failed: {str(e)}",
                }

        try:
            transcript = recognizer.recognize_google(audio)
            return {
                "transcript": transcript,
                "confidence": 0.80,
                "language": "en",
                "model": "google-stt",
            }
        except sr.UnknownValueError:
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": "en",
                "model": "google-stt",
                "error": "Could not understand audio. Try speaking more clearly.",
            }
        except sr.RequestError as e:
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": "en",
                "model": "google-stt",
                "error": f"Speech recognition service error: {str(e)}",
            }

    except ImportError:
        return {
            "transcript": "",
            "confidence": 0.0,
            "language": "en",
            "model": "none",
            "error": (
                "No STT library installed. "
                "Install Whisper: pip install openai-whisper  (recommended) "
                "OR: pip install SpeechRecognition"
            ),
        }

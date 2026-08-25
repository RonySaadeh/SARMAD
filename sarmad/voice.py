"""Speech I/O: microphone recording, local speech-to-text, free cloud text-to-speech.

Transcription runs fully locally via faster-whisper (no API key, uses your CPU).
Playback uses edge-tts, a free wrapper around Microsoft Edge's TTS voices (no
API key required either) plus `playsound` since edge-tts outputs mp3.
"""

import asyncio
import io
import re
import tempfile
import wave
from pathlib import Path

import edge_tts
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from playsound import playsound

from sarmad import config

SAMPLE_RATE = 16000
CHANNELS = 1

_ARABIC_SCRIPT = re.compile(r"[؀-ۿ]")

_whisper_model: WhisperModel | None = None


def _get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        # Downloads the model from Hugging Face on first run, then caches it locally.
        _whisper_model = WhisperModel(config.WHISPER_MODEL_SIZE, device=config.WHISPER_DEVICE, compute_type="int8")
    return _whisper_model


def record_until_silence(max_seconds: float = 25.0, silence_seconds: float = 0.9, silence_threshold: float = 0.01) -> bytes:
    """Record from the default microphone until the user stops talking, and return WAV bytes."""
    block_seconds = 0.25
    block_frames = int(SAMPLE_RATE * block_seconds)
    max_blocks = int(max_seconds / block_seconds)
    silence_blocks_needed = int(silence_seconds / block_seconds)

    frames = []
    silent_run = 0
    heard_speech = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16") as stream:
        for _ in range(max_blocks):
            block, _ = stream.read(block_frames)
            frames.append(block.copy())

            volume = np.abs(block.astype(np.float32) / 32768.0).mean()
            if volume > silence_threshold:
                heard_speech = True
                silent_run = 0
            elif heard_speech:
                silent_run += 1
                if silent_run >= silence_blocks_needed:
                    break

    audio = np.concatenate(frames, axis=0) if frames else np.zeros((0, CHANNELS), dtype=np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()


def transcribe(wav_bytes: bytes) -> str:
    """Transcribe recorded audio locally with faster-whisper."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        temp_path = Path(f.name)

    try:
        segments, _ = _get_whisper_model().transcribe(str(temp_path))
        return " ".join(segment.text.strip() for segment in segments).strip()
    finally:
        temp_path.unlink(missing_ok=True)


def speak(text: str) -> None:
    """Synthesize speech with edge-tts (free, no key) and play it back.

    Picks an Arabic voice automatically when the reply contains Arabic
    script, so bilingual conversations sound right in either language.
    """
    if not text:
        return

    voice = config.ARABIC_TTS_VOICE if _ARABIC_SCRIPT.search(text) else config.EDGE_TTS_VOICE

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_path = Path(f.name)

    try:
        asyncio.run(edge_tts.Communicate(text, voice).save(str(temp_path)))
        playsound(str(temp_path))
    finally:
        temp_path.unlink(missing_ok=True)

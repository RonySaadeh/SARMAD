"""Speech I/O: microphone recording, cloud speech-to-text, cloud text-to-speech playback.

Playback uses the Windows-native `winsound` module, so this module is Windows-only
(matching the rest of SARMAD v0).
"""

import io
import tempfile
import wave
import winsound
from pathlib import Path

import numpy as np
import sounddevice as sd
from openai import OpenAI

from sarmad import config

SAMPLE_RATE = 16000
CHANNELS = 1


def _client() -> OpenAI:
    return OpenAI(api_key=config.OPENAI_API_KEY)


def record_until_silence(max_seconds: float = 12.0, silence_seconds: float = 1.5, silence_threshold: float = 0.01) -> bytes:
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
    """Send recorded audio to OpenAI Whisper and return the transcript text."""
    buf = io.BytesIO(wav_bytes)
    buf.name = "speech.wav"
    result = _client().audio.transcriptions.create(model="whisper-1", file=buf)
    return result.text.strip()


def speak(text: str) -> None:
    """Synthesize speech with OpenAI TTS and play it back."""
    if not text:
        return
    response = _client().audio.speech.create(
        model="tts-1",
        voice=config.OPENAI_TTS_VOICE,
        input=text,
        response_format="wav",
    )
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(response.read())
        temp_path = Path(f.name)

    try:
        winsound.PlaySound(str(temp_path), winsound.SND_FILENAME)
    finally:
        temp_path.unlink(missing_ok=True)

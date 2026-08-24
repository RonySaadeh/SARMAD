"""Always-on, local, offline wake-phrase detection using Vosk.

Runs fully offline so it's cheap to leave listening 24/7 (no API calls until the
wake phrase actually fires). Restricting Vosk to a small grammar of just the
wake-phrase vocabulary keeps accuracy high on limited CPU.
"""

import json
import queue

import sounddevice as sd
from vosk import KaldiRecognizer, Model

from sarmad import config

SAMPLE_RATE = 16000


def _grammar_words() -> list[str]:
    words: set[str] = set()
    for phrase in config.WAKE_PHRASES:
        for word in phrase.replace("'", "").split():
            words.add(word)
    return sorted(words)


def listen_for_wake_word() -> None:
    """Blocks until one of config.WAKE_PHRASES is heard, then returns."""
    model = Model(config.VOSK_MODEL_PATH)
    grammar = json.dumps(_grammar_words() + ["[unk]"])
    recognizer = KaldiRecognizer(model, SAMPLE_RATE, grammar)

    audio_queue: queue.Queue[bytes] = queue.Queue()

    def _callback(indata, frames, time_info, status):
        audio_queue.put(bytes(indata))

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=_callback,
    ):
        while True:
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                text = json.loads(recognizer.Result()).get("text", "")
            else:
                text = json.loads(recognizer.PartialResult()).get("partial", "")

            if not text:
                continue

            for phrase in config.WAKE_PHRASES:
                phrase_words = phrase.replace("'", "").split()
                if all(word in text for word in phrase_words):
                    return

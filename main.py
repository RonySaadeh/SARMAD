"""SARMAD v0 entry point: wake word -> listen -> think -> speak, forever."""

from sarmad import config, voice, wake_word
from sarmad.brain import process


def run() -> None:
    config.require_keys()
    print("SARMAD is running. Say 'SARMAD, Daddy's home' to wake him up.")

    while True:
        wake_word.listen_for_wake_word()
        print("[woken up]")

        voice.speak("Yes? What should we do?")
        wav_bytes = voice.record_until_silence()
        user_text = voice.transcribe(wav_bytes)

        if not user_text:
            voice.speak("I didn't catch that. Say my name again when you need me.")
            continue

        print(f"You: {user_text}")
        reply = process(user_text)
        print(f"SARMAD: {reply}")
        voice.speak(reply)


if __name__ == "__main__":
    run()

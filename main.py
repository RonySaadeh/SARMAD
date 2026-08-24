"""SARMAD v0 entry point: wake word -> listen -> think -> speak, forever."""

from sarmad import config, voice, wake_word
from sarmad.brain import process


def run(hud=None) -> None:
    config.require_keys()
    print("SARMAD is running. Say 'SARMAD, Daddy's home' to wake him up.")

    while True:
        if hud:
            hud.set_state("idle")
        wake_word.listen_for_wake_word()
        print("[woken up]")

        if hud:
            hud.set_state("speaking")
        voice.speak("Yes? What should we do?")

        # Stay awake for follow-ups after each reply instead of requiring the
        # wake word again - only fall back to sleep once the user goes quiet.
        first_turn = True
        while True:
            if hud:
                hud.set_state("listening")
            wav_bytes = voice.record_until_silence()
            user_text = voice.transcribe(wav_bytes)

            if not user_text:
                if first_turn:
                    if hud:
                        hud.set_state("speaking")
                    voice.speak("I didn't catch that. Say my name again when you need me.")
                break

            print(f"You: {user_text}")
            if hud:
                hud.set_state("thinking")
            reply = process(user_text)
            print(f"SARMAD: {reply}")

            if hud:
                hud.set_transcript(user_text, reply)
                hud.set_state("speaking")
            voice.speak(reply)
            first_turn = False


if __name__ == "__main__":
    if config.ENABLE_HUD:
        from sarmad import hud as hud_module

        hud_module.start(run)
    else:
        run()

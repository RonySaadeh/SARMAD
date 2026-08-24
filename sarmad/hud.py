"""JARVIS-style visual HUD: a small always-on-top glowing status widget.

Runs as a native WebView2 window (sarmad/assets/hud.html) with no browser
chrome. pywebview requires the GUI loop to own the main thread, so the voice
loop is handed off to run in a background thread while webview.start() blocks
here; state changes are pushed into the page via evaluate_js rather than the
page polling Python.
"""

from pathlib import Path
from typing import Callable

import webview

_HUD_PATH = Path(__file__).parent / "assets" / "hud.html"

_window: webview.Window | None = None


class Hud:
    def set_state(self, state: str) -> None:
        if _window is not None:
            _window.evaluate_js(f"setState({state!r})")

    def set_transcript(self, user_text: str, reply_text: str) -> None:
        if _window is not None:
            _window.evaluate_js(f"setTranscript({user_text!r}, {reply_text!r})")


def start(voice_loop: Callable[[Hud], None]) -> None:
    """Open the HUD window and run voice_loop(hud) in a background thread."""
    global _window
    _window = webview.create_window(
        "SARMAD",
        url=str(_HUD_PATH),
        width=340,
        height=380,
        resizable=False,
        on_top=True,
        frameless=True,
        easy_drag=True,
        background_color="#050b0d",
    )
    webview.start(voice_loop, Hud(), gui="edgechromium")

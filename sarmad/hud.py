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

_IDLE_SIZE = (380, 460)
_CODING_SIZE = (420, 720)

_window: webview.Window | None = None
_instance: "Hud | None" = None


class Hud:
    def __init__(self) -> None:
        global _instance
        _instance = self

    def set_state(self, state: str) -> None:
        if _window is None:
            return
        _window.evaluate_js(f"setState({state!r})")
        _window.resize(*(_CODING_SIZE if state == "coding" else _IDLE_SIZE))

    def set_transcript(self, user_text: str, reply_text: str) -> None:
        if _window is not None:
            _window.evaluate_js(f"setTranscript({user_text!r}, {reply_text!r})")

    def clear_log(self) -> None:
        if _window is not None:
            _window.evaluate_js("clearLog()")

    def append_log(self, line: str, is_task: bool = False) -> None:
        if _window is not None:
            _window.evaluate_js(f"appendLog({line!r}, {'true' if is_task else 'false'})")


def current() -> "Hud | None":
    """The running HUD instance, if any tool needs to push updates into it directly."""
    return _instance


def start(voice_loop: Callable[[Hud], None]) -> None:
    """Open the HUD window and run voice_loop(hud) in a background thread."""
    global _window
    _window = webview.create_window(
        "SARMAD",
        url=str(_HUD_PATH),
        width=_IDLE_SIZE[0],
        height=_IDLE_SIZE[1],
        resizable=False,
        on_top=True,
        frameless=True,
        easy_drag=True,
        background_color="#050b0d",
    )
    webview.start(voice_loop, Hud(), gui="edgechromium")

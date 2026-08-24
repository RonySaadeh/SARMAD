"""Webcam capture for visual inspection, gated by an explicit tool call.

The camera is only opened in direct response to the model calling this tool
(which it's instructed to do only when the user explicitly asks). A single
frame is captured, encoded, and handed to Claude — nothing is written to disk.
"""

import base64

import cv2

from sarmad import config


def capture_and_look() -> dict:
    cam = cv2.VideoCapture(config.CAMERA_INDEX)
    try:
        if not cam.isOpened():
            return {
                "ok": False,
                "error": f"Could not open camera index {config.CAMERA_INDEX}. Is it in use by another app?",
            }

        # Let the camera settle its exposure/white balance before the real capture.
        for _ in range(5):
            cam.read()
        ok, frame = cam.read()
        if not ok:
            return {"ok": False, "error": "Failed to capture a frame from the camera."}

        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            return {"ok": False, "error": "Failed to encode the captured frame."}

        return {
            "ok": True,
            "image_b64": base64.b64encode(buffer.tobytes()).decode("ascii"),
            "media_type": "image/jpeg",
        }
    finally:
        cam.release()

"""
Eddoboozi — page-to-voice prototype backend.

Two endpoints:
  POST /ocr   -> {text}                 (pytesseract, fully local, free)
  POST /tts   -> audio file              (Sunbird AI for Luganda, gTTS for English)
"""

import os
import platform
import uuid

import requests
import pytesseract
from PIL import Image
from flask import Flask, request, jsonify, send_file, render_template

app = Flask(__name__)

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SUNBIRD_TOKEN = os.environ.get("SUNBIRD_TOKEN", "")
# Sunbird's TTS moved to a unified endpoint — /tasks/tts, /tasks/modal/tts,
# /tasks/runpod/tts are all deprecated in favour of this one.
SUNBIRD_TTS_URL = "https://api.sunbird.ai/tasks/audio/speech"

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "generated_audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ocr", methods=["POST"])
def ocr():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files["image"]
    try:
        image = Image.open(image_file.stream)
        text = pytesseract.image_to_string(image)
        text = text.strip()
    except Exception as e:
        return jsonify({"error": f"Could not read the image: {e}"}), 500

    if not text:
        return jsonify({"error": "No readable text found in that photo. Try a clearer, flatter shot."}), 422

    return jsonify({"text": text})


@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    language = data.get("language", "eng")

    if not text:
        return jsonify({"error": "No text to read aloud"}), 400

    base_name = uuid.uuid4().hex

    try:
        if language == "lug":
            if not SUNBIRD_TOKEN:
                return jsonify({"error": "SUNBIRD_TOKEN is not set on the server"}), 500

            # Step 1: ask Sunbird to synthesize — this returns a signed URL to
            # the audio, not the audio bytes themselves.
            resp = requests.post(
                SUNBIRD_TTS_URL,
                headers={
                    "Authorization": f"Bearer {SUNBIRD_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={"text": text, "language": "lug"},
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
            audio_url = result.get("audio_url")
            if not audio_url:
                return jsonify({"error": "Sunbird AI did not return an audio URL"}), 502

            # Step 2: fetch the actual audio bytes from that signed URL.
            audio_resp = requests.get(audio_url, timeout=60)
            audio_resp.raise_for_status()
            content_type = audio_resp.headers.get("Content-Type", "")
            ext = ".wav" if "wav" in content_type else ".mp3"
            filename = base_name + ext
            filepath = os.path.join(AUDIO_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(audio_resp.content)
        else:
            # English: gTTS is a free, solved problem — not our differentiator, so keep it simple.
            from gtts import gTTS
            filename = base_name + ".mp3"
            filepath = os.path.join(AUDIO_DIR, filename)
            gTTS(text=text, lang="en").save(filepath)
    except Exception as e:
        return jsonify({"error": f"Could not generate audio: {e}"}), 502

    return jsonify({"audio_url": f"/audio/{filename}"})


@app.route("/audio/<filename>")
def get_audio(filename):
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Not found"}), 404
    return send_file(filepath)  # let Flask infer the mimetype from the extension


if __name__ == "__main__":
    app.run(debug=True, port=5000)
"""
Eddoboozi — page-to-voice prototype backend.

Two endpoints:
  POST /ocr   -> {text}                 (pytesseract, fully local, free)
  POST /tts   -> audio file              (Sunbird AI for Luganda, gTTS for English)

Setup:
  1. pip install -r requirements.txt
  2. Register at https://api.sunbird.ai/register, get a bearer token
  3. export SUNBIRD_TOKEN="your_token_here"
  4. python app.py
  5. open http://localhost:5000
"""

import os
import io
import uuid

import requests
import pytesseract 
import platform
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import Image
from flask import Flask, request, jsonify, send_file, render_template

app = Flask(__name__)

SUNBIRD_TOKEN = os.environ.get("SUNBIRD_TOKEN", "")
SUNBIRD_TTS_URL = "https://api.sunbird.ai/tasks/tts"
LUGANDA_SPEAKER_ID = 248  # "Luganda / Female / Natural, conversational" per Sunbird docs

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

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    try:
        if language == "lug":
            if not SUNBIRD_TOKEN:
                return jsonify({"error": "SUNBIRD_TOKEN is not set on the server"}), 500
            resp = requests.post(
                SUNBIRD_TTS_URL,
                headers={
                    "Authorization": f"Bearer {SUNBIRD_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={"text": text, "speaker_id": LUGANDA_SPEAKER_ID},
                timeout=30,
            )
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(resp.content)
        else:
            # English: gTTS is a free, solved problem — not our differentiator, so keep it simple.
            from gtts import gTTS
            gTTS(text=text, lang="en").save(filepath)
    except Exception as e:
        return jsonify({"error": f"Could not generate audio: {e}"}), 502

    return jsonify({"audio_url": f"/audio/{filename}"})


@app.route("/audio/<filename>")
def get_audio(filename):
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Not found"}), 404
    return send_file(filepath, mimetype="audio/mpeg")


if __name__ == "__main__":
    app.run(debug=True, port=5000)

from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "recordings"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.get("/<path:filename>")
def static_files(filename):
    if filename not in ("app.js", "style.css"):
        return jsonify({"error": "Not found"}), 404

    return send_from_directory(BASE_DIR, filename)

@app.post("/voice")
def receive_audio():
    audio = request.files.get("audio")

    if audio is None:
        return jsonify({"error": "No audio received"}), 400

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.webm"
    audio.save(UPLOAD_DIR / filename)

    print(f"Saved audio: {filename}")

    return jsonify({"success": True, "filename": filename})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)

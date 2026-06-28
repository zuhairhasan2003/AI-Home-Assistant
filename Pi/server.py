from flask import Flask, request
import whisper
import tempfile
import os
import json
import socket

app = Flask(__name__)

# ----------------------------
# LOAD WHISPER ONCE
# ----------------------------
model = whisper.load_model("base")


# ----------------------------
# WHISPER TRANSCRIPTION
# ----------------------------
def transcribe_audio(file_path: str) -> str:
    result = model.transcribe(file_path)
    return result["text"].strip()


# ----------------------------
# RULE-BASED INTENT PARSER
# ----------------------------
def parse_intent(transcript: str):
    text = transcript.lower().strip()

    intent = {
        "user_input": transcript,
        "operation": "unknown",
        "service": "unknown",
        "parameter": None
    }

    # ----------------------------
    # SERVICE DETECTION
    # ----------------------------
    music_keywords = ["play", "song", "music", "track", "album", "listen", "put on", "play some", "listen to"]
    light_keywords = ["light", "lights", "lamp", "bulb"]

    if any(word in text for word in music_keywords):
        intent["service"] = "music"
    elif any(word in text for word in light_keywords):
        intent["service"] = "lights"

    # ----------------------------
    # MUSIC OPERATIONS
    # ----------------------------
    if intent["service"] == "music":

        if any(word in text for word in ["stop", "end", "shut"]):
            intent["operation"] = "stop"

        elif any(word in text for word in ["play", "start"]):
            intent["operation"] = "play"

    # ----------------------------
    # LIGHT OPERATIONS
    # ----------------------------
    elif intent["service"] == "lights":

        if any(word in text for word in ["onn", "on", "turn on", "switch on"]):
            intent["operation"] = "turn_on"

        elif any(word in text for word in ["of", "off", "turn off", "switch off"]):
            intent["operation"] = "turn_off"

    return intent


# ----------------------------
# SEND TO C CONTROLLER
# ----------------------------
def send_to_controller(data: dict):

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 8080))

        message = json.dumps(data) + "\n"
        s.sendall(message.encode())
        s.close()

        print("\n===== SENT TO CONTROLLER =====")
        print(message)
        print("=============================\n")

    except Exception as e:
        print("Failed to send to controller:", e)


# ----------------------------
# MAIN ENDPOINT
# ----------------------------
@app.route("/voice", methods=["POST"])
def voice():

    audio = request.files["audio"]

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        audio.save(tmp.name)

        # STEP 1: Whisper
        transcript = transcribe_audio(tmp.name)
        print("\nTranscript:", transcript)

        # STEP 2: Rule-based intent parser
        intent = parse_intent(transcript)

        print("\n===== INTENT =====")
        print(intent)
        print("==================\n")

        # STEP 3: Send to controller
        send_to_controller(intent)

    os.remove(tmp.name)

    return intent


# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
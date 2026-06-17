from flask import Flask, request
import whisper
import tempfile
import os
import json
import ollama
import socket
import re

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
# OLLAMA INTENT PARSER
# ----------------------------
def parse_intent(transcript: str):

    prompt = f"""
You are a strict JSON generator for a home assistant system.

RULES:
- Output ONLY valid JSON
- No markdown
- No explanations
- No extra text

FORMAT:
{{
  "user_input": "{transcript}",
  "operation": "<play | pause | stop | next | turn_on | turn_off | volume | unknown>",
  "service": "<music | lights | tv | system | unknown>"
}}

INPUT:
{transcript}
"""

    response = ollama.chat(
        model="gemma2:2b",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw = response["message"]["content"].strip()

    # ----------------------------
    # DEBUG OUTPUT
    # ----------------------------
    print("\n===== RAW OLLAMA OUTPUT =====")
    print(raw)
    print("============================\n")

    # ----------------------------
    # JSON PARSING
    # ----------------------------
    try:
        parsed = json.loads(raw)

        print("\n===== PARSED JSON =====")
        print(parsed)
        print("======================\n")

        return parsed

    except json.JSONDecodeError:
        # fallback: extract JSON from messy output
        match = re.search(r"\{.*\}", raw, re.S)
        if match:
            try:
                parsed = json.loads(match.group())
                print("\n===== FIXED JSON =====")
                print(parsed)
                print("======================\n")
                return parsed
            except:
                pass

    # final fallback
    return {
        "user_input": transcript,
        "operation": "unknown",
        "service": "unknown"
    }


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

        # STEP 2: Ollama → JSON intent
        intent = parse_intent(transcript)

        # STEP 3: Send to C controller
        send_to_controller(intent)

    os.remove(tmp.name)

    # return result to browser
    return intent


# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

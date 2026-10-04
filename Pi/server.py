from flask import Flask, request
import whisper
import tempfile
import os
import json
import socket
import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer

app = Flask(__name__)

model = whisper.load_model("base")

onnx_model = ort.InferenceSession("minilm-onnx/model.onnx")
# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    "sentence-transformers/all-MiniLM-L6-v2"
)

def embed(text):
    # Convert text into tokens
    inputs = tokenizer(
        text,
        return_tensors="np",
        padding=True,
        truncation=True
    )

    # ONNX model only expects these two inputs
    inputs = {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"]
    }

    # Run ONNX model
    outputs = onnx_model.run(None, inputs)

    # Token embeddings
    embeddings = outputs[0]

    # Mean pooling
    mask = inputs["attention_mask"][..., None]

    embedding = (embeddings * mask).sum(axis=1) / mask.sum(axis=1)

    # Normalize
    embedding /= np.linalg.norm(
        embedding,
        axis=1,
        keepdims=True
    )

    return embedding[0]

# Things we want to classify against
service_descriptions = {
    "lights": """
    This is a smart home lighting command.

    The user wants to control a light, lamp, bulb, or room lighting.
    The user may want to turn a light on or off.
    The user may want to switch the lights on or off.
    The user may want to control the lighting in a room.
    The user may be talking about the bedroom light, living room light,
    kitchen light, hallway light, or another light in the home.

    Examples:
    Turn on the lights.
    Turn off the lights.
    Switch the lights on.
    Switch the lights off.
    Turn the bedroom light on.
    Turn the living room lamp off.
    Can you turn the light on?
    Can you turn the light off?
    Please switch the lamp on.
    Please switch the lamp off.
    The room is too dark.
    Make the room brighter.
    I need some light in here.
    Turn on the lamp.
    Turn off the lamp.
    Switch on the bedroom lights.
    Switch off the living room lights.
    """,

    "music": """
    This is a smart home music player command.

    The user wants to control music, songs, tracks, albums, audio,
    or music playback.
    The user may want to start playing music.
    The user may want to stop or pause music.
    The user may want to listen to a song or start the music player.

    Examples:
    Play some music.
    Play a song.
    Start the music.
    Start playing music.
    Stop the music.
    Stop playing.
    Please stop the music.
    Can you please stop?
    Pause the music.
    Pause what is playing.
    Stop the song.
    End the music.
    Put some music on.
    I'd like to listen to some music.
    Play a track.
    Play an album.
    I want to listen to music.
    Turn the music on.
    Turn the music off.
    """
}

service_choices = list(service_descriptions.keys())

# Create embeddings for our choices description
choice_embeddings = np.array([
    embed(description)
    for description in service_descriptions.values()
])

def transcribe_audio(file_path: str) -> str:
    result = model.transcribe(file_path)
    return result["text"].strip()

def parse_operation_by_service(transcript: str, service: str):
    text = transcript.lower().strip()

    intent = {
        "user_input": transcript,
        "operation": "unknown",
        "service": service,
        "parameter": None
    }

    if intent["service"] == service_choices[1]:
        if any(word in text for word in ["stop", "end", "shut"]):
            intent["operation"] = "stop"
        elif any(word in text for word in ["play", "start", "put on", "put onn"]):
            intent["operation"] = "play"

    elif intent["service"] == service_choices[0]:
        if any(word in text for word in ["onn", "on", "turn on", "switch on"]):
            intent["operation"] = "turn_on"
        elif any(word in text for word in ["of", "off", "turn off", "switch off"]):
            intent["operation"] = "turn_off"

    return intent

def get_service_via_on_device_model(transcript: str):
    # Embed user's sentence
    query = embed(transcript)

    # Calculate similarity bw user input(vector format) and avaliable choices
    scores = choice_embeddings @ query

    # Find best match
    best = np.argmax(scores)

    return service_choices[best] # returns service name e.g. "music", "lights" etc...

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

@app.route("/voice", methods=["POST"])
def voice():
    audio = request.files["audio"]

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        audio.save(tmp.name)

        # STEP 1: Whisper
        transcript = transcribe_audio(tmp.name)
        print("\nTranscript:", transcript)

        # STEP 2: intent parser
        service = get_service_via_on_device_model(transcript)
        intent = parse_operation_by_service(transcript, service)

        print("\n===== INTENT =====")
        if intent["operation"] != "unknown":
            # STEP 3: Send to controller
            send_to_controller(intent)
        else:
            print("WARNING : Unable to parse intent", flush=True)
            print(intent, flush=True)
            return {
                "error": "Unable to parse intent"
            }, 400

        print("==================\n")

    os.remove(tmp.name)

    return intent

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

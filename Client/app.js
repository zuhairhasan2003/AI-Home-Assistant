let recorder;
let chunks = [];
let isRecording = false;

const micButton = document.getElementById("micButton");

// Toggle on click
micButton.onclick = async () => {

    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
};

async function startRecording() {

    const stream = await navigator.mediaDevices.getUserMedia({
        audio: true
    });

    recorder = new MediaRecorder(stream);
    chunks = [];

    recorder.ondataavailable = e => {
        chunks.push(e.data);
    };

    recorder.start();
    isRecording = true;

    micButton.classList.add("recording");
}

function stopRecording() {

    recorder.stop();
    isRecording = false;

    micButton.classList.remove("recording");

    recorder.onstop = async () => {

        const blob = new Blob(chunks, { type: "audio/webm" });

        const formData = new FormData();
        formData.append("audio", blob, "audio.webm");

        try {
            const response = await fetch(`${window.location.origin}/voice`,
                {
                    method: "POST",
                    body: formData
                }
            );

            console.log("Upload status:", response.status);
            console.log("Upload response:", await response.text());
        } catch (err) {
            console.error("Request failed:", err);
    }
    };
}
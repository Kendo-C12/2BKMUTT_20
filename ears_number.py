import time
import keyboard
import json

import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from scipy.io import wavfile

import io

from vosk import Model, KaldiRecognizer

model = None

def init_ears():
    global model
    print("Loading Vosk model...")
    model = Model("vosk-model-small-en-us-0.15")  # 🔥 change path if needed
    print("Model loaded.")

def record_audio(fs=16000):
    print("Press 'y' to start recording...")
    while True:
        if keyboard.is_pressed('y'):
            break

    print("Recording... Press 'n' to stop.")
    recording = []

    def callback(indata, frames, time, status):
        if status:
            print(status)
        recording.append(indata.copy())

    with sd.InputStream(samplerate=fs, channels=1, callback=callback):
        while True:
            if keyboard.is_pressed('n'):
                break

    audio_data = np.concatenate(recording, axis=0)

    audio_int16 = (audio_data * 32767).astype(np.int16)

    bytes_wav = io.BytesIO()
    write(bytes_wav, fs, audio_int16)
    bytes_wav.seek(0)

    print("Recording stopped.")
    return bytes_wav

def listen(bytes_wav):
    global model

    print("Processing audio with Vosk...")

    bytes_wav.seek(0)
    rate, audio = wavfile.read(bytes_wav)

    if len(audio.shape) > 1:
        audio = audio.squeeze()

    # 🔥 Grammar محدود to numbers 0–10
    grammar = '["zero","one","two","three","four","five","six","seven","eight","nine","ten"]'

    rec = KaldiRecognizer(model, rate, grammar)

    rec.AcceptWaveform(audio.tobytes())
    result = json.loads(rec.FinalResult())

    return result.get("text", "")

# 🔥 Convert text → number
def text_to_number(text):
    mapping = {
        "zero": 0, "one": 1, "two": 2,
        "three": 3, "four": 4, "five": 5, 
        "six": 6, "seven": 7, "eight": 8, 
        "nine": 9, "ten": 10
    }
    return mapping.get(text.lower(), None)

if __name__ == "__main__":
    init_ears()

    while True:
        print("Ready to record...")
        audio_bytes = record_audio(fs=16000)

        text = listen(audio_bytes)
        number = text_to_number(text)

        print(f"I heard: {text}")

        if number is not None:
            print(f"Detected number: {number}")
        else:
            print("Invalid / noise")
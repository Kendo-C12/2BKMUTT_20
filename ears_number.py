from sys import prefix
from time import time
import time
import keyboard

import torch
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
from transformers import pipeline

import os
import re

from scipy.io import wavfile

import io

pipe = None

def init_ears():
    global pipe
    # Initialize the ASR pipeline
    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-base",
        device=-1 
    )

def record_audio(fs=16000):
    """Record audio until 'n' is pressed, return io.BytesIO containing WAV bytes."""
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

    # Concatenate all chunks
    audio_data = np.concatenate(recording, axis=0)

    # Convert to int16 for WAV
    audio_int16 = (audio_data * 32767).astype(np.int16)

    # Save to BytesIO instead of a file
    bytes_wav = io.BytesIO()
    write(bytes_wav, fs, audio_int16)
    bytes_wav.seek(0)  # rewind for reading
    print("Recording stopped. Audio is in memory.")
    return bytes_wav

def listen(bytes_wav):
    global pipe

    print("Processing audio from memory...")

    # Read WAV from BytesIO
    bytes_wav.seek(0)
    rate, audio = wavfile.read(bytes_wav)

    # Convert to float32
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    # Normalize if needed
    if np.max(np.abs(audio)) > 1:
        audio = audio / 32767.0

    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val

    # Whisper expects 1D array
    if len(audio.shape) > 1:
        audio = audio.squeeze()

    # Run ASR directly on numpy array
    result = pipe(
        audio,
        generate_kwargs={"language": "english", "task": "transcribe"}
    )

    return result["text"]

if __name__ == "__main__":
    init_ears()
    while True:
        print("Ready to record...")
        audio_bytes = record_audio(fs=16000)
        text = listen(audio_bytes)
        print(f"I heard: {text}")
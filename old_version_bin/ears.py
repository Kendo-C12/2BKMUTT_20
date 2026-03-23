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

pipe = None

def init_ears():
    global pipe
    # Initialize the ASR pipeline
    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-base",
        device=-1 
    )

def record_audio(filename="input.wav", fs=16000):
    """Records audio from the mic until 'n' is pressed."""
    print("Press 'y' to start recording...")
    while input().lower() != 'y':
        pass

    print("Recording... Press 'n' to stop.")
    recording = []
    
    # This opens a stream to capture audio in chunks
    def callback(indata, frames, time, status):
        if status:
            print(status)
        recording.append(indata.copy())

    with sd.InputStream(samplerate=fs, channels=1, callback=callback):
        while input().lower() != 'n':
            pass

    print("Recording stopped. Saving...")
    # Concatenate all chunks and save as a WAV file
    audio_data = np.concatenate(recording, axis=0)
    write(filename, fs, audio_data)
    return filename

def normalize_audio(input_path, output_path):
    rate, audio = wavfile.read(input_path)

    # convert to float if needed
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    # if int type (e.g., int16), scale to [-1, 1]
    if np.max(np.abs(audio)) > 1:
        audio = audio / 32767.0

    # normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val

    # convert back to int16 for saving
    audio_int16 = (audio * 32767).astype(np.int16)

    wavfile.write(output_path, rate, audio_int16)

def listen(audio_file="input.wav"):
    global pipe

    # Initialize the ASR pipeline
    print(f"Processing audio: {audio_file}...")

    # normalize first
    normalized_file = "normalized.wav"
    normalize_audio(audio_file, normalized_file)

    # Transcribe Thai audio
    result = pipe(
        normalized_file, 
        generate_kwargs={"language": "thai", "task": "transcribe"}
    )
    
    return result["text"]

if __name__ == "__main__":
    prefix = "inputSound_"
    extension = "wav"
    max_range = 20
    sample_rate = 16000

    directory = "."

    init_ears()

    while True:
        # while not keyboard.is_pressed('y'):
        #     time.sleep(0.1)

        t = input("Press 'y' to start recording...")
                
        files = os.listdir(directory)
        found_numbers = []

        for file in files:
            regex_pattern = rf"^{prefix}(\d+)\.{extension}$"
            match = re.match(regex_pattern, file)
            if match:
                num = int(match.group(1))
                if 1 <= num <= max_range:
                    found_numbers.append(num)

        found_numbers = sorted(found_numbers)
        print("Found files:", found_numbers)

        index = 0

        if found_numbers:
            index = found_numbers[0]-1
            for i in found_numbers:
                if i == index+1:
                    index += 1
                    # os.remove(f"{prefix}{index}.{extension}")
                else:
                    break
        
        file_name = f"{prefix}{index}.{extension}"

        text = listen(file_name)
        print(f"I heard: {text}")

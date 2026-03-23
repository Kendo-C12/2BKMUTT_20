import torch
from transformers import VitsModel, AutoTokenizer
import scipy.io.wavfile

import numpy as np

import io

import soundfile as sf
import sounddevice as sd

model = None
tokenizer = None

model_name = "facebook/mms-tts-tha"

def init_mouth():
    global model, tokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = VitsModel.from_pretrained(model_name)
    return model, tokenizer

def normalize_audio(audio):
    # Remove extra dimensions if they exist
    audio = audio.cpu().numpy()

    # remove extra dims if needed
    audio = np.squeeze(audio)

    # normalize to [-1, 1]
    audio = audio / np.max(np.abs(audio))

    # convert to int16
    audio_int16 = (audio * 32767).astype(np.int16)

    return audio_int16

def speak(text):
    global model, tokenizer

    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad():
        output = model(**inputs).waveform

    audio = normalize_audio(output)

    # Write to in-memory buffer instead of file
    buffer = io.BytesIO()
    scipy.io.wavfile.write(buffer, model.config.sampling_rate, audio)

    buffer.seek(0)  # VERY IMPORTANT
    buffer.name = "response.wav"  # optional but useful

    return buffer

if __name__ == "__main__":
    print("Testing the Mouth (TTS)...")

    init_mouth()

    # kmutt_context = None
    # with open("context.txt", "r", encoding="utf-8") as f:
    #     kmutt_context = f.read()

    wav_bytes = speak("เป็นอย่างไรบ้าง ที่นี้คือ มหาลัย.")
    
    input("Enter to continue...")
    
    wav_bytes.seek(0)
    data, samplerate = sf.read(wav_bytes, dtype='float32')
    sd.play(data, samplerate=samplerate)
    sd.wait()

    print("Done!")
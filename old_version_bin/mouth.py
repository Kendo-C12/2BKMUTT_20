import torch
from transformers import VitsModel, AutoTokenizer
import scipy.io.wavfile

import numpy as np


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

def speak(text,filename):
    global model, tokenizer

    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform

    # scipy.io.wavfile.write(filename, rate=model.config.sampling_rate, data=output.cpu().numpy().T)
    
    audio = normalize_audio(output)

    scipy.io.wavfile.write(filename, model.config.sampling_rate, audio)
    return filename

if __name__ == "__main__":
    print("Testing the Mouth (TTS)...")

    init_mouth()

    kmutt_context = None
    with open("context.txt", "r", encoding="utf-8") as f:
        kmutt_context = f.read()

    speak("เป็นอย่างไรบ้าง ที่นี้คือ มหาลัย", "output.wav")
    print("Done!")
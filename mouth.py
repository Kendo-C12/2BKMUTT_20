import torch
from transformers import VitsModel, VitsTokenizer
import scipy.io.wavfile

import numpy as np
import io
import soundfile as sf
import sounddevice as sd

model = None
tokenizer = None

model_name = "facebook/mms-tts-eng"

def init_mouth():
    global model, tokenizer

    tokenizer = VitsTokenizer.from_pretrained(model_name)
    model = VitsModel.from_pretrained(model_name)

    model.eval()
    return model, tokenizer

def normalize_audio(audio):
    audio = audio.cpu().numpy()
    audio = np.squeeze(audio)

    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val

    return (audio * 32767).astype(np.int16)

def speak(text):
    global model, tokenizer

    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad():
        output = model(**inputs)

    waveform = output.waveform
    audio = normalize_audio(waveform)

    samplerate = getattr(model.config, "sampling_rate", 22050)

    buffer = io.BytesIO()
    scipy.io.wavfile.write(buffer, samplerate, audio)

    buffer.seek(0)
    buffer.name = "response.wav"

    return buffer

if __name__ == "__main__":
    print("Testing the Mouth (TTS)...")

    init_mouth()

    wav_bytes = speak("Hello, this is a test of the mouth module.")

    input("Enter to continue...")

    wav_bytes.seek(0)
    data, samplerate = sf.read(wav_bytes, dtype='float32')

    sd.play(data, samplerate=samplerate)
    sd.wait()

    print("Done!")
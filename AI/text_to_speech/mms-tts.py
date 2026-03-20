from transformers import VitsModel, VitsTokenizer
import torch

# Load the Thai model
model_name = "facebook/mms-tts-tha"
tokenizer = VitsTokenizer.from_pretrained(model_name)
model = VitsModel.from_pretrained(model_name)

text = "สวัสดีครับ ยินดีที่ได้รู้จัก"
inputs = tokenizer(text, return_tensors="pt")

with torch.no_grad():
    output = model(**inputs).waveform
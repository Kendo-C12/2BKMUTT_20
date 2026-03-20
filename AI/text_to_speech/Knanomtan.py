from pythaitts import TTS

# 1. Initialize the TTS with the Khanomtan model
# This will automatically download the correct files from Hugging Face
tts = TTS(pretrained="khanomtan")

# 2. Generate and save the audio
# speaker_idx can be "Linda" (Female) or "p259" (Male)
text = "สวัสดีครับ ยินดีที่ได้รู้จัก"
output_file = "output.wav"

print(f"Generating audio for: {text}")
tts.tts(text, speaker_idx="Linda", filename=output_file)

print(f"Success! Audio saved to {output_file}")
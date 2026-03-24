import io

import ears
import brain
import mouth

import os
import re
import time

import soundfile as sf
import sounddevice as sd

# Configuration
directory = "."
input_prefix = "inputSound_"
output_prefix = "outputSound_"
extension = "wav"
max_range = 20

'''
listen io.BytesIO(.wav) -> text
think text -> text
speak text -> io.BytesIO(.wav)
'''

def next_index(index):
    index += 1
    if index > max_range:
        index = 1
    return index


def run_kmutt_assistant(audio_input, output_index):
    # 1. LISTEN
    try:
        audio_input.seek(0)  # IMPORTANT
        user_speech = ears.listen(audio_input)
    except Exception as e:
        print(f"Error during listening: {e}")
        return
    
    print(f"User asked: {user_speech}")

    user_speech = user_speech.strip()
    if not user_speech:
        print("Error: Transcription resulted in empty text.")
        return

    # (Optional test override)
    # user_speech = "บางมดคืออะไร"

    # 2. THINK
    try:
        ai_answer = brain.think(user_speech)
    except Exception as e:
        print(f"Error during thinking: {e}")
        return

    print(f"AI decided to say: {ai_answer}")

    ai_answer = ai_answer.strip()
    if not ai_answer:
        print("Error: Brain returned an empty answer.")
        return

    # 3. SPEAK → returns BytesIO
    try:
        audio_output = mouth.speak(ai_answer)
        audio_output.seek(0)
    except Exception as e:
        print(f"Error during speech synthesis: {e}")
        return

    # 4. SAVE (optional)
    file_name_output = f"{output_prefix}{output_index}.{extension}"
    try:
        with open(file_name_output, "wb") as f:
            f.write(audio_output.getvalue())
    except Exception as e:
        print(f"Error saving file: {e}")
        return

    print(f"Audio saved to: {file_name_output}")

    input("Press Enter to play the audio...")
    
    audio_output.seek(0)
    data, samplerate = sf.read(audio_output, dtype='float32')

    sd.play(data, samplerate)
    sd.wait()
        

if __name__ == "__main__":
    mouth.init_mouth()
    ears.init_ears()
    brain.init_brain()

    files = os.listdir(directory)
    found_input_numbers = []
    found_output_numbers = []

    # Scan files
    for file in files:
        input_match = re.match(f"^{input_prefix}(\\d+)\\.{extension}$", file)
        if input_match:
            num = int(input_match.group(1))
            if 1 <= num <= max_range:
                found_input_numbers.append(num)

        output_match = re.match(f"^{output_prefix}(\\d+)\\.{extension}$", file)
        if output_match:
            num = int(output_match.group(1))
            if 1 <= num <= max_range:
                found_output_numbers.append(num)

    found_input_numbers.sort()
    found_output_numbers.sort()

    # Find next input index
    input_index = 0
    if found_input_numbers:
        input_index = found_input_numbers[0] - 1
        for i in found_input_numbers:
            if i == input_index + 1:
                input_index += 1
            else:
                break
    input_index = next_index(input_index)

    # Find next output index
    output_index = 0
    if found_output_numbers:
        output_index = found_output_numbers[0] - 1
        for i in found_output_numbers:
            if i == output_index + 1:
                output_index += 1
            else:
                break
    output_index = next_index(output_index)

    print("Input Index:", input_index)
    print("Output Index:", output_index)

    # MAIN LOOP
    while True:
        filename = f"{input_prefix}{input_index}.{extension}"
        filepath = os.path.join(directory, filename)

        print(f"Waiting for {filename}...")
        time.sleep(0.5)

        if os.path.exists(filepath):
            try:
                # ✅ Convert file → BytesIO
                with open(filepath, "rb") as f:
                    wav_io = io.BytesIO(f.read())

                wav_io.seek(0)

                # ✅ Run pipeline
                run_kmutt_assistant(wav_io, output_index)

            except Exception as e:
                print(f"Error processing {filename}: {e}")

            # Move to next index
            input_index = next_index(input_index)
            output_index = next_index(output_index)

            # Optional: clean next output slot
            next_output_filename = f"{output_prefix}{next_index(output_index)}.{extension}"
            next_output_path = os.path.join(directory, next_output_filename)

            if os.path.exists(next_output_path):
                os.remove(next_output_path)
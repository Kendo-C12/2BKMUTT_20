import ears
import brain
import mouth

import os
import re

import time

# Configuration
directory = "."  # Current folder
input_prefix = "inputSound_"
output_prefix = "outputSound_"
extension = "wav"  # Add any extensions you use
max_range = 20

def next_index(index):
    index += 1
    if index > 20:
        index = 1
    return index

def run_kmutt_assistant(file_name_input, output_index):
    # 1. LISTEN (Whisper)
    # Note: Ensure 'input.wav' exists or replace with mic logic
    if not os.path.exists(file_name_input):
        print("Error: Please provide an 'input.wav' file to transcribe.")
        return
        
    user_speech = ears.listen(file_name_input)
    print(f"User asked: {user_speech}")

    user_speech = user_speech.strip()
    if not user_speech:
        print("Error: Transcription resulted in empty text.")
        return
    
    user_speech = "บางมดคืออะไร" # For testing, you can replace this with user_speech

    # 2. THINK (Wangchan)
    ai_answer = brain.think(user_speech)
    print(f"AI decided to say: {ai_answer}")
        
    ai_answer = ai_answer.strip()
    if not ai_answer:
        print("Error: Brain returned an empty answer.")
        return

    # 3. SPEAK (MMS-TTS)
    file_name_output = f"{output_prefix}{output_index}.{extension}"
    audio_file = mouth.speak(ai_answer, file_name_output)
    print(f"Audio saved to: {audio_file}")
    
    # (Optional) Play the audio automatically on Windows
    # os.system(f"start {audio_file}")

if __name__ == "__main__":
    mouth.init_mouth()
    ears.init_ears()
    brain.init_brain()

    files = os.listdir(directory)
    found_input_numbers = []
    found_output_numbers = []

    for file in files:
        # Matches 'sound_', then digits, then one of the extensions
        # Example: sound_5.wav -> extracts 5
        input_regex_pattern = f"^{input_prefix}(\d+)\.{extension}$"
        input_match = re.match(input_regex_pattern, file)
        
        if input_match:
            num = int(input_match.group(1))
            if 1 <= num <= max_range:
                found_input_numbers.append(num)

        output_regex_pattern = f"^{output_prefix}(\d+)\.{extension}$"
        output_match = re.match(output_regex_pattern, file)
        
        if output_match:
            num = int(output_match.group(1))
            if 1 <= num <= max_range:
                found_output_numbers.append(num)
    found_input_numbers = sorted(found_input_numbers)
    found_output_numbers = sorted(found_output_numbers)


    input_index = 0
    if found_input_numbers:
        input_index = found_input_numbers[0]-1
        for i in found_input_numbers:
            if i == input_index+1:
                input_index += 1
                # os.remove(f"{input_prefix}{input_index}.{extension}")
            else:
                break     
    input_index = next_index(input_index)

    output_index = 0
    if found_output_numbers:
        output_index = found_output_numbers[0]-1
        for i in found_output_numbers:
            if i == output_index+1:
                output_index += 1
            else:
                break        
    output_index = next_index(output_index)

    print("Input Index:", input_index)
    print("Output Index:", output_index)

    while 1:
        print(f"Waiting for {input_prefix}{input_index}.{extension}...")
        time.sleep(0.5)  # Avoid busy waiting
        check_filename = f"{input_prefix}{input_index}.{extension}"

        if os.path.exists(os.path.join(directory, check_filename)):
            try:
                run_kmutt_assistant(check_filename,output_index)
            except Exception as e:
                print(f"Error processing {check_filename}: {e}")

            input_index = next_index(input_index)
            output_index = next_index(output_index)

            next_output_filename = f"{output_prefix}{next_index(output_index)}.{extension}"
            if os.path.exists(os.path.join(directory, next_output_filename)):
                os.remove(os.path.join(directory, next_output_filename))

        

import os
import re
import time
import keyboard
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write

# --- Configuration ---
prefix = "inputSound_"
extension = "wav"
max_range = 20
sample_rate = 16000

directory = "."

def next_index(index):
    index += 1
    if index > 20:
        index = 1
    return index

if __name__ == "__main__":
    print("Program Running. Press 'Ctrl+C' to exit.")

    # 1. Logic to find the next available number (1-20)
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
    # Determine next number
    
    index = 0

    if found_numbers:
        index = found_numbers[0]-1
        for i in found_numbers:
            if i == index+1:
                index += 1
                # os.remove(f"{prefix}{index}.{extension}")
            else:
                break
    
    index = next_index(index)

    while True:    
        current_filename = f"{prefix}{index}.{extension}"
        
        # 2. Wait for User to start
        print(f"\n[Target: {current_filename}]")
        print("Hold 'y' to start recording...")
        
        while not keyboard.is_pressed('y'):
            time.sleep(0.1)

        # 3. Recording Phase
        audio_data = []
        def callback(indata, frames, time_info, status):
            audio_data.append(indata.copy())

        print("Recording... Press 'n' to stop.")
        with sd.InputStream(samplerate=sample_rate, channels=1, callback=callback):
            while not keyboard.is_pressed('n'):
                time.sleep(0.1)

        # 4. Save and Reset
        print("Saving...")
        if audio_data:
            recorded_audio = np.concatenate(audio_data, axis=0)
            write(current_filename, sample_rate, recorded_audio)
            print(f"Successfully saved {current_filename}")
        
        # Brief pause so the 'n' press doesn't trigger the next loop instantly
        time.sleep(1.0)

        index = next_index(index)
        next_filename = f"{prefix}{next_index(index)}.{extension}"
        if os.path.exists(os.path.join(directory, next_filename)):
            os.remove(os.path.join(directory, next_filename))

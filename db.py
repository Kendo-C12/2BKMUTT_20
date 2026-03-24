import sounddevice as sd
import numpy as np
import time
import scipy.io.wavfile as wav

# =====================
# CONFIG
# =====================
FS = 16000          # sample rate
DURATION = 0.1      # chunk duration
SILENCE_GAP = 2     # seconds to stop recording

# =====================
# UTILS
# =====================
def get_decibel(audio):
    rms = np.sqrt(np.mean(audio**2))
    if rms == 0:
        return 0
    db = 20 * np.log10(rms)
    return db

def record_chunk():
    audio = sd.rec(int(FS * DURATION), samplerate=FS, channels=1)
    sd.wait()
    return audio.flatten()

# =====================
# STEP 1: CALIBRATE QUIET
# =====================
def measure_quiet():
    print("Be quiet for 5 seconds...")
    values = []

    start = time.time()
    while time.time() - start < 5:
        audio = record_chunk()
        db = get_decibel(audio)
        values.append(db)

    return np.mean(values)

# =====================
# STEP 2: CALIBRATE SPEAK
# =====================
def measure_speak():
    print("Speak for 5 seconds...")
    values = []

    start = time.time()
    while time.time() - start < 5:
        audio = record_chunk()
        db = get_decibel(audio)
        values.append(db)

    return np.mean(values)

# =====================
# STEP 3: MAIN LOOP
# =====================
def listen_loop(trigger_db):
    print("Listening...")

    recording = []
    last_sound_time = None
    is_recording = False

    while True:
        audio = record_chunk()
        db = get_decibel(audio)

        print(f"DB: {db:.2f}")

        if db > trigger_db:
            # sound detected
            last_sound_time = time.time()
            is_recording = True
            recording.append(audio)

        else:
            if is_recording:
                # check silence timeout
                if time.time() - last_sound_time > SILENCE_GAP:
                    print("Stop recording")

                    # save file
                    full_audio = np.concatenate(recording)
                    wav.write("output.wav", FS, full_audio)

                    # call AI pipeline
                    process_audio("output.wav")

                    # reset
                    recording = []
                    is_recording = False

# =====================
# AI PLACEHOLDER
# =====================
def process_audio(file):
    print("Send to AI:", file)
    # Example:
    # speech_to_text(file)
    # send to LLM
    # TTS response
    pass

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    quiet_db = measure_quiet()
    speak_db = measure_speak()

    print("Quiet:", quiet_db)
    print("Speak:", speak_db)

    # threshold (same idea as your formula)
    trigger_db = (quiet_db + speak_db) / 2

    print("Trigger:", trigger_db)

    listen_loop(trigger_db)


import mouth

speech_list = {
    "Please speak again": "No_response.wav",
    "Receiving question. Please wait for a moment.": "Receiving_question.wav",
    
}   

if __name__ == "__main__":
    mouth.init()

    for text, filename in speech_list.items():
        print(f"Generating speech for: {text}")
        wav_bytes = mouth.speak(text)

        with open(filename, "wb") as f:
            f.write(wav_bytes.read())
import mouth

speech_list = {
    "Please speak again": "No_response.wav",
    "Receiving question. Please wait for a moment.": "Receiving_question.wav",

    # Added from Unity constants
    "Scan marker": "scan_maker.wav",
    "Do you want to go?": "wanna_go.wav",
    "Come with me": "come_with_me.wav",
    "Let me explain telesorting": "explain_telesorting.wav",
    "Let me explain the control panel": "explain_control_panel.wav",
    "Let me explain quest one": "explain_quest_1.wav",
    "Do you want the tutorial again?": "tutorial_again.wav",
    "Let me explain quest two": "explain_quest_2.wav",  
    "Do you want to do quest one?": "wanna_quest_1.wav",
    "Do you want to do quest two?": "wanna_quest_2.wav",
}

if __name__ == "__main__":
    mouth.init_mouth()

    for text, filename in speech_list.items():
        print(f"Generating speech for: {text}")
        wav_bytes = mouth.speak(text)

        with open("speech_list/" + filename, "wb") as f:
            f.write(wav_bytes.read())
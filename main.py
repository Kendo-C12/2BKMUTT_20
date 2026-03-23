import ears
import brain
import mouth

import os
import re

import time
from paho.mqtt import client as mqtt_client

import io

# Configuration
broker = 'test.mosquitto.org'
port = 1883

topic_subscribe = "2BKMUTT/PC"
topic_publish = "2BKMUTT/AR"

client_id = f'PC'
client = None

'''
ears.listen(BytesIO(.wav)) -> text
brain.think(text) -> text
mouth.speak(text) -> BytesIO(.wav)
'''

def run_kmutt_assistant(bytes_wav):
    # 1. LISTEN (Whisper)        
    user_speech = ears.listen(bytes_wav)
    print(f"User asked: {user_speech}")

    user_speech = user_speech.strip()
    if not user_speech:
        print("Error: Transcription resulted in empty text.")
        return mouth.speak("No speech detected")
    
    # 2. THINK (Wangchan)
    ai_answer = brain.think(user_speech)
    print(f"AI decided to say: {ai_answer}")
        
    ai_answer = ai_answer.strip()
    if not ai_answer:
        print("Error: Brain returned an empty answer.")
        return mouth.speak("No answer generated")

    # 3. SPEAK (MMS-TTS)
    bytes_wav = mouth.speak(ai_answer)
    print(f"Audio finish")
    
    return bytes_wav

def connect_mqtt():
    global client
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {reason_code}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id)
    client.on_connect = on_connect
    client.connect(broker, port)

def publish(msg):
    global client
    result = client.publish(topic_publish, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{len(msg)}` bytes to topic `{topic_publish}`")
    else:
        print(f"Failed to send message to topic {topic_publish}")

def subscribe():
    global client
    def handle_sound(client, userdata, msg, properties=None):
        print(f"Received {len(msg.payload)} bytes from `{msg.topic}` topic")

        # Convert raw bytes (.wav) → in-memory file
        wav_file = io.BytesIO(msg.payload)
        wav_file.name = "audio.wav"  # some libs require a filename

        # Pass to your assistant
        wav_file = run_kmutt_assistant(wav_file)
        wav_file.name = "response.wav"

        publish(wav_file.getvalue())
    client.subscribe(topic_subscribe)
    client.on_message = handle_sound


if __name__ == "__main__":
    mouth.init_mouth()
    ears.init_ears()
    brain.init_brain()

    connect_mqtt()
    subscribe()
    client.loop_forever()

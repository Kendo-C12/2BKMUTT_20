import os
import re

import time
from paho.mqtt import client as mqtt_client

import io

import ears

import soundfile as sf
import sounddevice as sd

# Configuration
broker = 'test.mosquitto.org'
port = 1883

topic_publish = "2BKMUTT/PC"
topic_subscribe = "2BKMUTT/AR"

client_id = f'tester'
client = None

directory = "."
check_filename = "input.wav"

flag = False

'''
ears.listen(BytesIO(.wav)) -> text
brain.think(text) -> text
mouth.speak(text) -> BytesIO(.wav)
'''

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
    global client,flag
    if flag:
        return
    flag = True

    result = client.publish(topic_publish, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic_publish}`")
    else:
        print(f"Failed to send message to topic {topic_publish}")
        flag = False

def subscribe():
    global client,flag
    def handle_sound(client, userdata, msg, properties=None):
        print(f"Received {len(msg.payload)} bytes from `{msg.topic}` topic")

        # Convert raw bytes (.wav) → in-memory file
        wav_bytes = io.BytesIO(msg.payload)
        wav_bytes.name = "audio.wav"  # some libs require a filename

        wav_bytes.seek(0)
        data, samplerate = sf.read(wav_bytes, dtype='float32')
        sd.play(data, samplerate=samplerate)
        sd.wait()

        flag = False

    client.subscribe(topic_subscribe)
    client.on_message = handle_sound


if __name__ == "__main__":

    ears.init_ears()
    connect_mqtt()
    subscribe()
    while True:
        time.sleep(0.5)
        if flag:
            print("Wait for flag...")
            continue
        print("Ready to record...")
        audio_bytes = ears.record_audio(fs=16000)
        publish(audio_bytes.getvalue())
        
        

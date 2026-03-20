import random
import time
from paho.mqtt import client as mqtt_client

# broker = 'mqtt.eclipseprojects.io'
# broker = 'broker.emqx.io'
broker = 'test.mosquitto.org'
port = 1883
topic = "KMUTT/2BKMUTT"

client_id = f'publish-2'

def connect_mqtt():
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {reason_code}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    # FIX IS HERE: Added 'properties' parameter for Version 2 compatibility
    def on_message(client, userdata, msg, properties=None):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    # This will keep the script running and listening for messages
    client.loop_forever()


if __name__ == '__main__':
    run()
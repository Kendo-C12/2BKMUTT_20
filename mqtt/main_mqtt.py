import random
import time
from paho.mqtt import client as mqtt_client

# broker = 'mqtt.eclipseprojects.io'
# broker = 'broker.emqx.io'
broker = 'test.mosquitto.org'
port = 1883
topic = "KMUTT/2BKMUTT"

client_id = f'PC-1'
client = None

AI = None

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

def publish(msg):
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")
    
def subscribe(client: mqtt_client):
    def handle_sound(client, userdata, msg, properties=None):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        msg = AI(msg)
        publish(msg)
    client.subscribe(topic)
    client.on_message = handle_sound


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()

if __name__ == '__main__':
    run()
    
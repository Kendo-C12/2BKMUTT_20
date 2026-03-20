import random
import time
from paho.mqtt import client as mqtt_client

# broker = 'mqtt.eclipseprojects.io'
# broker = 'broker.emqx.io'
broker = 'test.mosquitto.org'
port = 1883
topic = "KMUTT/2BKMUTT"

client_id = f'publish-1'

def connect_mqtt():
    # FIX 1: Updated signature for Version 2 (added reason_code and properties)
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {reason_code}")

    # FIX 2: Explicitly using VERSION2
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client):
    msg_count = 1
    while True:
        time.sleep(1)
        msg = f"messages: {msg_count}"
        result = client.publish(topic, msg)
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1
        if msg_count > 5:
            break

def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()

if __name__ == '__main__':
    run()
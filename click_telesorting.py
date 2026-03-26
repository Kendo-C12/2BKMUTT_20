import random
import time
import json
from paho.mqtt import client as mqtt_client

import keyboard

# broker = 'mqtt.eclipseprojects.io'
# broker = 'broker.emqx.io'
# broker = 'test.mosquitto.org'
broker = '10.22.10.1'
port = 1883
topic = "2BKMUTT/KMUTT"

client_id = f'click_telesorting'

msg_template = {
    "id": 3000,          # 🔹 better as number
    "type": "String",
    "value": "1",
    "detail": "PC"
}

def keyboard_control(client):
    print("Press number (0–9) then ENTER | Ctrl+C to exit")

    try:
        while True:
            key = input(">> ").strip()

            if key.isdigit() and len(key) == 1:
                num = int(key)

                print(f"Sending: {num}")
                publish(client, num)

            else:
                print("❌ Invalid input (use single digit 0–9)")

    except KeyboardInterrupt:
        print("\nStopped keyboard control")

def init_mqtt(_client_id=client_id, _broker=broker, _port=port, _topic=topic):
    global client_id, broker, port, topic
    client_id = _client_id
    broker = _broker
    port = _port
    topic = _topic


def connect_mqtt():
    connected = False

    def on_connect(client, userdata, flags, reason_code, properties):
        nonlocal connected
        if reason_code == 0:
            print("Connected to MQTT Broker!")
            connected = True
        else:
            print(f"Failed to connect, return code {reason_code}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id)
    client.on_connect = on_connect
    client.connect(broker, port)

    while not connected:
        client.loop(timeout=1.0)  # process network events
        time.sleep(0.1)          # avoid busy-wait

    return client


def publish(client, value):
    # 🔹 update template
    msg_template["value"] = str(value)

    # 🔹 convert to JSON string
    msg_json = json.dumps(msg_template)

    result = client.publish(topic, msg_json)
    status = result[0]

    if status == 0:
        print(f"Send `{msg_json}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


if __name__ == '__main__':
    client = connect_mqtt()
    client.loop_start()

    keyboard_control(client)

    client.loop_stop()
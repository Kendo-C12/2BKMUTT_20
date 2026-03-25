import random
import time
import json
from paho.mqtt import client as mqtt_client

# broker = 'mqtt.eclipseprojects.io'
# broker = 'broker.emqx.io'
broker = 'test.mosquitto.org'
port = 1883
topic = "tss/1/rpc/request/1"

client_id = f'sub_test'


def connect_mqtt():
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {reason_code}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id)
    client.on_connect = on_connect
    client.connect(broker, port, keepalive=60)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg, properties=None):
        payload = msg.payload.decode()

        try:
            # 🔹 Try parse JSON
            data = json.loads(payload)

            # 🔹 Extract fields safely
            cmd = data.get("cmd", "N/A")
            param = data.get("param", [])

            # 🔹 Handle param list safely
            if isinstance(param, list) and len(param) >= 2:
                output = str(param[0])
                action = str(param[1])
            else:
                output = "N/A"
                action = "N/A"

            print(f"[JSON] cmd={cmd}, output={output}, action={action}")
        except json.JSONDecodeError:
            # 🔹 Fallback if not JSON
            print(f"[RAW] `{payload}` from `{msg.topic}`")

    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
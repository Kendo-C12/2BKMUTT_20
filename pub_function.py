import random
import time
import json
from paho.mqtt import client as mqtt_client

# broker = 'mqtt.eclipseprojects.io'
# broker = 'broker.emqx.io'
broker = 'test.mosquitto.org'
port = 1883

client_id = f'test_PC'

msg_template = {
    "id": 3000,          # 🔹 better as number
    "type": "String",
    "value": 1,
    "detail": "PC"
}

def init_mqtt(_client_id=client_id, _broker=broker, _port=port):
    global client_id, broker, port, topic
    client_id = _client_id
    broker = _broker
    port = _port


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


def publish(client, topic, value):
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


def run():
    client = connect_mqtt()
    client.loop_start()
    for i in range(5):
        publish(client, i)   # 🔹 send values 0-4
        time.sleep(1)
    client.loop_stop()


if __name__ == '__main__':
    run()
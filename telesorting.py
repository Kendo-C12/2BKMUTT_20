import random
import time
from paho.mqtt import client as mqtt_client

import keyboard

broker = 'test.mosquitto.org'
port = 1883

# subscribe
topic_subscribe = [f"tss/1/sensor/{INPUT}" for INPUT in range(0, 11)]
'''
topic format: tss/1/sensor/[INPUT]

data format:
{
 “id”: [ID],
 “type”: [TYPE],
 “value”: [VALUE],
 “detail”: [DETAIL]
}

[ID] หมายถึง ID ของ Input เป็นข้อมูลประเภท Number
[TYPE] หมายถึง ประเภทของ Input เป็นข้อมูลประเภท String
[VALUE] หมายถึง ค่าสถานะของ Input เมื่ออ่านค่าจาก Proximity Sensor จะเป็นข้อมูลประเภท Number เมื่ออ่านค่าจาก Vision Sensor จะเป็นข้อมูลประเภท String
[DETAIL] หมายถึง รายละเอียดเพิ่มเติมของ Input เป็นข้อมูลประเภท String
'''

# publish
topic_publish = [f"tss/1/rpc/request/{OUTPUT}" for OUTPUT in range(0, 10)]
'''
topic format: tss/1/rpc/request/[OUTPUT]
data format:
{
 “cmd”: “ACTUATOR”,
 “param”: [[OUTPUT], [ACTION]]
}

[OUTPUT] หมายถึง ID ของ Output เป็นข้อมูลประเภท Number
[ACTION] หมายถึง ส่งคำสั่งควบคุมของ Output เป็นข้อมูลประเภท Number
'''
template_publish = {
    "cmd": "ACTUATOR",
    "param": [[0], [0]]
}

last_push = [(time.time()-5) for OUTPUT in range(0, 10)]

status = ["0" for _ in range(10)]
status.append("None")

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

def publish(id, topic, duration=5):
    def handle_publish(id, topic, command):
        msg = template_publish.copy()
        msg["param"][0][0] = int(id)
        msg["param"][1][0] = 1
    # Create a copy of the template and update it with the new values
    msg = template_publish.copy()
    msg["param"][0][0] = int(id)
    msg["param"][1][0] = 1

    result = client.publish(topic, str(msg))
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")
    
def subscribe(client: mqtt_client):
    def handle_sound(client, userdata, msg, properties=None):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        status[int(msg["id"])] = str(msg["value"])
    for topic in topic_subscribe:
        client.subscribe(topic)
    client.on_message = handle_sound


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()

if __name__ == '__main__':
    run()

    while 1:
        for i in range(10):
            if keyboard.is_pressed(str(i)):
                publish(str(i), topic_publish[i])
                time.sleep(0.02)  # debounce delay

        output = ""
        for i in range(10):
            output += f"{i}:{status[i]} "
        print(f"\r{output}", end="")
import paho.mqtt.client as mqtt
import time

# Define the broker and topic
BROKER = 'broker.hivemq.com' # A free public broker
PORT = 1883
TOPIC = "python/test/topic"
MESSAGE = "Hello MQTT from Python!"

def publish():
    # Create a client instance, specifying MQTT version 5 (recommended for new development)
    # Use CallbackAPIVersion.VERSION1 for compatibility with older examples/brokers
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) 
    
    client.connect(BROKER, PORT, 60)
    client.loop_start() # Start the loop to handle network traffic in a background thread

    # Publish a message
    result, mid = client.publish(TOPIC, MESSAGE, qos=1)
    if result == mqtt.MQTT_ERR_SUCCESS:
        print(f"Message published successfully to topic '{TOPIC}'")
    else:
        print(f"Failed to publish message: {result}")

    time.sleep(2) # Give time for the message to be sent
    client.loop_stop()
    client.disconnect()

if __name__ == '__main__':
    publish()

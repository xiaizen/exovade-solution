import paho.mqtt.client as mqtt
import json

class MQTTClient:
    def __init__(self, broker="test.mosquitto.org", port=1883):
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port
        self.connected = False
        
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            self.connected = True
            print(f"[AGENCY] Connected to MQTT Broker: {self.broker}")
        except Exception as e:
            print(f"[AGENCY] MQTT Connection Failed: {e}")

    def publish(self, topic, payload):
        if not self.connected:
            print("[AGENCY] Cannot publish: MQTT not connected.")
            return

        if isinstance(payload, dict):
            payload = json.dumps(payload)
            
        self.client.publish(topic, payload)
        print(f"[AGENCY] Published to {topic}: {payload}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

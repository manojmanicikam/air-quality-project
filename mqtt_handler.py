import paho.mqtt.client as mqtt
import json
import time


class MQTTReceiver:
    def __init__(self, broker, port, topic):
        self.broker = broker
        self.port = port
        self.topic = topic

        self.last_data = None
        self.last_received_time = 0
        self.data_history = []
        self.connected = False  # ← track broker connection

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="python_receiver")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    # ───────── AQI ─────────
    def calculate_aqi_no2(self, cp):
        breakpoints = [
            (0.000, 0.053,  0,   50),
            (0.054, 0.100,  51,  100),
            (0.101, 0.360,  101, 150),
            (0.361, 0.649,  151, 200),
            (0.650, 1.249,  201, 300),
            (1.250, 2.049,  301, 400),
            (2.050, 5.000,  401, 500),
        ]
        for c_lo, c_hi, i_lo, i_hi in breakpoints:
            if c_lo <= cp <= c_hi:
                return int(((i_hi - i_lo) / (c_hi - c_lo)) * (cp - c_lo) + i_lo)
        return None

    # ───────── CALLBACKS ─────────
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print("Connected to MQTT broker")
            client.subscribe(self.topic)
        else:
            self.connected = False
            print(f"Connection failed: rc={rc}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"Disconnected from MQTT broker: rc={rc}")

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())

            temp = data.get("temp")
            hum  = data.get("hum")
            ppm  = data.get("h2_ppm")

            ppm = round(ppm * 0.1, 4)
            aqi = self.calculate_aqi_no2(ppm)

            self.last_data = {
                "temp": temp,
                "hum":  hum,
                "no2":  ppm,
                "aqi":  aqi,
                "timestamp": time.time(),
            }

            self.data_history.append(self.last_data)
            if len(self.data_history) > 50:
                self.data_history.pop(0)

            self.last_received_time = time.time()

        except Exception as e:
            print(f"Message parse error: {e}")

    # ───────── START ─────────
    def start(self):
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()

    # ───────── GETTERS ─────────
    def get_data(self):
        return self.last_data

    def get_data_history(self):
        return self.data_history

    def is_fresh(self, timeout=5):
        """True if a message arrived within `timeout` seconds."""
        return (time.time() - self.last_received_time) < timeout

    def is_connected(self):
        """True if the TCP connection to the broker is up."""
        return self.connected

    def seconds_since_last_message(self):
        if self.last_received_time == 0:
            return None
        return round(time.time() - self.last_received_time, 1)
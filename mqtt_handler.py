import paho.mqtt.client as mqtt
import json
import time


class MQTTReceiver:
    def __init__(self, broker, port, topic):
        self.broker = broker
        self.port   = port
        self.topic  = topic

        self.last_data          = None
        self.last_received_time = 0
        self.data_history       = []
        self.connected          = False
        self.last_error         = None   # ← surface errors to the UI

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1,
            client_id="python_receiver"
        )
        self.client.on_connect    = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message    = self.on_message

    # ───────── AQI ─────────
    def calculate_aqi_no2(self, cp: float) -> int:
        cp = float(cp)
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
        return 500   # clamp instead of None — prevents downstream crashes

    # ───────── CALLBACKS ─────────
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print("[MQTT] Connected to broker")
            client.subscribe(self.topic)
            print(f"[MQTT] Subscribed to topic: {self.topic}")
        else:
            self.connected = False
            self.last_error = f"Connection failed with rc={rc}"
            print(f"[MQTT] {self.last_error}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print(f"[MQTT] Disconnected: rc={rc}")

    def on_message(self, client, userdata, msg):
        try:
            raw = msg.payload.decode()
            print(f"[MQTT] Raw payload: {raw}")        # ← shows in terminal

            data = json.loads(raw)
            print(f"[MQTT] Parsed keys: {list(data.keys())}")

            temp = data.get("temp")
            hum  = data.get("hum")

            # ── Try all plausible key names your ESP32 might send ──
            ppm_raw = (
                data.get("h2_ppm")
                or data.get("ppm")
                or data.get("no2")
                or data.get("no2_ppm")
            )

            if ppm_raw is None:
                self.last_error = (
                    f"No gas key found in payload. Keys received: {list(data.keys())}"
                )
                print(f"[MQTT] WARNING: {self.last_error}")
                return   # don't update last_data with broken record

            ppm = round(float(ppm_raw) * 0.1, 4)
            aqi = self.calculate_aqi_no2(ppm)

            self.last_data = {
                "temp":      temp,
                "hum":       hum,
                "no2":       ppm,
                "aqi":       aqi,
                "timestamp": time.time(),
            }
            self.last_error = None   # clear any previous error

            self.data_history.append(self.last_data)
            if len(self.data_history) > 50:
                self.data_history.pop(0)

            self.last_received_time = time.time()
            print(f"[MQTT] Stored → temp={temp} hum={hum} no2={ppm} aqi={aqi}")

        except json.JSONDecodeError as e:
            self.last_error = f"JSON parse error: {e} | raw='{msg.payload.decode()}'"
            print(f"[MQTT] {self.last_error}")
        except Exception as e:
            self.last_error = f"Unexpected error: {e}"
            print(f"[MQTT] {self.last_error}")

    # ───────── START ─────────
    def start(self):
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            print(f"[MQTT] Connecting to {self.broker}:{self.port} ...")
        except Exception as e:
            self.last_error = f"Could not connect to broker: {e}"
            print(f"[MQTT] {self.last_error}")

    # ───────── GETTERS ─────────
    def get_data(self):
        return self.last_data

    def get_data_history(self):
        return self.data_history

    def get_last_error(self):
        """Returns the last error string, or None if everything is healthy."""
        return self.last_error

    def is_fresh(self, timeout=5):
        return (time.time() - self.last_received_time) < timeout

    def is_connected(self):
        return self.connected

    def seconds_since_last_message(self):
        if self.last_received_time == 0:
            return None
        return round(time.time() - self.last_received_time, 1)
import paho.mqtt.client as mqtt
import json
import time

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "arun/esp32/sensors"

# ───────── GLOBAL STORAGE ─────────
last_data = None
last_received_time = 0

# ───────── AQI FUNCTION ─────────
def calculate_aqi_no2(cp):
    breakpoints = [
        (0.000, 0.053, 0, 50),
        (0.054, 0.100, 51, 100),
        (0.101, 0.360, 101, 150),
        (0.361, 0.649, 151, 200),
        (0.650, 1.249, 201, 300),
        (1.250, 2.049, 301, 400),
        (2.050, 5.000, 401, 500)
    ]

    for c_lo, c_hi, i_lo, i_hi in breakpoints:
        if c_lo <= cp <= c_hi:
            return int(((i_hi - i_lo) / (c_hi - c_lo)) * (cp - c_lo) + i_lo)

    return None

# ───────── CALLBACKS ─────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected")
        client.subscribe(TOPIC)
    else:
        print("Connection failed:", rc)

def on_message(client, userdata, msg):
    global last_data, last_received_time

    try:
        data = json.loads(msg.payload.decode())

        temp = data.get("temp")
        hum  = data.get("hum")
        ppm  = data.get("h2_ppm")

        ppm = round(ppm * 0.1, 4)
        aqi = calculate_aqi_no2(ppm)

        # Store latest data
        last_data = (temp, hum, ppm, aqi)
        last_received_time = time.time()

        print(f"📡 NEW → Temp: {temp}°C | Humidity: {hum}% | NO2: {ppm} ppm | AQI: {aqi}")

    except Exception as e:
        print("Error:", e)

# ───────── CLIENT SETUP ─────────
client = mqtt.Client(client_id="python_receiver")

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)

print("Waiting for data...\n")

client.loop_start()   # Non-blocking loop

# ───────── FALLBACK LOOP ─────────
while True:
    time.sleep(3)

    if last_data is not None:
        elapsed = time.time() - last_received_time

        if elapsed >= 3:
            temp, hum, ppm, aqi = last_data
            print(f"⏳ USING OLD → Temp: {temp}°C | Humidity: {hum}% | NO2: {ppm} ppm | AQI: {aqi}")
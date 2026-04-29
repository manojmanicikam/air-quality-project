import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from mqtt_handler import MQTTReceiver

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "arun/esp32/sensors"
REFRESH_MS   = 2_000   # UI refresh interval
FRESH_TIMEOUT = 5      # seconds before data is considered stale

# ─────────────────────────────────────────
# PAGE
# ─────────────────────────────────────────
st.set_page_config(page_title="AQI Dashboard", page_icon="🌍", layout="centered")
st_autorefresh(interval=REFRESH_MS, key="aqi_refresh")   # replaces sleep+rerun

# ─────────────────────────────────────────
# INIT MQTT ONCE PER SESSION
# ─────────────────────────────────────────
if "mqtt" not in st.session_state:
    receiver = MQTTReceiver(BROKER, PORT, TOPIC)
    receiver.start()
    st.session_state.mqtt = receiver

receiver: MQTTReceiver = st.session_state.mqtt

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def aqi_color(aqi: int) -> str:
    if aqi is None:
        return "gray"
    if aqi <= 50:   return "green"
    if aqi <= 100:  return "yellow"
    if aqi <= 150:  return "orange"
    if aqi <= 200:  return "red"
    if aqi <= 300:  return "purple"
    return "maroon"

def aqi_label(aqi: int) -> str:
    if aqi is None:         return "Unknown"
    if aqi <= 50:           return "Good"
    if aqi <= 100:          return "Moderate"
    if aqi <= 150:          return "Unhealthy for Sensitive Groups"
    if aqi <= 200:          return "Unhealthy"
    if aqi <= 300:          return "Very Unhealthy"
    return "Hazardous"

# ─────────────────────────────────────────
# HEADER  +  CONNECTION STATUS
# ─────────────────────────────────────────
st.title("🌍 Live AQI Monitoring")

broker_ok  = receiver.is_connected()
data_fresh = receiver.is_fresh(FRESH_TIMEOUT)
data       = receiver.get_data()
age        = receiver.seconds_since_last_message()

# Three possible states
if broker_ok and data_fresh:
    st.success("🟢 Live — receiving data from ESP32")
elif broker_ok and not data_fresh:
    age_str = f"{age}s ago" if age is not None else "never"
    st.warning(f"🟡 Broker connected, but no message yet (last: {age_str})")
else:
    st.error("🔴 Disconnected from MQTT broker — retrying…")

# ─────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────
if data:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ Temp",     f"{data['temp']} °C")
    col2.metric("💧 Humidity", f"{data['hum']} %")
    col3.metric("🧪 NO₂",      f"{data['no2']} ppm")
    col4.metric("🌫️ AQI",      f"{data['aqi']}")

    color = aqi_color(data["aqi"])
    label = aqi_label(data["aqi"])
    st.markdown(
        f"""
        <div style="
            background:{color};
            color:white;
            padding:10px 18px;
            border-radius:8px;
            font-weight:600;
            font-size:1rem;
            display:inline-block;
            margin-top:4px;">
            AQI {data['aqi']} — {label}
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("⏳ Waiting for first MQTT message…")

# ─────────────────────────────────────────
# HISTORY CHART
# ─────────────────────────────────────────
history = receiver.get_data_history()
if len(history) >= 2:
    st.divider()
    st.subheader("📈 Sensor History (last 50 readings)")

    df = pd.DataFrame(history)
    df["time"] = pd.to_datetime(df["timestamp"], unit="s").dt.strftime("%H:%M:%S")
    df = df.set_index("time")

    tab1, tab2, tab3 = st.tabs(["AQI", "NO₂ ppm", "Temp & Humidity"])

    with tab1:
        st.line_chart(df[["aqi"]])
    with tab2:
        st.line_chart(df[["no2"]])
    with tab3:
        st.line_chart(df[["temp", "hum"]])
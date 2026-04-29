import streamlit as st
import pandas as pd
import folium
import math
import random
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from streamlit_folium import st_folium
from mqtt_handler import MQTTReceiver
from forecaster import AQIForecaster

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
BROKER        = "broker.hivemq.com"
PORT          = 1883
TOPIC         = "arun/esp32/sensors"
REFRESH_MS    = 5_000
FRESH_TIMEOUT = 10
FORECAST_TTL  = 300

SENSOR_LAT = 13.127879413345047
SENSOR_LON = 77.58657587251105

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="AQI Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #0b0f1a;
    color: #e2e8f0;
}
div[data-testid="metric-container"] {
    background: #131929;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 18px 20px;
}
div[data-testid="metric-container"] label {
    color: #64748b !important;
    font-size: 0.78rem !important;
    letter-spacing: .06em;
    text-transform: uppercase;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem !important;
    color: #f1f5f9 !important;
}
.forecast-card {
    background: #131929;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 18px 16px;
    text-align: center;
    transition: border-color .2s;
}
.forecast-card:hover { border-color: #38bdf8; }
.forecast-hour {
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    color: #475569;
    margin-bottom: 6px;
    letter-spacing: .08em;
}
.forecast-time { font-size: 0.82rem; color: #94a3b8; margin-bottom: 10px; }
.forecast-aqi {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
}
.forecast-ppm  { font-size: 0.78rem; color: #64748b; margin-bottom: 8px; }
.forecast-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: .04em;
}
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 8px;
}
.pill-live    { background:#052e16; color:#4ade80; border:1px solid #16a34a; }
.pill-stale   { background:#1c1608; color:#facc15; border:1px solid #ca8a04; }
.pill-offline { background:#1c0808; color:#f87171; border:1px solid #dc2626; }
h1, h2, h3 { font-family: 'Space Mono', monospace !important; }
.legend-row { display:flex; align-items:center; gap:8px; font-size:0.78rem; margin-bottom:5px; }
.legend-dot { width:13px; height:13px; border-radius:50%; flex-shrink:0; }
div[data-testid="stStatusWidget"] { display:none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# INIT MQTT & FORECASTER
# ─────────────────────────────────────────
if "mqtt" not in st.session_state:
    receiver = MQTTReceiver(BROKER, PORT, TOPIC)
    receiver.start()
    st.session_state.mqtt = receiver

if "forecaster_ok" not in st.session_state:
    try:
        st.session_state.forecaster    = AQIForecaster("lstm_model.keras")
        st.session_state.forecaster_ok = True
    except Exception as e:
        st.session_state.forecaster_ok  = False
        st.session_state.forecaster_err = str(e)

if "forecast_cache" not in st.session_state:
    st.session_state.forecast_cache = None
    st.session_state.forecast_ts    = 0.0

receiver: MQTTReceiver = st.session_state.mqtt

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
AQI_PALETTE = {
    "Good":                  ("#4ade80", "#052e16"),
    "Moderate":              ("#facc15", "#1c1608"),
    "Unhealthy (Sensitive)": ("#fb923c", "#1c0e08"),
    "Unhealthy":             ("#f87171", "#1c0808"),
    "Very Unhealthy":        ("#c084fc", "#160820"),
    "Hazardous":             ("#fb7185", "#200810"),
}

def aqi_colors(label: str):
    return AQI_PALETTE.get(label, ("#94a3b8", "#0f172a"))

def aqi_label(aqi: int) -> str:
    if aqi is None: return "Unknown"
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Moderate"
    if aqi <= 150:  return "Unhealthy (Sensitive)"
    if aqi <= 200:  return "Unhealthy"
    if aqi <= 300:  return "Very Unhealthy"
    return "Hazardous"

def render_forecast_card(entry: dict) -> str:
    label  = entry["label"]
    fg, bg = aqi_colors(label)
    ts_str = entry["timestamp"].strftime("%I:%M %p")
    offset = entry["hour_offset"]
    return f"""
    <div class="forecast-card">
        <div class="forecast-hour">+{offset} HR</div>
        <div class="forecast-time">{ts_str}</div>
        <div class="forecast-aqi" style="color:{fg}">{entry['aqi']}</div>
        <div class="forecast-ppm">{entry['ppm']:.4f} ppm NO₂</div>
        <div class="forecast-badge"
             style="background:{bg};color:{fg};border:1px solid {fg}40">
            {label}
        </div>
    </div>"""

# ─────────────────────────────────────────
# AQI ZONE SEEDER  (fixed seed → stable positions)
# ─────────────────────────────────────────
def _seed_aqi_zones(n: int = 28, seed: int = 77) -> list[dict]:
    """
    Scatter n AQI zones within ~1.5 km of the sensor.
    Distribution: Good 40%, Moderate 25%, Sensitive 15%,
                  Unhealthy 10%, Very Unhealthy 7%, Hazardous 3%
    """
    rng = random.Random(seed)
    buckets = (
        [(0,   50)] * 11 +
        [(51, 100)] * 7  +
        [(101,150)] * 4  +
        [(151,200)] * 3  +
        [(201,300)] * 2  +
        [(301,400)] * 1
    )
    rng.shuffle(buckets)
    zones = []
    for lo, hi in buckets[:n]:
        angle  = rng.uniform(0, 2 * math.pi)
        radius = rng.uniform(120, 1400)          # metres from sensor
        dlat   = (radius * math.cos(angle)) / 111_320
        dlon   = (radius * math.sin(angle)) / (
                    111_320 * math.cos(math.radians(SENSOR_LAT)))
        aqi    = rng.randint(lo, hi)
        zones.append({
            "lat":    SENSOR_LAT + dlat,
            "lon":    SENSOR_LON + dlon,
            "aqi":    aqi,
            "radius": rng.randint(7, 18),        # folium circle px radius
        })
    return zones

# ─────────────────────────────────────────
# MAP BUILDER  (cached — rebuilt only when live AQI changes)
# ─────────────────────────────────────────
@st.cache_resource
def build_map(live_aqi: int | None = None) -> folium.Map:
    m = folium.Map(
        location=[SENSOR_LAT, SENSOR_LON],
        zoom_start=15,
        tiles="CartoDB dark_matter",
    )

    # ── Draw seeded AQI zones ─────────────────────────────
    for z in _seed_aqi_zones():
        label    = aqi_label(z["aqi"])
        fg, _    = aqi_colors(label)
        folium.CircleMarker(
            location=[z["lat"], z["lon"]],
            radius=z["radius"],
            color=fg,
            fill=True,
            fill_color=fg,
            fill_opacity=0.30,
            weight=1.2,
            tooltip=f'AQI {z["aqi"]} — {label}',
            popup=folium.Popup(
                f'<div style="font-family:sans-serif;text-align:center;padding:4px 8px">'
                f'<span style="font-size:1.2rem;font-weight:700;color:{fg}">'
                f'AQI {z["aqi"]}</span><br>'
                f'<span style="color:#555;font-size:.8rem">{label}</span></div>',
                max_width=160,
            ),
        ).add_to(m)

    # ── Sensor origin marker ──────────────────────────────
    origin_aqi = live_aqi or 25
    o_label    = aqi_label(origin_aqi)
    o_fg, _    = aqi_colors(o_label)

    # Pulsing ring around sensor
    folium.CircleMarker(
        location=[SENSOR_LAT, SENSOR_LON],
        radius=22,
        color=o_fg,
        fill=True,
        fill_color=o_fg,
        fill_opacity=0.12,
        weight=2,
    ).add_to(m)

    folium.Marker(
        location=[SENSOR_LAT, SENSOR_LON],
        tooltip="📍 I'm here",
        popup=folium.Popup(
            f'<div style="font-family:sans-serif;text-align:center;min-width:150px">'
            f'<b>📍 Sensor Location</b><br>'
            f'<span style="font-size:1rem;font-weight:700;color:{o_fg}">'
            f'AQI {origin_aqi}</span><br>'
            f'<span style="color:#555;font-size:.8rem">{o_label}</span><br>'
            f'<hr style="margin:5px 0">'
            f'<span style="font-size:.7rem;color:#aaa">'
            f'{SENSOR_LAT:.6f}, {SENSOR_LON:.6f}</span></div>',
            max_width=200,
        ),
        icon=folium.Icon(
            color="red",
            icon_color="white",
            icon="map-marker",
            prefix="fa",
        ),
    ).add_to(m)

    return m

# ─────────────────────────────────────────
# STATIC HEADER
# ─────────────────────────────────────────
st.markdown("## 🌍 AQI Monitoring")
st.markdown("---")

# ─────────────────────────────────────────
# MAP + LEGEND
# ─────────────────────────────────────────
st.markdown("### 🗺️ Live AQI Map")

map_col, legend_col = st.columns([5, 1])

with legend_col:
    st.markdown("**AQI Levels**")
    for label, (fg, _) in AQI_PALETTE.items():
        st.markdown(
            f'<div class="legend-row">'
            f'<div class="legend-dot" style="background:{fg}"></div>'
            f'<span>{label}</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div style="margin-top:12px;font-size:0.72rem;color:#475569;line-height:1.7">'
        '🔴 Red pin = your sensor<br>'
        '⚪ Circles = nearby AQI zones<br>'
        'Click a circle for details'
        '</div>',
        unsafe_allow_html=True,
    )

with map_col:
    _data     = receiver.get_data()
    _live_aqi = _data["aqi"] if _data else None

    # Only invalidate cache when live AQI value actually changes
    _map_key = f"map_{_live_aqi}"
    if st.session_state.get("_map_cache_key") != _map_key:
        st.session_state["_map_cache_key"] = _map_key
        # Clear st.cache_resource so build_map() rebuilds with new live_aqi
        build_map.clear()

    st_folium(
        build_map(live_aqi=_live_aqi),
        width="100%",
        height=460,
        returned_objects=[],
        key="sensor_map",
    )

st.markdown("---")

# ─────────────────────────────────────────
# LIVE FRAGMENT
# ─────────────────────────────────────────
@st.fragment(run_every=REFRESH_MS / 1000)
def live_panel():
    data      = receiver.get_data()
    fresh     = receiver.is_fresh(FRESH_TIMEOUT)
    connected = receiver.is_connected()
    age       = receiver.seconds_since_last_message()

    # Connection pill
    if connected and fresh:
        pill_cls, dot, status_text = "pill-live",    "●", "Live · receiving data"
    elif connected:
        age_str = f"{age}s ago" if age else "never"
        pill_cls, dot, status_text = "pill-stale",   "◉", f"Connected · last msg {age_str}"
    else:
        pill_cls, dot, status_text = "pill-offline", "○", "Disconnected from broker"

    st.markdown(
        f'<div class="status-pill {pill_cls}">{dot} {status_text}</div>',
        unsafe_allow_html=True,
    )

    mqtt_error = receiver.get_last_error()
    if mqtt_error:
        st.warning(f"⚠️ MQTT error: `{mqtt_error}`")

    # Metrics
    st.markdown("### 📊 Current Readings")
    if data:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🌡️ Temperature", f"{data['temp']} °C")
        c2.metric("💧 Humidity",    f"{data['hum']} %")
        c3.metric("🧪 NO₂",         f"{data['no2']} ppm")
        c4.metric("🌫️ AQI",         f"{data['aqi']}")

        label  = aqi_label(data["aqi"])
        fg, bg = aqi_colors(label)
        st.markdown(
            f'<div style="margin:12px 0 4px">'
            f'<span style="background:{bg};color:{fg};border:1px solid {fg}60;'
            f'padding:5px 16px;border-radius:999px;font-weight:700;font-size:.85rem">'
            f'AQI {data["aqi"]} — {label}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("⏳ Waiting for first MQTT message…")

    st.markdown("---")

    # Forecast
    st.markdown("### 🔮 LSTM Forecast — Next 3 Hours")
    if not st.session_state.get("forecaster_ok", False):
        st.warning(
            f"⚠️ Model not loaded: `{st.session_state.get('forecaster_err', 'unknown error')}`  \n"
            "Place `lstm_model.keras` in the same directory as `app.py` and restart."
        )
    else:
        current_ppm = data["no2"]       if data else 0.08
        current_ts  = data["timestamp"] if data else time.time()

        cache     = st.session_state.forecast_cache
        elapsed   = time.time() - st.session_state.forecast_ts
        ppm_drift = abs(current_ppm - cache[0]["ppm"]) if cache else 999

        if cache is None or elapsed > FORECAST_TTL or ppm_drift > 0.05:
            with st.spinner("Running LSTM forecast…"):
                try:
                    all_6h = st.session_state.forecaster.forecast(
                        current_ppm=current_ppm,
                        current_ts=current_ts,
                        hours=6,
                    )
                    st.session_state.forecast_cache = all_6h
                    st.session_state.forecast_ts    = time.time()
                except Exception as e:
                    st.error(f"Forecast error: {e}")
                    all_6h = None
        else:
            all_6h = cache

        if all_6h:
            next_3h = all_6h[:3]
            cols = st.columns(3)
            for col, entry in zip(cols, next_3h):
                with col:
                    st.markdown(render_forecast_card(entry), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            chart_rows = []
            if data:
                chart_rows.append({
                    "Time": datetime.fromtimestamp(current_ts).strftime("%H:%M"),
                    "AQI":  data["aqi"],
                })
            for entry in next_3h:
                chart_rows.append({
                    "Time": entry["timestamp"].strftime("%H:%M"),
                    "AQI":  entry["aqi"],
                })
            df_chart = pd.DataFrame(chart_rows).set_index("Time")
            st.line_chart(df_chart, height=160)

            last_run = datetime.fromtimestamp(st.session_state.forecast_ts).strftime("%H:%M:%S")
            st.caption(
                f"Model last run at {last_run} · "
                f"refreshes every {FORECAST_TTL // 60} min "
                f"or when NO₂ shifts by > 0.05 ppm"
            )

    st.markdown("---")

    # History
    history = receiver.get_data_history()
    if len(history) >= 2:
        st.markdown("### 📈 Sensor History (last 50 readings)")
        df = pd.DataFrame(history)
        df["time"] = pd.to_datetime(df["timestamp"], unit="s").dt.strftime("%H:%M:%S")
        df = df.set_index("time")
        tab1, tab2, tab3 = st.tabs(["AQI", "NO₂ ppm", "Temp & Humidity"])
        with tab1: st.line_chart(df[["aqi"]])
        with tab2: st.line_chart(df[["no2"]])
        with tab3: st.line_chart(df[["temp", "hum"]])

live_panel()
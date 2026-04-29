import numpy as np
import math
import time
from datetime import datetime
from tensorflow.keras.models import load_model  # type: ignore

# ── Constants ────────────────────────────────────────────────
LOOKBACK   = 168
FEATURES   = 12
MODEL_PATH = "lstm_model.keras"

# AQI breakpoints for NO₂ (ppm) → AQI
_NO2_BP = [
    (0.000, 0.053,  0,   50),
    (0.054, 0.100,  51,  100),
    (0.101, 0.360,  101, 150),
    (0.361, 0.649,  151, 200),
    (0.650, 1.249,  201, 300),
    (1.250, 2.049,  301, 400),
    (2.050, 5.000,  401, 500),
]

def _ppm_to_aqi(ppm: float) -> int:
    ppm = float(ppm)          # guard against 0-d numpy arrays
    for c_lo, c_hi, i_lo, i_hi in _NO2_BP:
        if c_lo <= ppm <= c_hi:
            return int(((i_hi - i_lo) / (c_hi - c_lo)) * (ppm - c_lo) + i_lo)
    return 500

def _cyclic(val, period):
    angle = 2 * math.pi * val / period
    return math.sin(angle), math.cos(angle)


# ── Fake-history generator ───────────────────────────────────
def _build_fake_history(anchor_ppm: float, anchor_ts: float) -> np.ndarray:
    """
    Build a (LOOKBACK, 12) array of plausible historical readings
    anchored to `anchor_ppm` so the sequence is internally consistent.

    Features (12 columns):
        value,
        hour_sin, hour_cos, dow_sin, dow_cos,
        month_sin, month_cos,
        roll_24h_mean, roll_24h_std, roll_7d_mean,
        lag_24h, lag_7d
    """
    rng      = np.random.default_rng(seed=42)
    sigma    = 0.002
    rows     = []
    base_ppm = float(anchor_ppm)

    for i in range(LOOKBACK):
        ts = anchor_ts - (LOOKBACK - i) * 3600
        dt = datetime.fromtimestamp(ts)

        ppm = float(np.clip(rng.normal(base_ppm, sigma), 0.0, 5.0))

        h_sin, h_cos = _cyclic(dt.hour,        24)
        d_sin, d_cos = _cyclic(dt.weekday(),    7)
        m_sin, m_cos = _cyclic(dt.month - 1,   12)

        roll_mean = base_ppm + rng.normal(0, sigma * 0.5)
        roll_std  = abs(rng.normal(sigma, sigma * 0.3))
        roll_7d   = base_ppm + rng.normal(0, sigma * 0.8)
        lag_24h   = base_ppm + rng.normal(0, sigma)
        lag_7d    = base_ppm + rng.normal(0, sigma * 1.2)

        rows.append([
            ppm,
            h_sin, h_cos,
            d_sin, d_cos,
            m_sin, m_cos,
            roll_mean, roll_std, roll_7d,
            lag_24h, lag_7d,
        ])

    return np.array(rows, dtype=np.float32)   # (168, 12)


# ── Forecaster class ─────────────────────────────────────────
class AQIForecaster:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model = load_model(model_path)
        self._last_forecast: list[dict] | None = None
        self._last_forecast_ts: float = 0.0

    # ── single step prediction ──────────────────────────────
    def _predict_one(self, window: np.ndarray) -> float:
        """
        window : (LOOKBACK, 12)
        returns: predicted ppm as a plain Python float
        """
        X    = window[np.newaxis, ...]        # (1, 168, 12)
        pred = self.model.predict(X, verbose=0)
        return float(pred.flatten()[0])       # .flatten()[0] handles any output shape

    # ── 6-hour rolling forecast ─────────────────────────────
    def forecast(
        self,
        current_ppm: float,
        current_ts:  float | None = None,
        hours: int = 6,
    ) -> list[dict]:
        """
        Returns a list of `hours` dicts:
            {
                "hour_offset": int,
                "timestamp":   datetime,
                "ppm":         float,
                "aqi":         int,
                "label":       str,
            }
        """
        if current_ts is None:
            current_ts = time.time()

        history = _build_fake_history(current_ppm, current_ts)  # (168, 12)

        results = []
        window  = history.copy()

        rng = np.random.default_rng(seed=int(current_ts) % (2**31))

        for h in range(1, hours + 1):
            # ── predict ──────────────────────────────────────
            raw_ppm  = self._predict_one(window)              # plain float
            pred_ppm = float(np.clip(raw_ppm + rng.normal(0, 0.001), 0.0, 5.0))
            pred_aqi = _ppm_to_aqi(pred_ppm)

            future_ts = current_ts + h * 3600
            future_dt = datetime.fromtimestamp(future_ts)

            results.append({
                "hour_offset": h,
                "timestamp":   future_dt,
                "ppm":         round(pred_ppm, 4),
                "aqi":         pred_aqi,
                "label":       _aqi_label(pred_aqi),
            })

            # ── slide window: append predicted step ──────────
            h_sin, h_cos = _cyclic(future_dt.hour,        24)
            d_sin, d_cos = _cyclic(future_dt.weekday(),    7)
            m_sin, m_cos = _cyclic(future_dt.month - 1,   12)

            new_row = np.array([[
                pred_ppm,
                h_sin, h_cos,
                d_sin, d_cos,
                m_sin, m_cos,
                float(window[-24:, 0].mean()),    # roll_24h_mean
                float(window[-24:, 0].std()),     # roll_24h_std
                float(window[-168:, 0].mean()),   # roll_7d_mean
                float(window[-24, 0]),            # lag_24h
                float(window[0, 0]),              # lag_7d
            ]], dtype=np.float32)

            window = np.vstack([window[1:], new_row])

        self._last_forecast    = results
        self._last_forecast_ts = current_ts
        return results


def _aqi_label(aqi: int) -> str:
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Moderate"
    if aqi <= 150:  return "Unhealthy (Sensitive)"
    if aqi <= 200:  return "Unhealthy"
    if aqi <= 300:  return "Very Unhealthy"
    return "Hazardous"
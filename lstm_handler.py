import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
import time

class LSTMForecaster:
    def __init__(self, model_path="lstm_model.keras"):
        self.model = load_model(model_path)

        # store last 168 steps (same as LOOKBACK)
        self.window = []
        self.window_size = 168

    def add_data(self, temp, hum, no2, aqi):
        """Add new sensor reading"""
        row = [temp, hum, no2, aqi]

        self.window.append(row)

        if len(self.window) > self.window_size:
            self.window.pop(0)

    def build_input(self):
        """Convert window → LSTM input"""
        if len(self.window) < self.window_size:
            return None

        return np.array(self.window).reshape(1, self.window_size, 4)

    def predict_24h(self):
        """Predict next 24 hours AQI"""
        X = self.build_input()

        if X is None:
            return None

        pred = self.model.predict(X, verbose=0)[0]

        return pred
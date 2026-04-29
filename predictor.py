import numpy as np
import tensorflow as tf
from datetime import datetime, timedelta
import pandas as pd

class AQIPredictor:
    def __init__(self, model_path="lstm_model.keras"):
        try:
            self.model = tf.keras.models.load_model(model_path)
            self.is_loaded = True
            print("LSTM model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.is_loaded = False
        
        # Store historical data for predictions (last 24 readings)
        self.history = []
        self.max_history = 24  # Assuming you need 24 hours of history
    
    def add_data_point(self, temp, hum, no2, aqi):
        """Add new data point to history"""
        self.history.append({
            'timestamp': datetime.now(),
            'temp': temp,
            'hum': hum,
            'no2': no2,
            'aqi': aqi
        })
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def prepare_sequence(self, lookback=24):
        """Prepare sequence for LSTM prediction"""
        if len(self.history) < lookback:
            return None
        
        # Get last 'lookback' data points
        recent = self.history[-lookback:]
        
        # Create feature array (temp, hum, no2, aqi)
        features = np.array([[d['temp'], d['hum'], d['no2'], d['aqi']] 
                            for d in recent])
        
        # Reshape for LSTM: (samples, timesteps, features)
        return features.reshape(1, lookback, 4)
    
    def predict_next_12_hours(self):
        """Predict AQI for next 12 hours"""
        if not self.is_loaded:
            return None
        
        # Get sequence for prediction
        sequence = self.prepare_sequence()
        if sequence is None:
            return None
        
        predictions = []
        current_sequence = sequence.copy()
        
        # Predict hour by hour (assuming model predicts next hour)
        for hour in range(12):
            try:
                # Predict next hour
                next_aqi = self.model.predict(current_sequence, verbose=0)[0][0]
                predictions.append(next_aqi)
                
                # Update sequence with prediction (for multi-step forecasting)
                # This assumes you need to update the sequence with the prediction
                new_step = current_sequence[0, -1, :].copy()
                new_step[-1] = next_aqi  # Update AQI value
                
                # Shift sequence and add new prediction
                current_sequence = np.roll(current_sequence, -1, axis=1)
                current_sequence[0, -1, :] = new_step
                
            except Exception as e:
                print(f"Prediction error at hour {hour+1}: {e}")
                return None
        
        return predictions
    
    def get_prediction_data(self):
        """Get formatted prediction data"""
        predictions = self.predict_next_12_hours()
        
        if predictions is None:
            return None
        
        # Create timestamps for next 12 hours
        start_time = datetime.now()
        timestamps = [start_time + timedelta(hours=i+1) for i in range(12)]
        
        # Create prediction results
        results = []
        for i, (timestamp, aqi) in enumerate(zip(timestamps, predictions)):
            # Categorize AQI
            if aqi <= 50:
                category = "Good"
                color = "🟢"
            elif aqi <= 100:
                category = "Moderate"
                color = "🟡"
            elif aqi <= 150:
                category = "Unhealthy for Sensitive Groups"
                color = "🟠"
            elif aqi <= 200:
                category = "Unhealthy"
                color = "🔴"
            elif aqi <= 300:
                category = "Very Unhealthy"
                color = "🟣"
            else:
                category = "Hazardous"
                color = "⚫"
            
            results.append({
                'hour': i+1,
                'timestamp': timestamp.strftime("%H:%M"),
                'aqi': int(round(aqi)),
                'category': category,
                'color': color
            })
        
        return results
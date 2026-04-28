from math import atan2, cos, radians, sin, sqrt
from typing import Iterable

from .schemas import RoutePoint


def calculate_aqi(
    pm25: float,
    pm10: float,
    gas_ppm: float = 0.0,
    temperature_c: float = 0.0,
    humidity_percent: float = 0.0,
) -> int:
    # Lightweight AQI approximation for hackathon/demo use.
    particulate_score = (pm25 * 1.6) + (pm10 * 0.5)
    gas_score = gas_ppm * 0.35
    weather_penalty = max(0.0, (temperature_c - 35) * 0.8) + max(0.0, (humidity_percent - 75) * 0.5)
    score = particulate_score + gas_score + weather_penalty
    return max(0, int(round(score)))


def classify_aqi_level(aqi: int) -> str:
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    return "Poor"


def haversine_km(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    r = 6371
    d_lat = radians(b_lat - a_lat)
    d_lng = radians(b_lng - a_lng)
    aa = sin(d_lat / 2) ** 2 + cos(radians(a_lat)) * cos(radians(b_lat)) * sin(d_lng / 2) ** 2
    c = 2 * atan2(sqrt(aa), sqrt(1 - aa))
    return r * c


def route_exposure_score(route_points: list[RoutePoint], sensor_rows: Iterable) -> int:
    total = 0.0
    if not route_points:
        return 0

    sensors = list(sensor_rows)
    if not sensors:
        return 0

    for sensor in sensors:
        min_distance = min(
            haversine_km(point.lat, point.lng, sensor.lat, sensor.lng) for point in route_points
        )
        total += sensor.aqi / (1 + (min_distance * 4))

    return int(round(total))

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class SensorReadingCreate(BaseModel):
    sensor_id: str
    location_name: str
    lat: float
    lng: float
    gas_ppm: float = Field(default=0, ge=0)
    temperature_c: float = Field(default=0)
    humidity_percent: float = Field(default=0, ge=0, le=100)
    pm25: float = Field(default=0, ge=0)
    pm10: float = Field(default=0, ge=0)
    no2: float = Field(default=0, ge=0)
    o3: float = Field(default=0, ge=0)
    timestamp: datetime | None = None


class SensorReadingOut(BaseModel):
    id: int
    sensor_id: str
    location_name: str
    lat: float
    lng: float
    gas_ppm: float
    temperature_c: float
    humidity_percent: float
    pm25: float
    pm10: float
    no2: float
    o3: float
    aqi: int
    created_at: datetime

    class Config:
        from_attributes = True


class HotspotOut(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    aqi: int
    level: str


class AlertOut(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    time: str


class RoutePoint(BaseModel):
    lat: float
    lng: float


class RouteScoreRequest(BaseModel):
    route_points: List[RoutePoint]


class RouteScoreResponse(BaseModel):
    exposure: int

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sensor_id: Mapped[str] = mapped_column(String(100), index=True)
    location_name: Mapped[str] = mapped_column(String(120), index=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    gas_ppm: Mapped[float] = mapped_column(Float, default=0.0)
    temperature_c: Mapped[float] = mapped_column(Float, default=0.0)
    humidity_percent: Mapped[float] = mapped_column(Float, default=0.0)
    pm25: Mapped[float] = mapped_column(Float, default=0.0)
    pm10: Mapped[float] = mapped_column(Float, default=0.0)
    no2: Mapped[float] = mapped_column(Float, default=0.0)
    o3: Mapped[float] = mapped_column(Float, default=0.0)
    aqi: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150))
    message: Mapped[str] = mapped_column(String(300))
    severity: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

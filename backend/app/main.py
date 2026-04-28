from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Alert, SensorReading
from .schemas import (
    AlertOut,
    HotspotOut,
    RouteScoreRequest,
    RouteScoreResponse,
    SensorReadingCreate,
    SensorReadingOut,
)
from .seed import seed_if_empty
from .services import calculate_aqi, classify_aqi_level, route_exposure_score

app = FastAPI(title="AirIQ Sensor Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_if_empty(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "airiq-backend"}


@app.post("/sensor/readings", response_model=SensorReadingOut)
def create_sensor_reading(payload: SensorReadingCreate, db: Session = Depends(get_db)):
    aqi = calculate_aqi(
        payload.pm25,
        payload.pm10,
        payload.gas_ppm,
        payload.temperature_c,
        payload.humidity_percent,
    )
    row = SensorReading(
        sensor_id=payload.sensor_id,
        location_name=payload.location_name,
        lat=payload.lat,
        lng=payload.lng,
        gas_ppm=payload.gas_ppm,
        temperature_c=payload.temperature_c,
        humidity_percent=payload.humidity_percent,
        pm25=payload.pm25,
        pm10=payload.pm10,
        no2=payload.no2,
        o3=payload.o3,
        aqi=aqi,
        created_at=payload.timestamp or datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/sensor/readings/latest", response_model=list[SensorReadingOut])
def latest_sensor_readings(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(SensorReading).order_by(desc(SensorReading.created_at)).limit(limit).all()


@app.get("/aqi/hotspots", response_model=list[HotspotOut])
def get_hotspots(db: Session = Depends(get_db)):
    rows = db.query(SensorReading).order_by(desc(SensorReading.created_at)).limit(200).all()

    latest_by_sensor: dict[str, SensorReading] = {}
    for row in rows:
        if row.sensor_id not in latest_by_sensor:
            latest_by_sensor[row.sensor_id] = row

    hotspots = []
    for row in latest_by_sensor.values():
        hotspots.append(
            HotspotOut(
                id=str(row.id),
                name=row.location_name,
                lat=row.lat,
                lng=row.lng,
                aqi=row.aqi,
                level=classify_aqi_level(row.aqi),
            )
        )

    return hotspots


@app.get("/alerts", response_model=list[AlertOut])
def get_alerts(db: Session = Depends(get_db)):
    rows = db.query(Alert).order_by(desc(Alert.created_at)).limit(20).all()
    return [
        AlertOut(
            id=str(alert.id),
            title=alert.title,
            message=alert.message,
            severity=alert.severity,
            time=f"{max(1, int((datetime.now(timezone.utc) - alert.created_at.replace(tzinfo=timezone.utc)).total_seconds() // 60))} min ago",
        )
        for alert in rows
    ]


@app.post("/route/score", response_model=RouteScoreResponse)
def score_route(payload: RouteScoreRequest, db: Session = Depends(get_db)):
    latest_rows = db.query(SensorReading).order_by(desc(SensorReading.created_at)).limit(200).all()

    latest_by_sensor: dict[str, SensorReading] = {}
    for row in latest_rows:
        if row.sensor_id not in latest_by_sensor:
            latest_by_sensor[row.sensor_id] = row

    exposure = route_exposure_score(payload.route_points, latest_by_sensor.values())
    return RouteScoreResponse(exposure=exposure)

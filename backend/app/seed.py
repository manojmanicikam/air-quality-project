from sqlalchemy.orm import Session

from .models import Alert, SensorReading
from .services import calculate_aqi


def seed_if_empty(db: Session) -> None:
    if db.query(SensorReading).count() > 0:
        return

    seed_rows = [
        ("blr-001", "Indiranagar", 12.9784, 77.6408, 102, 31, 60, 33, 54, 18, 22),
        ("blr-002", "Malleshwaram", 13.0035, 77.5706, 84, 29, 56, 22, 40, 12, 16),
        ("blr-003", "Whitefield", 12.9698, 77.7499, 128, 32, 64, 42, 65, 21, 18),
        ("blr-004", "Electronic City", 12.8456, 77.6603, 175, 35, 68, 69, 95, 29, 14),
        ("blr-005", "Yeshwanthpur", 13.0285, 77.5400, 188, 34, 70, 74, 102, 31, 11),
    ]

    for sensor_id, location_name, lat, lng, gas_ppm, temperature_c, humidity_percent, pm25, pm10, no2, o3 in seed_rows:
        db.add(
            SensorReading(
                sensor_id=sensor_id,
                location_name=location_name,
                lat=lat,
                lng=lng,
                gas_ppm=gas_ppm,
                temperature_c=temperature_c,
                humidity_percent=humidity_percent,
                pm25=pm25,
                pm10=pm10,
                no2=no2,
                o3=o3,
                aqi=calculate_aqi(pm25, pm10, gas_ppm, temperature_c, humidity_percent),
            )
        )

    db.add_all(
        [
            Alert(
                title="AQI Warning - North Bengaluru",
                message="AQI has crossed 150 near industrial corridors. Avoid prolonged outdoor activity.",
                severity="high",
            ),
            Alert(
                title="Dust Storm Advisory",
                message="Dry winds expected after 7 PM. Wear masks and close windows when possible.",
                severity="medium",
            ),
            Alert(
                title="Smoke/Fire Nearby",
                message="Localized smoke plume detected near Electronic City. Route diversions enabled.",
                severity="high",
            ),
        ]
    )

    db.commit()

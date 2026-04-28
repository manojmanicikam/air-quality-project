"use client";

import { useMemo } from "react";
import L, { DivIcon } from "leaflet";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import { aqiMarkers, cityCenter } from "@/data/mockData";
import { AqiLevel } from "@/types/aqi";

const iconSetupComplete = { current: false };

function levelColor(level: AqiLevel) {
  switch (level) {
    case "Good":
      return "#22c55e";
    case "Moderate":
      return "#eab308";
    default:
      return "#ef4444";
  }
}

function buildAqiIcon(level: AqiLevel): DivIcon {
  return L.divIcon({
    html: `<span style="display:inline-block;width:14px;height:14px;border-radius:9999px;background:${levelColor(
      level
    )};box-shadow:0 0 8px ${levelColor(level)};"></span>`,
    className: "aqi-pin",
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

function ensureLeafletDefaults() {
  if (iconSetupComplete.current) return;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  });
  iconSetupComplete.current = true;
}

export function AqiMap() {
  const center = useMemo(() => cityCenter, []);
  ensureLeafletDefaults();

  return (
    <MapContainer center={[center.lat, center.lng]} zoom={11} style={{ width: "100%", height: "100%" }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {aqiMarkers.map((marker) => (
        <Marker
          key={marker.id}
          position={[marker.lat, marker.lng]}
          icon={buildAqiIcon(marker.level)}
        >
          <Popup>
            <strong>{marker.name}</strong>
            <br />
            AQI: {marker.aqi} ({marker.level})
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

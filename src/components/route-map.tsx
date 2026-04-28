"use client";

import { useMemo } from "react";
import { MapContainer, Marker, Polyline, Popup, TileLayer } from "react-leaflet";
import { cityCenter } from "@/data/mockData";

export type LatLngPoint = { lat: number; lng: number };

interface RouteMapProps {
  fastestRoute?: LatLngPoint[];
  cleanestRoute?: LatLngPoint[];
}

function isValidPoint(point: LatLngPoint) {
  return Number.isFinite(point.lat) && Number.isFinite(point.lng);
}

function sanitizePath(path?: LatLngPoint[]) {
  if (!Array.isArray(path)) return [];
  return path.filter(isValidPoint);
}

export function RouteMap({ fastestRoute = [], cleanestRoute = [] }: RouteMapProps) {
  const paths = useMemo(() => {
    const fastest = sanitizePath(fastestRoute);
    const cleanest = sanitizePath(cleanestRoute);
    if (fastest.length < 2) return null;
    return { fastest, cleanest: cleanest.length >= 2 ? cleanest : fastest };
  }, [fastestRoute, cleanestRoute]);

  const center = useMemo(() => {
    if (!paths) return cityCenter;
    return paths.fastest[Math.floor(paths.fastest.length / 2)];
  }, [paths]);

  const mapKey = `${center.lat.toFixed(4)}-${center.lng.toFixed(4)}`;

  return (
    <MapContainer key={mapKey} center={[center.lat, center.lng]} zoom={12} style={{ width: "100%", height: "100%" }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {paths ? (
        <>
          <Marker position={[paths.fastest[0].lat, paths.fastest[0].lng]}>
            <Popup>Start</Popup>
          </Marker>
          <Marker
            position={[
              paths.fastest[paths.fastest.length - 1].lat,
              paths.fastest[paths.fastest.length - 1].lng,
            ]}
          >
            <Popup>Destination</Popup>
          </Marker>
          <Polyline
            positions={paths.fastest.map((point) => [point.lat, point.lng])}
            pathOptions={{ color: "#f59e0b", weight: 5 }}
          />
          <Polyline
            positions={paths.cleanest.map((point) => [point.lat, point.lng])}
            pathOptions={{ color: "#22c55e", weight: 5 }}
          />
        </>
      ) : null}
    </MapContainer>
  );
}

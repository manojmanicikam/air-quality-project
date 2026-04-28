"use client";

import { useMemo } from "react";
import { GoogleMap, MarkerF, useJsApiLoader } from "@react-google-maps/api";
import { aqiMarkers, cityCenter } from "@/data/mockData";
import { LoadingSkeleton } from "@/components/loading-skeleton";

const containerStyle = {
  width: "100%",
  height: "100%",
};

function levelColor(level: "Good" | "Moderate" | "Poor") {
  switch (level) {
    case "Good":
      return "http://maps.google.com/mapfiles/ms/icons/green-dot.png";
    case "Moderate":
      return "http://maps.google.com/mapfiles/ms/icons/yellow-dot.png";
    default:
      return "http://maps.google.com/mapfiles/ms/icons/red-dot.png";
  }
}

export function AqiMap() {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: apiKey,
    id: "airiq-dashboard-map",
  });

  const center = useMemo(() => cityCenter, []);

  if (!apiKey) {
    return (
      <div className="flex h-full items-center justify-center rounded-2xl border border-amber-400/40 bg-amber-500/10 p-6 text-sm text-amber-200">
        Missing NEXT_PUBLIC_GOOGLE_MAPS_API_KEY. Add it in .env.local to view maps.
      </div>
    );
  }

  if (!isLoaded) {
    return <LoadingSkeleton className="h-full w-full" />;
  }

  return (
    <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={11} options={{ disableDefaultUI: true }}>
      {aqiMarkers.map((marker) => (
        <MarkerF
          key={marker.id}
          position={{ lat: marker.lat, lng: marker.lng }}
          title={`${marker.name} AQI ${marker.aqi}`}
          icon={levelColor(marker.level)}
        />
      ))}
    </GoogleMap>
  );
}

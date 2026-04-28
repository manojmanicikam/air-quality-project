"use client";

import { useMemo } from "react";
import { GoogleMap, MarkerF, PolylineF, useJsApiLoader } from "@react-google-maps/api";
import { cityCenter } from "@/data/mockData";
import { LoadingSkeleton } from "@/components/loading-skeleton";

const containerStyle = {
  width: "100%",
  height: "100%",
};

const fastestRoute = [
  { lat: 13.0392, lng: 80.2455 },
  { lat: 13.0542, lng: 80.2545 },
  { lat: 13.0722, lng: 80.2638 },
];

const cleanestRoute = [
  { lat: 13.0392, lng: 80.2455 },
  { lat: 13.0499, lng: 80.2311 },
  { lat: 13.0662, lng: 80.2396 },
  { lat: 13.0722, lng: 80.2638 },
];

export function RouteMap() {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: apiKey,
    id: "airiq-route-map",
  });

  const center = useMemo(() => cityCenter, []);

  if (!apiKey) {
    return (
      <div className="flex h-full items-center justify-center rounded-2xl border border-amber-400/40 bg-amber-500/10 p-6 text-sm text-amber-200">
        Missing NEXT_PUBLIC_GOOGLE_MAPS_API_KEY. Add it in .env.local to view route map.
      </div>
    );
  }

  if (!isLoaded) {
    return <LoadingSkeleton className="h-full w-full" />;
  }

  return (
    <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={12} options={{ disableDefaultUI: true }}>
      <MarkerF position={fastestRoute[0]} label="S" />
      <MarkerF position={fastestRoute[fastestRoute.length - 1]} label="D" />
      <PolylineF path={fastestRoute} options={{ strokeColor: "#f59e0b", strokeWeight: 5 }} />
      <PolylineF path={cleanestRoute} options={{ strokeColor: "#22c55e", strokeWeight: 5 }} />
    </GoogleMap>
  );
}

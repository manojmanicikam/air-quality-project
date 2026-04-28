"use client";

import { useMemo, useState } from "react";
import { GlassCard } from "@/components/glass-card";
import { LatLngPoint, RouteMap } from "@/components/route-map";
import { aqiMarkers } from "@/data/mockData";

interface RouteMetrics {
  durationMin: number;
  exposure: number;
}

interface RouteResultState {
  fastestPath: LatLngPoint[];
  cleanestPath: LatLngPoint[];
  fastestMetrics: RouteMetrics;
  cleanestMetrics: RouteMetrics;
}

const BENGALURU_HINT = "Bengaluru, Karnataka, India";
const DEFAULT_PATH: LatLngPoint[] = [
  { lat: 13.0410, lng: 77.5917 },
  { lat: 13.0208, lng: 77.6213 },
  { lat: 12.9698, lng: 77.7499 },
];

export default function RouteOptimizationPage() {
  const [start, setStart] = useState("Hebbal, Bengaluru");
  const [destination, setDestination] = useState("Whitefield, Bengaluru");
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RouteResultState | null>(null);

  const displayResult = useMemo(() => {
    if (!result) return null;

    const pollutionSaved =
      result.fastestMetrics.exposure > 0
        ? ((result.fastestMetrics.exposure - result.cleanestMetrics.exposure) / result.fastestMetrics.exposure) * 100
        : 0;

    return {
      fastestText: `${result.fastestMetrics.durationMin} min • AQI exposure ${result.fastestMetrics.exposure}`,
      cleanestText: `${result.cleanestMetrics.durationMin} min • AQI exposure ${result.cleanestMetrics.exposure}`,
      savedText: `${Math.max(0, pollutionSaved).toFixed(1)}%`,
    };
  }, [result]);

  async function handleSearch() {
    setSearched(true);
    setLoading(true);
    setError(null);

    try {
      const startPoint = await geocodeBengaluruLocation(start);
      const destinationPoint = await geocodeBengaluruLocation(destination);
      const routes = await fetchOsrmRoutes(startPoint, destinationPoint);

      if (routes.length === 0) {
        throw new Error("No route found between the selected locations.");
      }

      const ranked = routes
        .map((route) => ({
          ...route,
          metrics: {
            durationMin: Math.max(1, Math.round(route.durationSec / 60)),
            exposure: calculateExposure(route.path),
          },
        }))
        .sort((a, b) => a.metrics.exposure - b.metrics.exposure);

      const cleanest = ranked[0];
      const fastest = [...ranked].sort((a, b) => a.durationSec - b.durationSec)[0];

      setResult({
        fastestPath: fastest.path,
        cleanestPath: cleanest.path,
        fastestMetrics: fastest.metrics,
        cleanestMetrics: cleanest.metrics,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to calculate route right now.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const mapFastestPath = result?.fastestPath ?? DEFAULT_PATH;
  const mapCleanestPath = result?.cleanestPath ?? DEFAULT_PATH;

  return (
    <section className="w-full space-y-4">
      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <GlassCard title="Cleanest Route Planner" className="h-fit">
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm text-zinc-300">Start Location</label>
              <input
                value={start}
                onChange={(e) => setStart(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none transition focus:border-emerald-400/60"
                placeholder="Enter start location"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm text-zinc-300">Destination</label>
              <input
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none transition focus:border-emerald-400/60"
                placeholder="Enter destination"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="w-full rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-black transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-emerald-800"
            >
              {loading ? "Finding Routes..." : "Find Cleanest Route"}
            </button>

            {error ? <p className="text-sm text-rose-300">{error}</p> : null}

            {searched && displayResult ? (
              <div className="space-y-2">
                <ResultRow label="Fastest Route" value={displayResult.fastestText} />
                <ResultRow label="Cleanest Route" value={displayResult.cleanestText} />
                <ResultRow label="Pollution Saved %" value={displayResult.savedText} highlight />
              </div>
            ) : (
              <p className="text-sm text-zinc-400">Search a route to compare fastest and cleanest options.</p>
            )}
          </div>
        </GlassCard>

        <GlassCard title="Route Visualization">
          <div className="h-[540px] overflow-hidden rounded-2xl border border-white/10">
            <RouteMap fastestRoute={mapFastestPath} cleanestRoute={mapCleanestPath} />
          </div>
        </GlassCard>
      </div>
    </section>
  );
}

function ResultRow({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-white/10 bg-black/40 px-4 py-3">
      <p className="text-sm text-zinc-300">{label}</p>
      <p className={`text-sm font-semibold ${highlight ? "text-emerald-300" : "text-white"}`}>{value}</p>
    </div>
  );
}

async function geocodeBengaluruLocation(input: string): Promise<LatLngPoint> {
  const query = `${input.trim()}, ${BENGALURU_HINT}`;
  const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(query)}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error("Unable to search locations. Please try again.");
  }

  const data = (await response.json()) as Array<{ lat: string; lon: string }>;
  const first = data[0];
  if (!first) {
    throw new Error(`Location not found: ${input}`);
  }

  return {
    lat: Number(first.lat),
    lng: Number(first.lon),
  };
}

async function fetchOsrmRoutes(start: LatLngPoint, destination: LatLngPoint) {
  const url = `https://router.project-osrm.org/route/v1/driving/${start.lng},${start.lat};${destination.lng},${destination.lat}?overview=full&geometries=geojson&alternatives=true&steps=false`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Routing service is unavailable right now.");
  }

  const data = (await response.json()) as {
    routes?: Array<{ duration: number; geometry: { coordinates: [number, number][] } }>;
  };

  return (data.routes ?? []).map((route) => ({
    durationSec: route.duration,
    path: route.geometry.coordinates.map(([lng, lat]) => ({ lat, lng })),
  }));
}

function calculateExposure(path: LatLngPoint[]) {
  const total = aqiMarkers.reduce((acc, marker) => {
    const distanceKm = minDistanceToPathKm(path, { lat: marker.lat, lng: marker.lng });
    const weighted = marker.aqi / (1 + distanceKm * 4);
    return acc + weighted;
  }, 0);

  return Math.round(total);
}

function minDistanceToPathKm(path: LatLngPoint[], marker: LatLngPoint) {
  let min = Number.POSITIVE_INFINITY;

  for (const point of path) {
    const d = haversineKm(point, marker);
    if (d < min) min = d;
  }

  return Number.isFinite(min) ? min : 100;
}

function haversineKm(a: LatLngPoint, b: LatLngPoint) {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const earthRadiusKm = 6371;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const x =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));
  return earthRadiusKm * c;
}

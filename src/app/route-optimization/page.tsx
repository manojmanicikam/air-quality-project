"use client";

import { useState } from "react";
import { GlassCard } from "@/components/glass-card";
import { RouteMap } from "@/components/route-map";

export default function RouteOptimizationPage() {
  const [start, setStart] = useState("T. Nagar, Chennai");
  const [destination, setDestination] = useState("Marina Beach, Chennai");
  const [searched, setSearched] = useState(false);

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
              onClick={() => setSearched(true)}
              className="w-full rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-black transition hover:bg-emerald-400"
            >
              Find Cleanest Route
            </button>

            {searched ? (
              <div className="space-y-2">
                <ResultRow label="Fastest Route" value="23 min • AQI exposure 121" />
                <ResultRow label="Cleanest Route" value="27 min • AQI exposure 78" />
                <ResultRow label="Pollution Saved %" value="35.5%" highlight />
              </div>
            ) : (
              <p className="text-sm text-zinc-400">Search a route to compare fastest and cleanest options.</p>
            )}
          </div>
        </GlassCard>

        <GlassCard title="Route Visualization">
          <div className="h-[540px] overflow-hidden rounded-2xl border border-white/10">
            <RouteMap />
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

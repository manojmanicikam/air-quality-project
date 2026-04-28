import { AqiMap } from "@/components/aqi-map";
import { GlassCard } from "@/components/glass-card";
import { Sidebar } from "@/components/sidebar";
import { StatCard } from "@/components/stat-card";
import { alertsData, aqiMarkers, dashboardStats } from "@/data/mockData";

export default function DashboardPage() {
  return (
    <section className="w-full space-y-4">
      <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
        <Sidebar />
        <div className="grid gap-4 xl:grid-cols-[1fr_1.1fr]">
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
              {dashboardStats.map((stat) => (
                <StatCard key={stat.label} label={stat.label} value={stat.value} delta={stat.delta} />
              ))}
            </div>

            <GlassCard title="Health Risk Score">
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-4xl font-bold text-emerald-300">72 / 100</p>
                  <p className="mt-2 text-sm text-zinc-300">Sensitive groups should reduce prolonged outdoor activity.</p>
                </div>
                <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-xs text-emerald-300">Moderate Risk</span>
              </div>
            </GlassCard>

            <GlassCard title="AQI Forecast (24h)">
              <div className="flex h-36 items-end gap-2">
                {[45, 60, 55, 72, 88, 75, 68].map((point, idx) => (
                  <div key={idx} className="flex flex-1 flex-col items-center gap-2">
                    <div className="w-full rounded-t bg-emerald-400/70" style={{ height: `${point}%` }} />
                    <span className="text-xs text-zinc-400">{idx * 4}h</span>
                  </div>
                ))}
              </div>
            </GlassCard>

            <GlassCard title="Alerts Panel">
              <div className="space-y-3">
                {alertsData.slice(0, 2).map((alert) => (
                  <div key={alert.id} className="rounded-lg border border-white/10 bg-black/30 p-3">
                    <p className="text-sm font-semibold text-white">{alert.title}</p>
                    <p className="mt-1 text-xs text-zinc-300">{alert.message}</p>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>

          <GlassCard title="Live AQI Hotspots Map" className="min-h-[560px]">
            <div className="h-[500px] overflow-hidden rounded-2xl border border-white/10">
              <AqiMap />
            </div>
            <div className="mt-4 grid gap-2 text-xs text-zinc-300 sm:grid-cols-2">
              {aqiMarkers.map((marker) => (
                <div key={marker.id} className="rounded-lg bg-black/40 px-3 py-2">
                  {marker.name}: AQI {marker.aqi} ({marker.level})
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      </div>
    </section>
  );
}

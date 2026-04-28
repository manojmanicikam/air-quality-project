import { GlassCard } from "@/components/glass-card";
import { alertsData } from "@/data/mockData";

const severityStyles = {
  low: "text-sky-300 bg-sky-500/10 border-sky-400/30",
  medium: "text-amber-300 bg-amber-500/10 border-amber-400/30",
  high: "text-rose-300 bg-rose-500/10 border-rose-400/30",
};

export default function AlertsPage() {
  return (
    <section className="w-full space-y-4">
      <GlassCard title="Real-Time Alerts">
        <p className="mb-4 text-sm text-zinc-300">
          AQI warnings, dust storms, and smoke/fire events are listed here. Data currently uses mock feed and is ready
          for FastAPI integration.
        </p>
        <div className="space-y-3">
          {alertsData.map((alert) => (
            <div
              key={alert.id}
              className={`rounded-xl border p-4 transition hover:-translate-y-0.5 ${severityStyles[alert.severity]}`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold">{alert.title}</p>
                <span className="text-xs opacity-80">{alert.time}</span>
              </div>
              <p className="mt-2 text-sm">{alert.message}</p>
            </div>
          ))}
        </div>
      </GlassCard>
    </section>
  );
}

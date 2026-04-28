import Link from "next/link";
import { StatCard } from "@/components/stat-card";
import { dashboardStats } from "@/data/mockData";

export default function Home() {
  return (
    <section className="hero-grid w-full rounded-3xl border border-white/10 p-6 sm:p-10">
      <div className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="animate-fade-in">
          <p className="text-sm uppercase tracking-[0.3em] text-emerald-300/80">AirIQ Platform</p>
          <h1 className="mt-4 text-4xl font-bold text-white sm:text-5xl">AirIQ Smart City AQI Monitor</h1>
          <p className="mt-4 text-xl text-emerald-300">Breathe Smarter, Travel Cleaner</p>
          <p className="mt-6 max-w-2xl text-zinc-300">
            Hyperlocal air intelligence for cleaner commutes and safer communities. Track AQI hotspots, health
            risk, and smarter routes in one modern dashboard built for smart city operations.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/dashboard"
              className="rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-black transition hover:scale-[1.02] hover:bg-emerald-400"
            >
              Open Dashboard
            </Link>
            <Link
              href="/route-optimization"
              className="rounded-full border border-emerald-400/40 px-6 py-3 text-sm font-semibold text-emerald-300 transition hover:bg-emerald-500/10"
            >
              Find Cleanest Route
            </Link>
          </div>
        </div>
        <div className="grid gap-4">
          {dashboardStats.map((stat) => (
            <StatCard key={stat.label} label={stat.label} value={stat.value} delta={stat.delta} />
          ))}
        </div>
      </div>
    </section>
  );
}

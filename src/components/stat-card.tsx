import { GlassCard } from "@/components/glass-card";

interface StatCardProps {
  label: string;
  value: string;
  delta: string;
}

export function StatCard({ label, value, delta }: StatCardProps) {
  return (
    <GlassCard className="animate-fade-in">
      <p className="text-sm text-zinc-300">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
      <p className="mt-2 text-xs text-emerald-300">{delta}</p>
    </GlassCard>
  );
}

import { ReactNode } from "react";

interface GlassCardProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function GlassCard({ title, children, className = "" }: GlassCardProps) {
  return (
    <section
      className={`rounded-2xl border border-white/10 bg-white/5 p-5 shadow-[0_0_30px_rgba(34,197,94,0.08)] backdrop-blur-xl transition hover:border-emerald-400/30 hover:shadow-[0_0_40px_rgba(34,197,94,0.25)] ${className}`}
    >
      {title ? <h3 className="mb-4 text-lg font-semibold text-white">{title}</h3> : null}
      {children}
    </section>
  );
}

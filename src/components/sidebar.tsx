"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/dashboard", label: "Live Dashboard" },
  { href: "/route-optimization", label: "Cleanest Route" },
  { href: "/alerts", label: "Alert Center" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="h-fit rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
      <p className="mb-3 text-xs uppercase tracking-[0.25em] text-zinc-400">Navigation</p>
      <div className="space-y-2">
        {links.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-lg px-3 py-2 text-sm transition ${
                active
                  ? "bg-emerald-500/20 text-emerald-300"
                  : "text-zinc-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </aside>
  );
}

import Link from "next/link";
import { Sora, Syne } from "next/font/google";
import { ArrowRight } from "lucide-react";

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
});

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
});

const stats = [
  { label: "Signal refresh", value: "12s" },
  { label: "Devices monitored", value: "18" },
  { label: "Trust confidence", value: "93.4%" },
];

const features = [
  "Zero-trust scoring across every device",
  "Attack simulation before real threats hit",
  "Topology-aware threat isolation in one click",
];

export default function LandingPage() {
  return (
    <main
      className={`${sora.variable} ${syne.variable} relative min-h-screen overflow-hidden bg-[#06070b] text-[#f5f5ef]`}
    >
      <div className="lp-ambient pointer-events-none absolute inset-0" />
      <div className="lp-orbit pointer-events-none absolute inset-0" />
      <div className="lp-grain pointer-events-none absolute inset-0" />

      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 pb-12 pt-8 sm:px-10 lg:px-16">
        <header className="lp-reveal flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Sentinel" className="h-8" />
            <p className="font-(--font-syne) text-sm tracking-[0.25em] text-white/70 uppercase">
              Sentinel
            </p>
          </div>
          <Link
            href="/dashboard"
            className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-xs tracking-[0.2em] text-white/80 uppercase transition hover:bg-white/10 hover:text-white"
          >
            Open Dashboard
          </Link>
        </header>

        <section className="my-auto grid gap-14 py-14 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
          <div className="lp-reveal [animation-delay:120ms]">
            <p className="mb-6 text-xs tracking-[0.2em] text-[#d2f6c5]/85 uppercase">
              Visual Cybersecurity Monitoring
            </p>
            <h1 className="max-w-3xl font-[var(--font-syne)] text-5xl leading-[0.95] tracking-[-0.03em] text-[#f7f7f2] sm:text-6xl lg:text-7xl">
              See your network, secure it live.
            </h1>
            <p className="mt-8 max-w-xl text-base leading-relaxed text-white/68 sm:text-lg">
              A minimalist command surface for security teams mapping devices,
              scoring trust in real time, and isolating threats when every
              second matters.
            </p>

            <div className="mt-10 flex flex-wrap gap-4">
              <Link
                href="/dashboard"
                className="group inline-flex items-center gap-2 rounded-full bg-[#e5ffd4] px-6 py-3 text-sm font-medium text-[#111411] transition hover:-translate-y-0.5 hover:bg-[#efffe4]"
              >
                Launch Canvas
                <ArrowRight className="size-4 transition group-hover:translate-x-0.5" />
              </Link>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.04] px-6 py-3 text-sm font-medium text-white/85 transition hover:-translate-y-0.5 hover:bg-white/[0.1]"
              >
                Run Simulation
              </Link>
            </div>
          </div>

          <div className="lp-reveal [animation-delay:260ms] space-y-6">
            <div className="rounded-3xl border border-white/15 bg-black/30 p-6 backdrop-blur-xl">
              <p className="text-xs tracking-[0.16em] text-white/55 uppercase">
                Core Signal
              </p>
              <p className="mt-3 font-[var(--font-syne)] text-3xl leading-tight tracking-[-0.02em]">
                Backdoor persistence detected across 3 nodes.
              </p>
              <p className="mt-4 text-sm text-white/60">
                Trust engine confidence is stable and trending upward over the
                last 20 minutes.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {stats.map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-2xl border border-white/12 bg-white/[0.03] px-4 py-4"
                >
                  <p className="text-2xl font-semibold tracking-tight">
                    {stat.value}
                  </p>
                  <p className="mt-1 text-xs text-white/55">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="lp-reveal [animation-delay:380ms] border-t border-white/10 pt-8">
          <ul className="grid gap-3 text-sm text-white/62 sm:grid-cols-3 sm:gap-6">
            {features.map((feature) => (
              <li key={feature}>{feature}</li>
            ))}
          </ul>
        </section>

        
      </div>
    </main>
  );
}
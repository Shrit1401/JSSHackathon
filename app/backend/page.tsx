import Link from "next/link";
import { Sora, Syne } from "next/font/google";
import {
  ArrowLeft,
  Radio,
  Cpu,
  BarChart3,
  TrendingDown,
  ShieldAlert,
  Bot,
  ShieldCheck,
  Lock,
  Timer,
  Bell,
  ScrollText,
  Network,
  Bomb,
  Search,
  Activity,
  Database,
  GitBranch,
} from "lucide-react";

const sora = Sora({ subsets: ["latin"], variable: "--font-sora" });
const syne = Syne({ subsets: ["latin"], variable: "--font-syne" });

const toc = [
  { id: "architecture", label: "Architecture" },
  { id: "telemetry", label: "Telemetry Ingestion" },
  { id: "features", label: "Feature Engineering" },
  { id: "baseline", label: "Baseline Learning" },
  { id: "drift", label: "Drift Detection" },
  { id: "policy", label: "Policy Engine" },
  { id: "ml", label: "ML Detection" },
  { id: "trust", label: "Trust Scoring" },
  { id: "gated", label: "Baseline Protection" },
  { id: "temporal", label: "Temporal Safeguards" },
  { id: "alerts", label: "Alert System" },
  { id: "timeline", label: "Event Timeline" },
  { id: "topology", label: "Network Topology" },
  { id: "attacks", label: "Attack Simulation" },
  { id: "explain", label: "Explainability" },
];

function StepBadge({ n, color }: { n: number; color: string }) {
  return (
    <span
      className="grid size-11 shrink-0 place-items-center rounded-xl text-xs font-bold tracking-wide"
      style={{
        color,
        background: `${color}18`,
        border: `1px solid ${color}33`,
      }}
    >
      {String(n).padStart(2, "0")}
    </span>
  );
}

function Ic({ children }: { children: React.ReactNode }) {
  return (
    <code
      className="rounded-md border border-white/10 bg-white/[0.06] px-1.5 py-0.5 text-[13px] text-[#d2f6c5]/85"
      style={{ fontFamily: "var(--font-geist-mono), monospace" }}
    >
      {children}
    </code>
  );
}

function CodeBlock({ children, title }: { children: string; title?: string }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-black/40">
      {title && (
        <div className="border-b border-white/[0.06] bg-white/[0.02] px-6 py-3 text-[11px] font-medium tracking-[0.1em] text-white/35 uppercase">
          {title}
        </div>
      )}
      <pre className="overflow-x-auto p-5 text-[13px] leading-[1.7] text-white/70" style={{ fontFamily: "var(--font-geist-mono), monospace" }}>
        <code>{children}</code>
      </pre>
    </div>
  );
}

function Formula({
  children,
  label,
}: {
  children: React.ReactNode;
  label?: string;
}) {
  return (
    <div
      className="relative flex items-center justify-center rounded-2xl border border-white/[0.08] p-8"
      style={{
        background:
          "linear-gradient(135deg, rgba(96,165,250,0.05), rgba(192,132,252,0.05))",
      }}
    >
      <div style={{ fontFamily: "var(--font-geist-mono), monospace" }}>
        {children}
      </div>
      {label && (
        <span className="absolute right-4 top-3 text-[10px] font-medium tracking-[0.12em] text-white/25 uppercase">
          {label}
        </span>
      )}
    </div>
  );
}

function Endpoint({ method, path }: { method: string; path: string }) {
  const isGet = method === "GET";
  return (
    <div className="inline-flex items-center gap-3 rounded-[10px] border border-white/[0.08] bg-black/30 px-4 py-2">
      <span
        className="rounded-[5px] px-2 py-0.5 text-[11px] font-bold tracking-[0.08em]"
        style={{
          fontFamily: "var(--font-geist-mono), monospace",
          color: isGet ? "#34d399" : "#60a5fa",
          background: isGet ? "rgba(52,211,153,0.12)" : "rgba(96,165,250,0.12)",
        }}
      >
        {method}
      </span>
      <span
        className="text-sm text-white/65"
        style={{ fontFamily: "var(--font-geist-mono), monospace" }}
      >
        {path}
      </span>
    </div>
  );
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-white/[0.07] bg-white/[0.02] p-7 backdrop-blur-xl ${className}`}>
      {children}
    </div>
  );
}

function SectionHeader({
  n,
  color,
  icon: Icon,
  title,
  sub,
}: {
  n: number;
  color: string;
  icon: React.ElementType;
  title: string;
  sub: string;
}) {
  return (
    <div className="mb-6 flex gap-4">
      <StepBadge n={n} color={color} />
      <div>
        <h2 className="flex items-center gap-2 text-2xl font-semibold tracking-[-0.02em] text-[#f7f7f2]/95" style={{ fontFamily: "var(--font-syne), system-ui" }}>
          <Icon className="size-5 opacity-50" />
          {title}
        </h2>
        <p className="mt-1 text-sm text-white/45">{sub}</p>
      </div>
    </div>
  );
}

export default function BackendPage() {
  return (
    <main
      className={`${sora.variable} ${syne.variable} relative min-h-screen bg-[#06070b] text-[#f5f5ef]`}
    >
      <div className="lp-ambient pointer-events-none fixed inset-0" />
      <div className="lp-grain pointer-events-none fixed inset-0" />

      <div className="relative z-10">
        {/* ── STICKY HEADER ── */}
        <header className="sticky top-0 z-50 border-b border-white/[0.08] bg-[#06070b]/80 backdrop-blur-2xl">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="flex items-center gap-2 text-sm text-white/60 transition hover:text-white"
              >
                <ArrowLeft className="size-4" />
                Home
              </Link>
              <span className="text-white/20">|</span>
              <p
                className="text-sm tracking-[0.2em] text-white/80 uppercase"
                style={{ fontFamily: "var(--font-syne), system-ui" }}
              >
                Backend Architecture
              </p>
            </div>
            <Link
              href="/dashboard"
              className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-xs tracking-[0.15em] text-white/70 uppercase transition hover:bg-white/10 hover:text-white"
            >
              Open Dashboard
            </Link>
          </div>
        </header>

        {/* ── MAIN LAYOUT ── */}
        <div className="mx-auto max-w-7xl px-6 py-12 lg:grid lg:grid-cols-[220px_1fr] lg:gap-12">
          {/* ── SIDEBAR TOC ── */}
          <aside className="hidden lg:block">
            <nav className="sticky top-24 flex flex-col gap-1">
              {toc.map((item) => (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  className="block rounded-lg px-3 py-2 text-[13px] text-white/40 transition hover:bg-white/[0.04] hover:text-white/80"
                >
                  {item.label}
                </a>
              ))}
            </nav>
          </aside>

          {/* ── CONTENT ── */}
          <article className="flex min-w-0 flex-col gap-16">
            {/* ── HERO ── */}
            <section className="flex flex-col gap-6 pb-4">
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-[#d2f6c5]/20 bg-[#d2f6c5]/[0.08] px-4 py-1.5">
                <Activity className="size-3.5 text-[#d2f6c5]" />
                <span className="text-xs tracking-[0.15em] text-[#d2f6c5]/90 uppercase">
                  System Internals
                </span>
              </div>
              <h1
                className="text-5xl leading-[1.05] tracking-[-0.03em] text-[#f7f7f2] sm:text-6xl"
                style={{ fontFamily: "var(--font-syne), system-ui" }}
              >
                How Sentinel&apos;s backend works
              </h1>
              <p className="max-w-2xl text-lg leading-relaxed text-white/55">
                A deep dive into the trust engine, anomaly detection pipeline,
                and every layer that powers real-time network security scoring
                — from raw telemetry to explainable verdicts.
              </p>
              <div className="flex flex-wrap gap-3 pt-2">
                {["Python", "FastAPI", "scikit-learn", "Redis", "PostgreSQL"].map(
                  (t) => (
                    <span
                      key={t}
                      className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-white/60"
                    >
                      {t}
                    </span>
                  )
                )}
              </div>
            </section>

            {/* ── 01 — ARCHITECTURE OVERVIEW ── */}
            <section id="architecture" className="scroll-mt-20">
              <SectionHeader n={1} color="#a8e6cf" icon={GitBranch} title="Architecture Overview" sub="The full pipeline from device telemetry to trust verdicts." />
              <Card>
                <p className="leading-relaxed text-white/60">
                  Sentinel follows a layered architecture where each stage
                  refines raw device signals into actionable security
                  intelligence. Data flows through five core stages:
                </p>
                <div className="mt-6 flex flex-wrap items-start justify-center gap-2">
                  {[
                    { icon: Radio, label: "Telemetry", desc: "Raw device data" },
                    { icon: Cpu, label: "Features", desc: "Behavior metrics" },
                    { icon: BarChart3, label: "Baseline", desc: "Normal profiles" },
                    { icon: Bot, label: "Detection", desc: "ML + Policy + Drift" },
                    { icon: ShieldCheck, label: "Trust", desc: "Composite score" },
                  ].map((stage, i) => (
                    <div key={stage.label} className="flex items-start gap-2">
                      <div className="flex min-w-[90px] flex-col items-center text-center">
                        <div className="grid size-12 place-items-center rounded-[14px] border border-white/10 bg-white/[0.04] text-white/65">
                          <stage.icon className="size-5" />
                        </div>
                        <p className="mt-2 text-sm font-medium text-white/90">{stage.label}</p>
                        <p className="text-xs text-white/45">{stage.desc}</p>
                      </div>
                      {i < 4 && (
                        <span className="mt-3.5 text-xl text-white/20">→</span>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            </section>

            {/* ── 02 — TELEMETRY INGESTION ── */}
            <section id="telemetry" className="scroll-mt-20">
              <SectionHeader n={2} color="#80d4ff" icon={Radio} title="Telemetry Ingestion" sub="Every device emits structured telemetry events that form our raw signal layer." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  Each network device — cameras, printers, routers, smart TVs —
                  continuously emits telemetry packets. We capture protocol
                  usage, traffic volume, session behavior, and destination
                  patterns into a structured event model.
                </p>
                <CodeBlock title="Telemetry Event Schema">{`{
  "device_id": "camera_1",
  "device_type": "camera",
  "protocol": "RTSP",
  "bytes_sent": 54000,
  "bytes_received": 1200,
  "session_duration": 4.3,
  "packet_count": 420,
  "destination": "internal_nvr",
  "timestamp": 1710000000
}`}</CodeBlock>
                <Endpoint method="POST" path="/telemetry" />
                <p className="text-sm text-white/45">
                  Events are stored in PostgreSQL with time-series indexing.
                  Even during simulation, the ingestion pipeline remains
                  identical to production — ensuring realistic behavior
                  throughout.
                </p>
              </Card>
            </section>

            {/* ── 03 — FEATURE ENGINEERING ── */}
            <section id="features" className="scroll-mt-20">
              <SectionHeader n={3} color="#ffd580" icon={Cpu} title="Feature Engineering Layer" sub="Raw telemetry is noisy. We compute behavioral metrics per device over rolling time windows." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  Rather than feeding raw events into detection models, we
                  aggregate telemetry into meaningful behavioral features per
                  1-minute time window. This dramatically reduces noise and
                  captures the <em>shape</em> of device behavior.
                </p>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {[
                    { metric: "packet_rate", desc: "Packets per minute", example: "120/min" },
                    { metric: "avg_session_duration", desc: "Mean session length", example: "5s" },
                    { metric: "destination_entropy", desc: "Diversity of targets", example: "0.2" },
                    { metric: "protocol_distribution", desc: "Protocol mix ratio", example: "RTSP: 0.95" },
                    { metric: "traffic_volume", desc: "Total bytes transferred", example: "54KB/min" },
                    { metric: "protocol_entropy", desc: "Shannon entropy of protocols", example: "0.2" },
                  ].map((f) => (
                    <div key={f.metric} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                      <code className="text-sm text-[#d2f6c5]">{f.metric}</code>
                      <p className="mt-1 text-xs text-white/50">{f.desc}</p>
                      <p className="mt-2 text-lg font-semibold text-white/90">{f.example}</p>
                    </div>
                  ))}
                </div>
                <CodeBlock title="Computed Feature Vector — camera_1">{`{
  "device": "camera_1",
  "window": "2024-03-10T00:01:00Z",
  "packet_rate": 120,
  "protocol_entropy": 0.2,
  "destination_count": 1,
  "avg_session_duration": 5.0,
  "traffic_volume": 54000
}`}</CodeBlock>
              </Card>
            </section>

            {/* ── 04 — BASELINE LEARNING ── */}
            <section id="baseline" className="scroll-mt-20">
              <SectionHeader n={4} color="#c4b5fd" icon={BarChart3} title="Baseline Learning" sub='Every device type builds a statistical profile of "normal" behavior.' />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  We compute per-device-type baselines by aggregating feature
                  vectors over a learning window. The baseline captures the
                  statistical signature of healthy behavior — mean, standard
                  deviation, and allowed protocol sets. Stored in Redis for
                  sub-millisecond lookups.
                </p>
                <CodeBlock title="Baseline Profile — camera">{`{
  "device_type": "camera",
  "protocols_allowed": ["RTSP", "HTTPS"],
  "packet_rate_mean": 100,
  "packet_rate_std": 30,
  "session_duration_mean": 5.2,
  "session_duration_std": 1.8,
  "destination_entropy": "low",
  "traffic_volume_mean": 48000,
  "traffic_volume_std": 12000
}`}</CodeBlock>
                <div className="flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] px-5 py-4">
                  <Database className="mt-0.5 size-4 shrink-0 text-[#c4b5fd]" />
                  <p className="text-sm text-white/55">
                    Baselines are stored in <Ic>Redis</Ic> for real-time
                    scoring speed, with persistence to <Ic>PostgreSQL</Ic>{" "}
                    for durability. Updated only when the device is trusted
                    (see Step 9 — Gated Learning).
                  </p>
                </div>
              </Card>
            </section>

            {/* ── 05 — DRIFT DETECTION ── */}
            <section id="drift" className="scroll-mt-20">
              <SectionHeader n={5} color="#f87171" icon={TrendingDown} title="Drift Detection" sub="Statistical deviation from baseline using z-score analysis." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  For every incoming feature vector, we compute z-scores
                  against the device type&apos;s baseline. A z-score quantifies
                  how many standard deviations a value sits from the mean —
                  anything beyond ±3σ is flagged as anomalous drift.
                </p>
                <Formula label="Z-Score Formula">
                  <div className="flex items-center gap-3 text-3xl font-light tracking-wide">
                    <span className="text-white/90">z</span>
                    <span className="text-white/40">=</span>
                    <div className="flex flex-col items-center">
                      <span className="border-b border-white/30 px-4 pb-1.5 text-white/90">
                        x − μ
                      </span>
                      <span className="pt-1.5 text-white/90">σ</span>
                    </div>
                  </div>
                </Formula>
                <div className="grid gap-4 sm:grid-cols-3">
                  {[
                    { v: "x", d: "Current observed value" },
                    { v: "μ", d: "Baseline mean" },
                    { v: "σ", d: "Standard deviation" },
                  ].map((item) => (
                    <div key={item.v} className="flex flex-col items-center gap-1.5 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                      <span className="text-2xl font-light text-white/85" style={{ fontFamily: "var(--font-geist-mono), monospace" }}>{item.v}</span>
                      <span className="text-xs text-white/50">{item.d}</span>
                    </div>
                  ))}
                </div>
                <div className="rounded-xl border border-[#f87171]/20 bg-[#f87171]/[0.05] p-5">
                  <p className="text-sm font-medium text-[#f87171]">
                    Anomaly threshold: |z| &gt; 3
                  </p>
                  <div className="mt-3 space-y-1 text-sm text-white/55">
                    <p>Camera baseline <Ic>packet_rate</Ic> = 100</p>
                    <p>Current observed = 420</p>
                    <p className="pt-1 text-white/70">
                      z = (420 − 100) / 30 ={" "}
                      <span className="font-semibold text-[#f87171]">10.6</span>{" "}
                      — highly anomalous
                    </p>
                  </div>
                </div>
              </Card>
            </section>

            {/* ── 06 — POLICY ENGINE ── */}
            <section id="policy" className="scroll-mt-20">
              <SectionHeader n={6} color="#fb923c" icon={ShieldAlert} title="Policy Engine" sub="Hard rules that catch obvious violations with high confidence." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  While ML models capture subtle anomalies, the policy engine
                  enforces deterministic rules based on known device
                  constraints. Policy violations produce high-confidence alerts
                  that require no statistical interpretation.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/[0.08]">
                        <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-[0.1em] text-white/35 uppercase">Device Type</th>
                        <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-[0.1em] text-white/35 uppercase">Forbidden Action</th>
                        <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-[0.1em] text-white/35 uppercase">Rationale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ["Camera", "SSH connections", "Cameras have no legitimate SSH use"],
                        ["Printer", "Internet access", "Printers should only communicate internally"],
                        ["Router", "FTP traffic", "Routers should not serve files"],
                        ["IoT Hub", "External DNS queries", "Hub should use internal DNS only"],
                      ].map(([dev, action, why]) => (
                        <tr key={dev} className="border-b border-white/[0.04] transition hover:bg-white/[0.02]">
                          <td className="px-4 py-3 text-white/60">{dev}</td>
                          <td className="px-4 py-3 text-white/60">{action}</td>
                          <td className="px-4 py-3 text-white/60">{why}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <CodeBlock title="Policy Violation Example">{`{
  "device": "printer_1",
  "protocol": "FTP",
  "destination": "203.0.113.42",
  "destination_type": "external",
  "policy_violation": true,
  "rule": "PRINTER_NO_EXTERNAL",
  "confidence": 0.98
}`}</CodeBlock>
              </Card>
            </section>

            {/* ── 07 — ML ANOMALY DETECTION ── */}
            <section id="ml" className="scroll-mt-20">
              <SectionHeader n={7} color="#34d399" icon={Bot} title="ML Anomaly Detection" sub="Isolation Forest for unsupervised anomaly scoring." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  We use <strong className="text-white/80">Isolation Forest</strong> from
                  scikit-learn — an unsupervised algorithm that isolates
                  anomalies by recursively partitioning feature space. Anomalous
                  points require fewer splits to isolate, yielding shorter
                  average path lengths.
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5">
                    <p className="text-[11px] font-medium tracking-[0.12em] text-white/40 uppercase">
                      Input Features
                    </p>
                    <ul className="mt-3 flex flex-col gap-2">
                      {[
                        "packet_rate",
                        "session_duration",
                        "bytes_sent",
                        "bytes_received",
                        "destination_entropy",
                        "protocol_entropy",
                      ].map((f) => (
                        <li key={f} className="flex items-center gap-2 text-sm text-white/65">
                          <span className="size-1.5 rounded-full bg-[#34d399]/60" />
                          <code>{f}</code>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5">
                    <p className="text-[11px] font-medium tracking-[0.12em] text-white/40 uppercase">
                      Output
                    </p>
                    <div className="mt-3 flex flex-col gap-4">
                      <div>
                        <code className="text-[#34d399]">anomaly_score</code>
                        <p className="mt-1 text-sm text-white/50">Continuous value from 0 to 1</p>
                      </div>
                      <div className="flex gap-4">
                        <div className="flex-1 rounded-lg bg-[#34d399]/10 p-3 text-center">
                          <p className="text-2xl font-semibold text-[#34d399]">0</p>
                          <p className="text-xs text-white/40">Normal</p>
                        </div>
                        <div className="flex-1 rounded-lg bg-[#f87171]/10 p-3 text-center">
                          <p className="text-2xl font-semibold text-[#f87171]">1</p>
                          <p className="text-xs text-white/40">Suspicious</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-4 pt-2">
                  <h3 className="text-sm font-medium tracking-[0.1em] text-white/50 uppercase">
                    Model Training Results
                  </h3>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white/[0.06] bg-black/30 p-4">
                      <img
                        src="/chart1.png"
                        alt="Isolation Forest training — anomaly score distribution"
                        className="w-full rounded-lg"
                      />
                      <p className="mt-3 text-center text-xs text-white/40">
                        Anomaly score distribution across device fleet
                      </p>
                    </div>
                    <div className="rounded-2xl border border-white/[0.06] bg-black/30 p-4">
                      <img
                        src="/chart2.png"
                        alt="Isolation Forest training — feature importance"
                        className="w-full rounded-lg"
                      />
                      <p className="mt-3 text-center text-xs text-white/40">
                        Feature importance and decision boundaries
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            </section>

            {/* ── 08 — TRUST SCORE ENGINE ── */}
            <section id="trust" className="scroll-mt-20">
              <SectionHeader n={8} color="#60a5fa" icon={ShieldCheck} title="Trust Score Engine" sub="A composite score combining all detection signals into a single trust metric." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  The trust score is the single number that drives the entire
                  frontend visualization — node colors, risk badges, and alert
                  priority. It combines ML anomaly scores, statistical drift,
                  and policy violations into one clamped metric.
                </p>
                <Formula label="Trust Score Computation">
                  <div className="flex flex-col gap-2 text-lg font-light tracking-wide">
                    <div className="flex items-center gap-2">
                      <span className="text-white/90">trust</span>
                      <span className="text-white/40">=</span>
                      <span className="text-[#60a5fa]">100</span>
                    </div>
                    <div className="flex items-center gap-2 text-[#f87171]">
                      <span className="text-white/40">−</span>
                      <span>anomaly_score × 40</span>
                    </div>
                    <div className="flex items-center gap-2 text-[#fb923c]">
                      <span className="text-white/40">−</span>
                      <span>drift_score × 20</span>
                    </div>
                    <div className="flex items-center gap-2 text-[#c084fc]">
                      <span className="text-white/40">−</span>
                      <span>policy_violations × 30</span>
                    </div>
                  </div>
                </Formula>
                <div className="flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] px-5 py-4">
                  <ShieldCheck className="mt-0.5 size-4 shrink-0 text-[#60a5fa]" />
                  <p className="text-sm text-white/55">
                    Result is clamped to <Ic>0 ≤ trust ≤ 100</Ic>
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/[0.08]">
                        <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-[0.1em] text-white/35 uppercase">Trust Range</th>
                        <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-[0.1em] text-white/35 uppercase">Risk Level</th>
                        <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-[0.1em] text-white/35 uppercase">Node Color</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { range: "80 – 100", level: "SAFE", color: "#34d399", cname: "Green" },
                        { range: "60 – 80", level: "LOW", color: "#fbbf24", cname: "Yellow" },
                        { range: "40 – 60", level: "MEDIUM", color: "#fb923c", cname: "Orange" },
                        { range: "< 40", level: "HIGH", color: "#f87171", cname: "Red" },
                      ].map((r) => (
                        <tr key={r.level} className="border-b border-white/[0.04] transition hover:bg-white/[0.02]">
                          <td className="px-4 py-3 text-white/60">{r.range}</td>
                          <td className="px-4 py-3">
                            <span
                              className="inline-block rounded-full px-2.5 py-0.5 text-[11px] font-bold tracking-[0.08em]"
                              style={{ color: r.color, background: `${r.color}1f` }}
                            >
                              {r.level}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="flex items-center gap-2 text-white/60">
                              <span className="size-3 rounded-full" style={{ background: r.color }} />
                              {r.cname}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </section>

            {/* ── 09 — GATED LEARNING ── */}
            <section id="gated" className="scroll-mt-20">
              <SectionHeader n={9} color="#e879f9" icon={Lock} title="Baseline Protection — Gated Learning" sub="Prevent attackers from poisoning the model by corrupting baselines." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  A sophisticated attacker might slowly shift a device&apos;s
                  behavior to make malicious activity look &quot;normal&quot;
                  over time — poisoning the baseline. Sentinel prevents this
                  with <strong className="text-white/80">gated learning</strong>: baselines
                  are only updated when the device&apos;s trust score exceeds a
                  confidence threshold.
                </p>
                <Formula label="Gated Baseline Update Rule">
                  <div className="flex flex-col gap-3 text-lg font-light tracking-wide">
                    <div className="flex items-center gap-3">
                      <span className="text-white/50">if</span>
                      <span className="text-[#34d399]">trust_score &gt; 85</span>
                      <span className="text-white/50">→</span>
                      <span className="text-white/90">update_baseline()</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-white/50">else</span>
                      <span className="text-white/50">→</span>
                      <span className="text-[#f87171]">freeze_baseline()</span>
                    </div>
                  </div>
                </Formula>
                <div
                  className="flex items-start gap-4 rounded-xl border border-white/[0.08] p-5"
                  style={{ background: "linear-gradient(135deg, rgba(232,121,249,0.04), rgba(96,165,250,0.04))" }}
                >
                  <Lock className="mt-0.5 size-5 shrink-0 text-[#e879f9]" />
                  <div>
                    <p className="text-sm font-medium text-white/80">
                      Why this matters
                    </p>
                    <p className="mt-1 text-sm text-white/50">
                      Without gated learning, an attacker could slowly increase
                      traffic over days — each increment appearing as a small,
                      acceptable deviation — until the baseline absorbs the
                      malicious pattern as &quot;normal&quot;. Gated learning
                      ensures only verified-clean behavior shapes future
                      baselines.
                    </p>
                  </div>
                </div>
              </Card>
            </section>

            {/* ── 10 — TEMPORAL SAFEGUARDS ── */}
            <section id="temporal" className="scroll-mt-20">
              <SectionHeader n={10} color="#fbbf24" icon={Timer} title="Temporal Safeguards" sub="Sustained anomaly windows prevent false alarms from transient spikes." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  A single anomalous reading could be network jitter or a
                  firmware update. To avoid false positives, Sentinel requires
                  drift to persist across multiple consecutive time windows
                  before escalating to an alert.
                </p>
                <div className="flex flex-col pl-2">
                  {["Window 1", "Window 2", "Window 3"].map((w, i) => (
                    <div key={w} className="relative flex items-center gap-4 py-3">
                      <div className="size-3 shrink-0 rounded-full border-2 border-[#fbbf24] bg-[#fbbf24]/20" />
                      <div>
                        <p className="text-sm font-medium text-white/80">{w}</p>
                        <p className="text-xs text-[#fbbf24]">drift detected</p>
                      </div>
                      {i < 2 && (
                        <div className="absolute bottom-0 left-[7px] top-[calc(0.75rem+12px)] w-0.5 bg-[#fbbf24]/20" />
                      )}
                    </div>
                  ))}
                  <div className="relative flex items-center gap-4 py-3">
                    <div className="size-3 shrink-0 rounded-full border-2 border-[#f87171] bg-[#f87171]/30 shadow-[0_0_12px_rgba(248,113,113,0.3)]" />
                    <div>
                      <p className="text-sm font-medium text-[#f87171]">Alert Triggered</p>
                      <p className="text-xs text-white/50">3 consecutive windows confirmed</p>
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] px-5 py-4">
                  <Timer className="mt-0.5 size-4 shrink-0 text-[#fbbf24]" />
                  <p className="text-sm text-white/55">
                    Configurable window size (default: 60s) and consecutive
                    threshold (default: 3 windows). Tunable per device type.
                  </p>
                </div>
              </Card>
            </section>

            {/* ── 11 — ALERT SYSTEM ── */}
            <section id="alerts" className="scroll-mt-20">
              <SectionHeader n={11} color="#f87171" icon={Bell} title="Alert System" sub="Structured, severity-ranked alerts with full context." />
              <Card className="flex flex-col gap-6">
                <CodeBlock title="Alert Object">{`{
  "id": "alert_00482",
  "type": "POLICY_VIOLATION",
  "device": "camera_1",
  "severity": "HIGH",
  "reason": "SSH connection attempt detected",
  "details": {
    "protocol": "SSH",
    "destination": "10.0.0.45",
    "baseline_protocols": ["RTSP", "HTTPS"]
  },
  "timestamp": 1710000000,
  "acknowledged": false
}`}</CodeBlock>
                <Endpoint method="GET" path="/alerts" />
                <p className="text-sm text-white/45">
                  Alerts are ranked by severity and surfaced in the dashboard&apos;s
                  real-time alert panel. Each alert links back to the device,
                  the triggering event, and the detection layer that flagged it.
                </p>
              </Card>
            </section>

            {/* ── 12 — EVENT TIMELINE ── */}
            <section id="timeline" className="scroll-mt-20">
              <SectionHeader n={12} color="#94a3b8" icon={ScrollText} title="Event Timeline" sub="Full audit trail of everything that happens on the network." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  Every significant event is logged chronologically — device
                  joins, traffic spikes, policy violations, attack detections,
                  and trust score changes. This provides a forensic timeline for
                  incident response.
                </p>
                <div className="flex flex-col gap-1">
                  {[
                    { time: "00:01:12", event: "Device joined", detail: "camera_1 connected via RTSP", color: "#60a5fa" },
                    { time: "00:04:38", event: "Traffic spike", detail: "camera_1 packet_rate 420/min (baseline: 100)", color: "#fbbf24" },
                    { time: "00:04:39", event: "Drift detected", detail: "z-score 10.6 on packet_rate", color: "#fb923c" },
                    { time: "00:05:02", event: "Policy violation", detail: "SSH protocol observed on camera_1", color: "#f87171" },
                    { time: "00:05:03", event: "Trust updated", detail: "camera_1: 87% → 23%", color: "#f87171" },
                  ].map((e) => (
                    <div key={e.time + e.event} className="flex items-center gap-3 rounded-lg px-3 py-2 transition hover:bg-white/[0.03]">
                      <code className="shrink-0 text-xs text-white/30" style={{ fontFamily: "var(--font-geist-mono), monospace" }}>{e.time}</code>
                      <span className="size-2 shrink-0 rounded-full" style={{ background: e.color }} />
                      <div>
                        <span className="text-sm text-white/75">{e.event}</span>
                        <span className="ml-2 text-xs text-white/40">{e.detail}</span>
                      </div>
                    </div>
                  ))}
                </div>
                <Endpoint method="GET" path="/events" />
              </Card>
            </section>

            {/* ── 13 — NETWORK TOPOLOGY ── */}
            <section id="topology" className="scroll-mt-20">
              <SectionHeader n={13} color="#2dd4bf" icon={Network} title="Network Topology Engine" sub="Structured topology instead of random graphs." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  The topology engine models the actual hierarchical structure
                  of the network. Devices are organized by their physical and
                  logical relationships — not scattered randomly. This enables
                  topology-aware threat detection and lateral movement tracking.
                </p>
                <CodeBlock title="Network Hierarchy">{`Router
 └─ Gateway
     └─ IoT Hub
         ├─ Camera (RTSP)
         ├─ Printer (IPP)
         ├─ Smart TV (HTTPS)
         ├─ Laptop (mixed)
         └─ Thermostat (MQTT)`}</CodeBlock>
                <Endpoint method="GET" path="/network-map" />
                <p className="text-sm text-white/45">
                  The frontend renders this as an interactive force-directed
                  graph using ReactFlow with dagre auto-layout. Edge thickness
                  represents traffic volume, and node colors reflect real-time
                  trust scores.
                </p>
              </Card>
            </section>

            {/* ── 14 — ATTACK SIMULATION ── */}
            <section id="attacks" className="scroll-mt-20">
              <SectionHeader n={14} color="#f472b6" icon={Bomb} title="Attack Simulation Engine" sub="Simulate real-world attacks and watch the system respond." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  The simulation engine injects realistic attack patterns into
                  the telemetry pipeline. This lets you stress-test every
                  detection layer live during a demo.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/[0.08]">
                        <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-[0.1em] text-white/35 uppercase">Attack Type</th>
                        <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-[0.1em] text-white/35 uppercase">Telemetry Effect</th>
                        <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-[0.1em] text-white/35 uppercase">Expected Detection</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ["Botnet recruitment", "High UDP traffic, many destinations", "ML + Drift"],
                        ["Data exfiltration", "Massive outbound bytes", "Drift + Policy"],
                        ["SSH backdoor", "New SSH protocol on non-SSH device", "Policy violation"],
                        ["Lateral movement", "New internal destinations", "Entropy spike"],
                        ["DDoS participation", "Extreme packet rate", "Drift + ML"],
                      ].map(([atk, effect, detect]) => (
                        <tr key={atk} className="border-b border-white/[0.04] transition hover:bg-white/[0.02]">
                          <td className="px-4 py-3 text-white/60">{atk}</td>
                          <td className="px-4 py-3 text-white/60">{effect}</td>
                          <td className="px-4 py-3 text-white/60">{detect}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Endpoint method="POST" path="/simulate-attack" />
              </Card>
            </section>

            {/* ── 15 — EXPLAINABILITY ── */}
            <section id="explain" className="scroll-mt-20">
              <SectionHeader n={15} color="#67e8f9" icon={Search} title="Explainability Layer" sub="Every flag comes with a human-readable explanation." />
              <Card className="flex flex-col gap-6">
                <p className="leading-relaxed text-white/60">
                  Explainable AI is critical for trust. When a device is
                  flagged, the explainability layer produces a ranked list of
                  contributing factors — making it clear <em>why</em> the
                  system made its decision.
                </p>
                <CodeBlock title="GET /devices/camera_1/explain">{`{
  "device": "camera_1",
  "trust_score": 23,
  "risk_level": "HIGH",
  "factors": [
    {
      "signal": "traffic_spike",
      "detail": "packet_rate 420/min — 4.2x baseline",
      "impact": -28
    },
    {
      "signal": "new_destination",
      "detail": "external IP 203.0.113.42 never seen before",
      "impact": -19
    },
    {
      "signal": "protocol_violation",
      "detail": "SSH observed — not in allowed set [RTSP, HTTPS]",
      "impact": -30
    }
  ],
  "summary": "camera_1 flagged: traffic 4x baseline, new external destination, SSH protocol violation"
}`}</CodeBlock>
                <Endpoint method="GET" path="/devices/{'{id}'}/explain" />
              
              </Card>
            </section>

            {/* ── FOOTER ── */}
            <div className="h-px bg-white/[0.08]" />
            <footer className="flex items-center justify-between pb-12 pt-4">
              <Link
                href="/"
                className="text-sm text-white/40 transition hover:text-white/70"
              >
                ← Back to Home
              </Link>
              <Link
                href="/dashboard"
                className="group inline-flex items-center gap-2 rounded-full bg-[#e5ffd4] px-6 py-3 text-sm font-medium text-[#111411] transition hover:-translate-y-0.5 hover:bg-[#efffe4]"
              >
                See it Live →
              </Link>
            </footer>
          </article>
        </div>
      </div>
    </main>
  );
}

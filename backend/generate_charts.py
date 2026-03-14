import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
from collections import Counter, defaultdict

import seaborn as sns

from app.services.telemetry_generator import TelemetryGenerator
from app.services.feature_engine import FeatureEngine
from app.services.baseline_engine import BaselineEngine
from app.services.drift_detector import DriftDetector
from app.services.policy_engine import PolicyEngine
from app.services.ml_detector import MLDetector
from app.models.telemetry import DeviceType

OUT = os.path.join(os.path.dirname(__file__), "charts")
os.makedirs(OUT, exist_ok=True)

PALETTE = {
    "camera": "#4F8CF7",
    "printer": "#34D399",
    "router": "#FBBF24",
    "laptop": "#A78BFA",
    "smart_tv": "#F87171",
}
ACCENT = "#4F8CF7"
DANGER = "#EF4444"
SAFE = "#10B981"
WARN = "#F59E0B"
BG = "#FAFBFC"
GRID = "#E5E7EB"
TEXT = "#1F2937"
SUBTEXT = "#6B7280"

sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": GRID,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.alpha": 0.6,
    "text.color": TEXT,
    "axes.labelcolor": TEXT,
    "xtick.color": SUBTEXT,
    "ytick.color": SUBTEXT,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "figure.dpi": 180,
})


def setup_data():
    gen = TelemetryGenerator(seed=42)
    gen.generate_baseline_windows(5, 3)
    fe = FeatureEngine()
    baseline_features = fe.process_all_windows(gen.get_all_telemetry())
    be = BaselineEngine()
    be.learn_all_baselines(baseline_features)
    dd = DriftDetector(be)
    dd.analyze_window(baseline_features)
    pe = PolicyEngine()
    pe.evaluate_records(gen.get_all_telemetry())
    ml = MLDetector()
    ml.train_on_baseline(baseline_features)
    ml.score_batch(baseline_features)

    attacks = [
        ("camera_1", "backdoor"),
        ("printer_1", "data_exfiltration"),
        ("smart_tv_1", "traffic_spike"),
    ]
    for device_id, attack_type in attacks:
        for _ in range(3):
            records = gen.generate_window(records_per_device=3, attack_devices={device_id: attack_type})
            window_features = fe.process_window(records)
            dd.analyze_window(window_features)
            pe.evaluate_records(records)
            ml.score_batch(window_features)

    return gen, fe, be, dd, pe, ml


def chart1_traffic_profile(fe, gen):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.suptitle("Device Traffic Fingerprints", fontsize=18, fontweight="bold", y=1.02, color=TEXT)

    device_types = ["camera", "printer", "router", "laptop", "smart_tv"]
    labels = ["Camera", "Printer", "Router", "Laptop", "Smart TV"]

    avg_sent = []
    avg_recv = []
    avg_rate = []
    avg_dur = []
    for dt in device_types:
        devices = [d for d in gen.devices if d.device_type.value == dt]
        all_fv = []
        for d in devices:
            all_fv.extend(fe.get_device_features(d.device_id))
        avg_sent.append(np.mean([f.total_bytes_sent for f in all_fv]) / 1000)
        avg_recv.append(np.mean([f.total_bytes_received for f in all_fv]) / 1000)
        avg_rate.append(np.mean([f.packet_rate for f in all_fv]))
        avg_dur.append(np.mean([f.avg_session_duration for f in all_fv]))

    x = np.arange(len(labels))
    w = 0.35
    colors_sent = [PALETTE[dt] for dt in device_types]
    colors_recv = [plt.matplotlib.colors.to_rgba(PALETTE[dt], 0.5) for dt in device_types]

    bars1 = axes[0].bar(x - w/2, avg_sent, w, label="Bytes Sent (KB)", color=colors_sent, edgecolor="white", linewidth=0.5)
    bars2 = axes[0].bar(x + w/2, avg_recv, w, label="Bytes Received (KB)", color=colors_recv, edgecolor="white", linewidth=0.5)
    axes[0].set_xlabel("Device Type")
    axes[0].set_ylabel("Average KB per Window")
    axes[0].set_title("Traffic Volume by Direction", fontsize=13, fontweight="600", pad=12)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=15, ha="right")
    axes[0].legend(frameon=True, fancybox=True, shadow=False, edgecolor=GRID)
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

    scatter_colors = [PALETTE[dt] for dt in device_types]
    sizes = [r * 3 for r in avg_rate]
    axes[1].scatter(avg_dur, avg_rate, s=sizes, c=scatter_colors, alpha=0.85, edgecolors="white", linewidth=1.5, zorder=5)
    for i, lbl in enumerate(labels):
        axes[1].annotate(lbl, (avg_dur[i], avg_rate[i]), textcoords="offset points",
                         xytext=(8, 8), fontsize=9, color=SUBTEXT, fontweight="500")
    axes[1].set_xlabel("Avg Session Duration (s)")
    axes[1].set_ylabel("Packet Rate (per min)")
    axes[1].set_title("Behavioral Clustering", fontsize=13, fontweight="600", pad=12)

    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "01_traffic_profile.png"), bbox_inches="tight", facecolor=BG)
    plt.close()
    print("  [1/7] Traffic Profile")


def chart2_radar(fe, gen):
    device_types = ["camera", "printer", "router", "laptop", "smart_tv"]
    labels_dt = ["Camera", "Printer", "Router", "Laptop", "Smart TV"]
    features = ["packet_rate", "avg_session_duration", "traffic_volume", "destination_entropy", "protocol_entropy", "unique_destinations"]
    feat_labels = ["Packet Rate", "Session Duration", "Traffic Volume", "Dest Entropy", "Proto Entropy", "Unique Dests"]

    all_vals = defaultdict(list)
    for dt in device_types:
        devices = [d for d in gen.devices if d.device_type.value == dt]
        fvs = []
        for d in devices:
            fvs.extend(fe.get_device_features(d.device_id))
        for feat in features:
            vals = [getattr(f, feat) for f in fvs]
            all_vals[dt].append(np.mean(vals))

    maxes = []
    for i in range(len(features)):
        maxes.append(max(all_vals[dt][i] for dt in device_types))
    normed = {}
    for dt in device_types:
        normed[dt] = [all_vals[dt][i] / max(maxes[i], 0.001) for i in range(len(features))]

    N = len(features)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    fig.suptitle("Device Behavioral Fingerprint", fontsize=18, fontweight="bold", y=1.0, color=TEXT)

    ax.set_facecolor("#FFFFFF")
    ax.spines["polar"].set_color(GRID)
    ax.set_thetagrids(np.degrees(angles[:-1]), feat_labels, fontsize=9, color=SUBTEXT)
    ax.set_ylim(0, 1.15)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7, color=SUBTEXT)
    ax.grid(color=GRID, alpha=0.5)

    for dt, lbl in zip(device_types, labels_dt):
        vals = normed[dt] + normed[dt][:1]
        ax.plot(angles, vals, linewidth=2.2, label=lbl, color=PALETTE[dt])
        ax.fill(angles, vals, alpha=0.08, color=PALETTE[dt])

    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), frameon=True, fancybox=True, edgecolor=GRID)
    fig.savefig(os.path.join(OUT, "02_behavioral_radar.png"), bbox_inches="tight", facecolor=BG)
    plt.close()
    print("  [2/7] Behavioral Radar")


def chart3_attack_detection(ml, gen, fe):
    attacks = {"camera_1": "Backdoor", "printer_1": "Exfiltration", "smart_tv_1": "Traffic Spike"}
    normals = {"camera_1": "camera_2", "printer_1": "printer_2", "smart_tv_1": "smart_tv_2"}

    fig, ax = plt.subplots(figsize=(12, 5.5))
    fig.suptitle("ML Anomaly Detection — Attack vs Normal", fontsize=18, fontweight="bold", y=1.02, color=TEXT)

    group_labels = []
    attacked_scores = []
    normal_scores = []
    for dev_id, attack_name in attacks.items():
        scores_atk = ml.get_device_scores(dev_id)
        scores_norm = ml.get_device_scores(normals[dev_id])
        attacked_scores.append(scores_atk[-1].anomaly_score if scores_atk else 0)
        normal_scores.append(scores_norm[-1].anomaly_score if scores_norm else 0)
        group_labels.append(f"{attack_name}\n({dev_id})")

    x = np.arange(len(group_labels))
    w = 0.32

    bars_atk = ax.bar(x - w/2, attacked_scores, w, label="Attacked Device", color=DANGER, edgecolor="white", linewidth=0.5, zorder=5)
    bars_nrm = ax.bar(x + w/2, normal_scores, w, label="Normal Peer", color=SAFE, edgecolor="white", linewidth=0.5, zorder=5)

    ax.axhline(y=0.5, color=WARN, linestyle="--", linewidth=1.5, alpha=0.8, label="Anomaly Threshold (0.5)")

    for bar, score in zip(bars_atk, attacked_scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, f"{score:.2f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold", color=DANGER)
    for bar, score in zip(bars_nrm, normal_scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, f"{score:.2f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold", color=SAFE)

    ax.set_ylabel("Anomaly Score (0 = normal, 1 = suspicious)")
    ax.set_xticks(x)
    ax.set_xticklabels(group_labels)
    ax.set_ylim(0, 1.12)
    ax.legend(loc="upper left", frameon=True, fancybox=True, edgecolor=GRID)

    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "03_attack_detection.png"), bbox_inches="tight", facecolor=BG)
    plt.close()
    print("  [3/7] Attack Detection Comparison")


def chart4_drift_timeline(dd):
    fig, ax = plt.subplots(figsize=(13, 5.5))
    fig.suptitle("Behavioral Drift Timeline — camera_1 Under Backdoor Attack", fontsize=16, fontweight="bold", y=1.02, color=TEXT)

    history = dd.get_device_history("camera_1")
    windows = [r.window_id for r in history]
    scores = [r.drift_score for r in history]
    drifting = [r.is_drifting for r in history]
    severities = [r.severity.value for r in history]

    colors = []
    for s in severities:
        if s == "critical":
            colors.append(DANGER)
        elif s == "high":
            colors.append("#F97316")
        elif s == "medium":
            colors.append(WARN)
        elif s == "low":
            colors.append("#60A5FA")
        else:
            colors.append(SAFE)

    ax.plot(windows, scores, color=ACCENT, linewidth=2.5, zorder=3, alpha=0.7)
    ax.scatter(windows, scores, c=colors, s=80, zorder=5, edgecolors="white", linewidth=1.2)

    attack_start = None
    for i, d in enumerate(drifting):
        if d and attack_start is None:
            attack_start = windows[i]
    if attack_start:
        ax.axvline(x=attack_start, color=DANGER, linestyle=":", linewidth=1.5, alpha=0.6)
        ax.annotate("Attack Begins", xy=(attack_start, max(scores) * 0.5),
                     fontsize=9, color=DANGER, fontweight="600",
                     xytext=(attack_start + 0.3, max(scores) * 0.6),
                     arrowprops=dict(arrowstyle="->", color=DANGER, lw=1.2))

    confirm_window = None
    for r in history:
        if r.consecutive_drift_windows == 3:
            confirm_window = r.window_id
            break
    if confirm_window:
        ax.axvline(x=confirm_window, color="#7C3AED", linestyle=":", linewidth=1.5, alpha=0.6)
        ax.annotate("Drift Confirmed", xy=(confirm_window, max(scores) * 0.8),
                     fontsize=9, color="#7C3AED", fontweight="600",
                     xytext=(confirm_window + 0.3, max(scores) * 0.9),
                     arrowprops=dict(arrowstyle="->", color="#7C3AED", lw=1.2))

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=SAFE, markersize=10, label="None"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=WARN, markersize=10, label="Medium"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#F97316", markersize=10, label="High"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=DANGER, markersize=10, label="Critical"),
    ]
    ax.legend(handles=legend_elements, title="Severity", loc="upper left", frameon=True, fancybox=True, edgecolor=GRID)

    ax.set_xlabel("Window ID")
    ax.set_ylabel("Drift Score")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "04_drift_timeline.png"), bbox_inches="tight", facecolor=BG)
    plt.close()
    print("  [4/7] Drift Timeline")


def chart5_policy_violations(pe):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.suptitle("Policy Engine — Violation Analysis", fontsize=18, fontweight="bold", y=1.02, color=TEXT)

    by_type = Counter()
    for v in pe.violations:
        by_type[v.policy_type.value] += 1

    type_labels = {
        "protocol_blacklist": "Protocol\nBlacklist",
        "destination_restriction": "Destination\nRestriction",
        "traffic_ceiling": "Traffic\nCeiling",
        "session_limit": "Session\nLimit",
        "traffic_direction": "Traffic\nDirection",
    }
    type_colors = {
        "protocol_blacklist": DANGER,
        "destination_restriction": "#F97316",
        "traffic_ceiling": WARN,
        "session_limit": "#60A5FA",
        "traffic_direction": "#A78BFA",
    }

    labels = [type_labels.get(k, k) for k in by_type.keys()]
    sizes = list(by_type.values())
    colors = [type_colors.get(k, ACCENT) for k in by_type.keys()]

    wedges, texts, autotexts = axes[0].pie(
        sizes, labels=labels, colors=colors, autopct="%1.0f%%",
        startangle=90, pctdistance=0.75,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
        textprops=dict(fontsize=9, color=TEXT),
    )
    for t in autotexts:
        t.set_fontsize(10)
        t.set_fontweight("bold")
        t.set_color("white")
    axes[0].set_title("Violations by Policy Type", fontsize=13, fontweight="600", pad=12)

    by_device = Counter()
    for v in pe.violations:
        by_device[v.device_id] += 1
    top_devices = by_device.most_common(8)
    if top_devices:
        dev_names = [d[0] for d in top_devices]
        dev_counts = [d[1] for d in top_devices]
        dev_colors = []
        for name in dev_names:
            for dt, color in PALETTE.items():
                if dt in name:
                    dev_colors.append(color)
                    break
            else:
                dev_colors.append(ACCENT)

        bars = axes[1].barh(dev_names[::-1], dev_counts[::-1], color=dev_colors[::-1], edgecolor="white", linewidth=0.5, height=0.6)
        for bar, count in zip(bars, dev_counts[::-1]):
            axes[1].text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, str(count),
                         va="center", fontsize=10, fontweight="bold", color=SUBTEXT)
        axes[1].set_xlabel("Number of Violations")
        axes[1].set_title("Top Devices with Violations", fontsize=13, fontweight="600", pad=12)

    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "05_policy_violations.png"), bbox_inches="tight", facecolor=BG)
    plt.close()
    print("  [5/7] Policy Violations")


def chart6_zscore_heatmap(be, fe, gen):
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.suptitle("Z-Score Deviation Heatmap — Latest Window (Attacked Devices)", fontsize=16, fontweight="bold", y=1.02, color=TEXT)

    target_devices = ["camera_1", "camera_2", "printer_1", "printer_2", "smart_tv_1", "smart_tv_2", "router_1", "laptop_1"]
    features_to_show = [
        "packet_rate", "avg_session_duration", "traffic_volume",
        "total_bytes_sent", "total_bytes_received", "destination_entropy",
        "protocol_entropy", "external_connection_ratio", "inbound_outbound_ratio",
    ]
    feat_short = ["Packet\nRate", "Session\nDuration", "Traffic\nVolume", "Bytes\nSent",
                   "Bytes\nRecv", "Dest\nEntropy", "Proto\nEntropy", "External\nConn", "In/Out\nRatio"]

    matrix = []
    row_labels = []
    for dev_id in target_devices:
        fvs = fe.get_device_features(dev_id)
        if not fvs:
            continue
        latest = fvs[-1]
        dev = be.compute_deviation(latest)
        row = [dev.deviations.get(f, 0) for f in features_to_show]
        row = [max(-15, min(15, v)) for v in row]
        matrix.append(row)
        attacked = dev_id in ("camera_1", "printer_1", "smart_tv_1")
        row_labels.append(f"{'>> ' if attacked else '   '}{dev_id}")

    matrix = np.array(matrix)
    im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto", vmin=-10, vmax=10)

    ax.set_xticks(np.arange(len(feat_short)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(feat_short, fontsize=8)
    ax.set_yticklabels(row_labels, fontsize=10)

    for i in range(len(row_labels)):
        for j in range(len(feat_short)):
            val = matrix[i, j]
            color = "white" if abs(val) > 5 else TEXT
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=8, fontweight="bold", color=color)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Z-Score (deviation from baseline)", fontsize=10)

    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "06_zscore_heatmap.png"), bbox_inches="tight", facecolor=BG)
    plt.close()
    print("  [6/7] Z-Score Heatmap")


def chart7_pipeline_overview(dd, pe, ml, gen):
    fig, ax = plt.subplots(figsize=(15, 6))
    fig.suptitle("IoT Sentinel — Multi-Signal Detection Dashboard", fontsize=18, fontweight="bold", y=1.02, color=TEXT)

    devices = ["camera_1", "camera_2", "printer_1", "printer_2",
               "smart_tv_1", "smart_tv_2", "router_1", "laptop_1"]

    drift_scores_norm = []
    policy_scores = []
    ml_scores = []
    device_labels = []

    for dev_id in devices:
        ds = dd.get_device_state(dev_id)
        drift_val = min(ds.latest_drift_score / 200, 1.0) if ds else 0

        ps = pe.get_device_state(dev_id)
        policy_val = min(ps.violation_rate * 5, 1.0) if ps else 0

        ml_s = ml.get_device_scores(dev_id)
        ml_val = ml_s[-1].anomaly_score if ml_s else 0

        drift_scores_norm.append(drift_val)
        policy_scores.append(policy_val)
        ml_scores.append(ml_val)

        attacked = dev_id in ("camera_1", "printer_1", "smart_tv_1")
        device_labels.append(f"{'* ' if attacked else ''}{dev_id}")

    matrix = np.array([drift_scores_norm, policy_scores, ml_scores])
    signal_labels = ["Drift\nDetection", "Policy\nViolations", "ML Anomaly\nScore"]

    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(np.arange(len(device_labels)))
    ax.set_yticks(np.arange(len(signal_labels)))
    ax.set_xticklabels(device_labels, fontsize=10, rotation=25, ha="right")
    ax.set_yticklabels(signal_labels, fontsize=11)

    for i in range(len(signal_labels)):
        for j in range(len(device_labels)):
            val = matrix[i, j]
            color = "white" if val > 0.5 else TEXT
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=9, fontweight="bold", color=color)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Signal Intensity (0 = safe, 1 = danger)", fontsize=10)

    ax.set_title("* = attacked device", fontsize=10, color=SUBTEXT, style="italic", pad=10)

    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "07_pipeline_dashboard.png"), bbox_inches="tight", facecolor=BG)
    plt.close()
    print("  [7/7] Pipeline Dashboard")


if __name__ == "__main__":
    print("Initializing detection pipeline...")
    gen, fe, be, dd, pe, ml = setup_data()
    print(f"Pipeline ready. Generating charts...\n")

    chart1_traffic_profile(fe, gen)
    chart2_radar(fe, gen)
    chart3_attack_detection(ml, gen, fe)
    chart4_drift_timeline(dd)
    chart5_policy_violations(pe)
    chart6_zscore_heatmap(be, fe, gen)
    chart7_pipeline_overview(dd, pe, ml, gen)

    print(f"\nAll charts saved to: {OUT}/")
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".png"):
            size = os.path.getsize(os.path.join(OUT, f)) / 1024
            print(f"  {f}  ({size:.0f} KB)")

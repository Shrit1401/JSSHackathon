from __future__ import annotations

import json
from datetime import datetime

from .engines.telemetry import TelemetryGenerator
from .engines.features import FeatureEngine
from .engines.baseline import BaselineEngine
from .engines.drift import DriftDetector
from .engines.policy import PolicyEngine
from .engines.ml import MLDetector
from .engines.trust import TrustEngine
from .engines.alerts import AlertManager
from .device_profiles import ATTACK_PROFILES


BASELINE_WINDOWS = 5
ATTACK_CYCLES = 5
TARGET_DEVICE = "camera_1"
ATTACK_TYPE = "backdoor"

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def color_trust(score):
    if score >= 80:
        return f"{GREEN}{score:.2f}{RESET}"
    if score >= 60:
        return f"{YELLOW}{score:.2f}{RESET}"
    if score >= 40:
        return f"{YELLOW}{score:.2f}{RESET}"
    return f"{RED}{score:.2f}{RESET}"


def color_risk(level):
    mapping = {"SAFE": GREEN, "LOW": YELLOW, "MEDIUM": YELLOW, "HIGH": RED}
    c = mapping.get(level, RESET)
    return f"{c}{level}{RESET}"


def color_severity(sev):
    mapping = {"CRITICAL": RED, "HIGH": RED, "MEDIUM": YELLOW, "LOW": GREEN, "INFO": DIM, "none": DIM}
    c = mapping.get(sev, RESET)
    return f"{c}{sev}{RESET}"


def separator(title=""):
    line = "═" * 70
    if title:
        print(f"\n{BOLD}{CYAN}╔{line}╗{RESET}")
        padded = title.center(70)
        print(f"{BOLD}{CYAN}║{padded}║{RESET}")
        print(f"{BOLD}{CYAN}╚{line}╝{RESET}")
    else:
        print(f"{DIM}{'─' * 72}{RESET}")


def main():
    separator("IoT SENTINEL — STANDALONE PIPELINE")
    print(f"{DIM}Started at {datetime.utcnow().isoformat()}Z{RESET}")

    generator = TelemetryGenerator(seed=42)
    feature_engine = FeatureEngine()
    baseline_engine = BaselineEngine()
    drift_detector = DriftDetector(baseline_engine)
    policy_engine = PolicyEngine()
    ml_detector = MLDetector()
    trust_engine = TrustEngine(drift_detector, policy_engine, ml_detector, baseline_engine)
    alert_manager = AlertManager(drift_detector, policy_engine, ml_detector, trust_engine)

    devices = [(d.device_id, d.device_type) for d in generator.devices]
    print(f"\n{BOLD}Devices registered:{RESET} {len(devices)}")
    for did, dtype in devices:
        print(f"  {DIM}•{RESET} {did} ({dtype.value})")

    # ── Phase 1: Baseline Learning ──
    separator("PHASE 1 — BASELINE LEARNING")
    print(f"Generating {BASELINE_WINDOWS} clean telemetry windows...")
    baseline_records = generator.generate_baseline_windows(num_windows=BASELINE_WINDOWS, records_per_device=3)
    print(f"  Telemetry records generated: {len(baseline_records)}")

    baseline_features = feature_engine.process_all_windows(baseline_records)
    print(f"  Feature vectors extracted:   {len(baseline_features)}")

    baseline_result = baseline_engine.learn_all_baselines(baseline_features)
    print(f"  Device baselines learned:    {baseline_result['device_baselines']}")
    print(f"  Type baselines learned:      {baseline_result['type_baselines']}")

    # ── Phase 2: ML Training ──
    separator("PHASE 2 — ML MODEL TRAINING")
    ml_detector.train_on_baseline(baseline_features)
    info = ml_detector.get_model_info()
    print(f"  Model:             {info.model_type}")
    print(f"  Training samples:  {info.training_samples}")
    print(f"  Features:          {', '.join(info.training_features)}")
    print(f"  Contamination:     {info.contamination}")

    # ── Phase 3: Normal operation (1 clean cycle) ──
    separator("PHASE 3 — NORMAL OPERATION (1 clean cycle)")
    clean_records = generator.generate_window(records_per_device=3)
    clean_features = feature_engine.process_window(clean_records)
    drift_detector.analyze_window(clean_features)
    policy_engine.evaluate_records(clean_records)
    ml_detector.score_batch(clean_features)
    trust_engine.ingest_features(clean_features)
    clean_trust = trust_engine.compute_all(devices)

    print(f"  {'Device':<22} {'Trust':>7}  {'Risk':<8}  {'Baseline Update'}")
    separator()
    for ts in sorted(clean_trust, key=lambda s: s.trust_score):
        allowed = f"{GREEN}allowed{RESET}" if ts.baseline_update_allowed else f"{RED}blocked{RESET}"
        print(f"  {ts.device_id:<22} {color_trust(ts.trust_score):>18}  {color_risk(ts.risk_level.value):<19}  {allowed}")

    # ── Phase 4: Attack Simulation ──
    profile = ATTACK_PROFILES[ATTACK_TYPE]
    separator(f"PHASE 4 — ATTACK: {ATTACK_TYPE.upper()} on {TARGET_DEVICE}")
    print(f"  {BOLD}Description:{RESET} {profile['description']}")
    print(f"  {BOLD}Cycles:{RESET}      {ATTACK_CYCLES}")
    print()

    cycle_results = []
    for i in range(ATTACK_CYCLES):
        records = generator.generate_window(
            records_per_device=3,
            attack_devices={TARGET_DEVICE: ATTACK_TYPE},
        )
        features = feature_engine.process_window(records)
        drift_results = drift_detector.analyze_window(features)
        policy_engine.evaluate_records(records)
        ml_detector.score_batch(features)
        trust_engine.ingest_features(features)
        trust_scores = trust_engine.compute_all(devices)

        target_trust = next((s for s in trust_scores if s.device_id == TARGET_DEVICE), None)
        target_drift = next((d for d in drift_results if d.device_id == TARGET_DEVICE), None)

        cycle_data = {
            "cycle": i + 1,
            "trust_score": target_trust.trust_score if target_trust else None,
            "risk_level": target_trust.risk_level.value if target_trust else None,
            "drift_score": target_drift.drift_score if target_drift else 0,
            "is_drifting": target_drift.is_drifting if target_drift else False,
            "drift_severity": target_drift.severity.value if target_drift else "none",
            "baseline_allowed": target_trust.baseline_update_allowed if target_trust else True,
        }
        cycle_results.append(cycle_data)

        drift_indicator = f"{RED}DRIFTING{RESET}" if cycle_data["is_drifting"] else f"{GREEN}stable{RESET}"
        baseline_indicator = f"{GREEN}allowed{RESET}" if cycle_data["baseline_allowed"] else f"{RED}blocked{RESET}"

        print(f"  Cycle {i+1}/{ATTACK_CYCLES}  │  "
              f"Trust: {color_trust(cycle_data['trust_score'])}  │  "
              f"Risk: {color_risk(cycle_data['risk_level'])}  │  "
              f"Drift: {drift_indicator} ({color_severity(cycle_data['drift_severity'])})  │  "
              f"Baseline: {baseline_indicator}")

    # ── Phase 5: Alert Generation ──
    separator("PHASE 5 — ALERT SYSTEM")
    alert_manager.scan_all()
    alerts = alert_manager.alerts

    summary = alert_manager.get_summary()
    print(f"  {BOLD}Total alerts:{RESET} {len(alerts)}")
    print()

    if summary.by_severity:
        print(f"  {BOLD}By severity:{RESET}")
        for sev, count in sorted(summary.by_severity.items(), key=lambda x: ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"].index(x[0]) if x[0] in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] else 99):
            print(f"    {color_severity(sev)}: {count}")
        print()

    if summary.by_type:
        print(f"  {BOLD}By type:{RESET}")
        for atype, count in sorted(summary.by_type.items()):
            print(f"    {atype}: {count}")
        print()

    if summary.by_device:
        print(f"  {BOLD}By device:{RESET}")
        for dev, count in sorted(summary.by_device.items(), key=lambda x: -x[1]):
            print(f"    {dev}: {count}")
        print()

    target_alerts = [a for a in alerts if a.device_id == TARGET_DEVICE]
    if target_alerts:
        print(f"  {BOLD}{RED}Alerts for {TARGET_DEVICE}:{RESET}")
        for a in target_alerts:
            print(f"    [{color_severity(a.severity.value)}] {a.title}")
            print(f"      {DIM}{a.reason}{RESET}")

    # ── Phase 6: Trust Score Final State ──
    separator(f"PHASE 6 — FINAL TRUST SCORES")
    all_trust = trust_engine.get_all_latest()

    print(f"  {'Device':<22} {'Trust':>7}  {'Risk':<8}  {'Baseline Update'}")
    separator()
    for ts in sorted(all_trust, key=lambda s: s.trust_score):
        allowed = f"{GREEN}allowed{RESET}" if ts.baseline_update_allowed else f"{RED}blocked{RESET}"
        print(f"  {ts.device_id:<22} {color_trust(ts.trust_score):>18}  {color_risk(ts.risk_level.value):<19}  {allowed}")

    trust_summary = trust_engine.get_summary()
    print()
    print(f"  {BOLD}Average trust:{RESET}          {color_trust(trust_summary.average_trust)}")
    print(f"  {BOLD}Lowest trust device:{RESET}    {trust_summary.lowest_trust_device} ({color_trust(trust_summary.lowest_trust_score)})")
    print(f"  {BOLD}Baseline blocked:{RESET}       {trust_summary.baseline_updates_blocked} devices")
    if trust_summary.devices_by_risk:
        print(f"  {BOLD}Risk distribution:{RESET}")
        for risk, count in trust_summary.devices_by_risk.items():
            print(f"    {color_risk(risk)}: {count}")

    # ── Phase 7: Baseline Protection State ──
    separator(f"PHASE 7 — BASELINE PROTECTION")
    protection_summary = trust_engine.protector.get_summary()

    print(f"  {BOLD}Total devices tracked:{RESET}  {protection_summary.total_devices}")
    print(f"  {BOLD}Learning:{RESET}               {GREEN}{protection_summary.devices_learning}{RESET}")
    print(f"  {BOLD}Frozen:{RESET}                 {YELLOW}{protection_summary.devices_frozen}{RESET}")
    print(f"  {BOLD}Quarantined:{RESET}            {RED}{protection_summary.devices_quarantined}{RESET}")
    print(f"  {BOLD}Total gate events:{RESET}      {protection_summary.total_gate_events}")
    print(f"  {BOLD}Allowed / Denied:{RESET}       {protection_summary.total_allowed} / {protection_summary.total_denied}")
    print(f"  {BOLD}Poisoning attempts:{RESET}     {protection_summary.total_poisoning_attempts}")
    print(f"  {BOLD}Average integrity:{RESET}      {protection_summary.average_integrity:.4f}")
    print(f"  {BOLD}Trust gate threshold:{RESET}   {protection_summary.trust_gate_threshold}")
    print(f"  {BOLD}Quarantine after:{RESET}       {protection_summary.quarantine_threshold} consecutive denials")

    target_protection = trust_engine.protector.get_device_state(TARGET_DEVICE)
    if target_protection:
        print()
        print(f"  {BOLD}{RED}Protection state for {TARGET_DEVICE}:{RESET}")
        print(f"    Status:             {color_severity(target_protection.status.value)}")
        print(f"    Frozen:             {target_protection.is_frozen}")
        print(f"    Quarantined:        {target_protection.is_quarantined}")
        print(f"    Consecutive denied: {target_protection.consecutive_denied}")
        print(f"    Total allowed:      {target_protection.total_allowed}")
        print(f"    Total denied:       {target_protection.total_denied}")
        print(f"    Poisoning attempts: {target_protection.poisoning_attempts}")
        print(f"    Baseline integrity: {target_protection.baseline_integrity:.4f}")

    # ── Signal Breakdown for target ──
    separator(f"SIGNAL BREAKDOWN — {TARGET_DEVICE}")
    target_final = trust_engine.get_device_trust(TARGET_DEVICE)
    if target_final and target_final.signal_breakdown:
        b = target_final.signal_breakdown
        print(f"  {BOLD}ML anomaly score:{RESET}      {b.ml_anomaly_score:.4f}  →  penalty: {RED}{b.ml_penalty:.2f}{RESET}")
        print(f"  {BOLD}Drift score:{RESET}           {b.drift_score:.4f}  →  penalty: {RED}{b.drift_penalty:.2f}{RESET}")
        print(f"  {BOLD}Drift confirmed:{RESET}       {b.drift_confirmed}  →  penalty: {RED}{b.drift_confirmation_penalty:.2f}{RESET}")
        print(f"  {BOLD}Policy violations:{RESET}     {b.policy_violations_total} total, {b.policy_high_confidence} high-conf  →  penalty: {RED}{b.policy_penalty:.2f}{RESET}")
        print(f"  {BOLD}Total penalty:{RESET}         {RED}{b.total_penalty:.2f}{RESET}")
        print(f"  {BOLD}Final trust score:{RESET}     {color_trust(target_final.trust_score)}")
        print(f"  {BOLD}Risk level:{RESET}            {color_risk(target_final.risk_level.value)}")

    # ── Trust History for target ──
    history = trust_engine.get_device_history(TARGET_DEVICE)
    if history:
        separator(f"TRUST HISTORY — {TARGET_DEVICE}")
        print(f"  {BOLD}Windows tracked:{RESET}  {len(history.scores)}")
        print(f"  {BOLD}Current:{RESET}          {color_trust(history.current_score)}")
        print(f"  {BOLD}Lowest:{RESET}           {color_trust(history.lowest_score)}")
        print(f"  {BOLD}Highest:{RESET}          {color_trust(history.highest_score)}")
        print(f"  {BOLD}Average:{RESET}          {color_trust(history.average_score)}")
        print()
        print(f"  {'Window':<8} {'Trust':>7}  {'Risk':<8}")
        separator()
        for idx, s in enumerate(history.scores):
            print(f"  {idx+1:<8} {color_trust(s.trust_score):>18}  {color_risk(s.risk_level.value)}")

    separator("DONE")
    print(f"{DIM}Completed at {datetime.utcnow().isoformat()}Z{RESET}\n")


if __name__ == "__main__":
    main()

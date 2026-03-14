from __future__ import annotations

import logging
import os
import time

from app.services import twilio_service
from app.services.ml_pipeline import pipeline

logger = logging.getLogger("iot_monitor.whatsapp_alerts")

ALERT_WHATSAPP_TO = os.getenv("ALERT_WHATSAPP_TO", "+919667271155")

_last_notified: dict[str, float] = {}
COOLDOWN_SECONDS = 120


def _should_notify(device_id: str) -> bool:
    last = _last_notified.get(device_id, 0)
    if time.time() - last < COOLDOWN_SECONDS:
        return False
    _last_notified[device_id] = time.time()
    return True


def _format_evidence_card(
    device_name: str,
    device_id: str,
    device_type: str,
    trust_score: int,
    risk_level: str,
    alert_type: str,
    severity: str,
    message: str,
    detail: dict | None = None,
) -> str:
    lines = [
        "🚨 *COMPROMISE DETECTED* 🚨",
        "",
        f"Device: {device_name}",
        f"Type: {device_type}",
        f"IP/ID: {device_id}",
        "",
        f"Trust Score: {trust_score}/100",
        f"Risk Level: {risk_level}",
        f"Alert: {alert_type}",
        f"Severity: {severity}",
        "",
        f"Details: {message}",
    ]

    if detail:
        lines.append("")
        lines.append("--- Evidence Breakdown ---")
        if "ml_anomaly_score" in detail:
            lines.append(f"ML Anomaly Score: {detail['ml_anomaly_score']:.4f}")
            lines.append(f"ML Penalty: {detail['ml_penalty']:.1f}")
        if "drift_score" in detail:
            lines.append(f"Drift Score: {detail['drift_score']:.4f}")
            lines.append(f"Drift Penalty: {detail['drift_penalty']:.1f}")
        if detail.get("drift_confirmed"):
            lines.append("Drift: CONFIRMED across multiple windows")
        if "policy_violations_total" in detail and detail["policy_violations_total"] > 0:
            lines.append(f"Policy Violations: {detail['policy_violations_total']} ({detail.get('policy_high_confidence', 0)} high-confidence)")
            lines.append(f"Policy Penalty: {detail['policy_penalty']:.1f}")
        if "total_penalty" in detail:
            lines.append(f"Total Penalty: {detail['total_penalty']:.1f}")

    lines.append("")
    lines.append("Action: Immediate isolation and forensic analysis recommended.")

    return "\n".join(lines)


def send_compromise_alert(
    device_name: str,
    device_id: str,
    device_type: str,
    trust_score: int,
    risk_level: str,
    alert_type: str = "COMPROMISE",
    severity: str = "CRITICAL",
    message: str = "Device trust critically low — likely compromised.",
) -> bool:
    if not _should_notify(device_id):
        logger.debug("Skipping WhatsApp alert for %s — cooldown active", device_id)
        return False

    detail = pipeline.get_device_trust_detail(device_id)

    card = _format_evidence_card(
        device_name=device_name,
        device_id=device_id,
        device_type=device_type,
        trust_score=trust_score,
        risk_level=risk_level,
        alert_type=alert_type,
        severity=severity,
        message=message,
        detail=detail,
    )

    try:
        twilio_service.send_whatsapp(to=ALERT_WHATSAPP_TO, body=card)
        logger.info("Evidence card sent for device %s (%s)", device_name, device_id)
        return True
    except Exception:
        logger.exception("Failed to send evidence card for device %s", device_id)
        return False


def send_attack_evidence_card(
    device: dict,
    attack_type: str,
    old_trust: int,
    new_trust: int,
    old_risk: str,
    new_risk: str,
) -> bool:
    device_id = device.get("id", "")
    if not _should_notify(device_id):
        logger.debug("Skipping attack evidence card for %s — cooldown active", device_id)
        return False

    detail = pipeline.get_device_trust_detail(device_id)

    message = (
        f"{attack_type} attack confirmed. "
        f"Trust dropped {old_trust} -> {new_trust}. "
        f"Risk escalated {old_risk} -> {new_risk}."
    )

    card = _format_evidence_card(
        device_name=device.get("name", "Unknown"),
        device_id=device_id,
        device_type=device.get("device_type", "unknown"),
        trust_score=new_trust,
        risk_level=new_risk,
        alert_type=attack_type,
        severity="CRITICAL",
        message=message,
        detail=detail,
    )

    try:
        twilio_service.send_whatsapp(to=ALERT_WHATSAPP_TO, body=card)
        logger.info("Attack evidence card sent for %s (%s)", device.get("name"), device_id)
        return True
    except Exception:
        logger.exception("Failed to send attack evidence card for %s", device_id)
        return False

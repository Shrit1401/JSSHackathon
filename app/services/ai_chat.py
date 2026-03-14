import asyncio
import json
import logging
import os

from google import genai

from app.database.supabase_client import supabase
from app.services.ml_pipeline import pipeline

logger = logging.getLogger("iot_monitor.ai_chat")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = "gemini-2.0-flash"

SYSTEM_INSTRUCTION = """You are an IoT security assistant for the IoT Trust Monitor system.
You have access to real-time data about the user's IoT network, including device info,
trust scores, risk levels, alerts, and ML pipeline analytics.

Your job is to answer questions about device health, trust scores, alerts, anomalies,
attacks, and overall network security status.

Rules:
- Be concise. Responses go to WhatsApp so keep them under 1500 characters.
- Use plain language but be precise with numbers and device names.
- If you see a device at HIGH risk or COMPROMISED, proactively warn about it.
- When listing devices, use a clean format with name, trust score, and risk level.
- If you don't have data for something, say so honestly.
- Do not use markdown formatting (no **, no ##, no ```) since this renders on WhatsApp.
- Use line breaks and simple dashes for lists.
"""


def _build_context() -> str:
    sections = []

    try:
        result = supabase.table("devices").select("name,device_type,trust_score,risk_level,status,ip_address").execute()
        devices = result.data or []
        if devices:
            lines = []
            for d in devices:
                lines.append(
                    f"- {d['name']} ({d['device_type']}) | trust: {d['trust_score']} | "
                    f"risk: {d['risk_level']} | status: {d['status']} | ip: {d['ip_address']}"
                )
            sections.append("DEVICES:\n" + "\n".join(lines))
    except Exception:
        logger.exception("Failed to fetch devices for AI context")

    try:
        result = supabase.table("alerts").select("*").order("timestamp", desc=True).limit(10).execute()
        alerts = result.data or []
        if alerts:
            lines = []
            for a in alerts:
                lines.append(
                    f"- [{a.get('severity', '?')}] {a.get('alert_type', '?')} on "
                    f"{a.get('device_name', 'unknown')}: {a.get('message', '')}"
                )
            sections.append("RECENT ALERTS (last 10):\n" + "\n".join(lines))
        else:
            sections.append("RECENT ALERTS: None")
    except Exception:
        logger.exception("Failed to fetch alerts for AI context")

    if pipeline.is_trained:
        try:
            trust_summary = pipeline.get_trust_summary()
            sections.append(
                f"TRUST SUMMARY:\n"
                f"- Total devices monitored: {trust_summary.get('total_devices', '?')}\n"
                f"- Average trust score: {trust_summary.get('average_trust', '?')}\n"
                f"- Risk distribution: {json.dumps(trust_summary.get('devices_by_risk', {}))}\n"
                f"- Weakest device ID: {trust_summary.get('lowest_trust_device', '?')} "
                f"(score: {trust_summary.get('lowest_trust_score', '?')})\n"
                f"- Baseline updates blocked: {trust_summary.get('baseline_updates_blocked', 0)}"
            )
        except Exception:
            logger.exception("Failed to get trust summary for AI context")

        try:
            protection = pipeline.get_protection_summary()
            sections.append(
                f"PROTECTION STATUS:\n"
                f"- Devices quarantined: {protection.get('devices_quarantined', 0)}\n"
                f"- Devices frozen: {protection.get('devices_frozen', 0)}\n"
                f"- Poisoning attempts: {protection.get('total_poisoning_attempts', 0)}\n"
                f"- Average baseline integrity: {protection.get('average_integrity', '?')}"
            )
        except Exception:
            logger.exception("Failed to get protection summary for AI context")

        if pipeline.active_attacks:
            attack_lines = []
            for internal_id, attack_type in pipeline.active_attacks.items():
                supa_id = pipeline.reverse_map.get(internal_id, internal_id)
                attack_lines.append(f"- Device {supa_id}: {attack_type}")
            sections.append("ACTIVE ATTACKS:\n" + "\n".join(attack_lines))
        else:
            sections.append("ACTIVE ATTACKS: None currently running")
    else:
        sections.append("ML PIPELINE: Not yet initialized")

    return "\n\n".join(sections)


async def chat(user_message: str) -> str:
    if not GEMINI_API_KEY:
        return "AI chat is not configured. Please set the GEMINI_API_KEY environment variable."

    try:
        context = await asyncio.to_thread(_build_context)

        full_system = SYSTEM_INSTRUCTION + "\n\nCURRENT NETWORK STATE:\n" + context

        client = genai.Client(api_key=GEMINI_API_KEY)

        response = await asyncio.to_thread(
            lambda: client.models.generate_content(
                model=MODEL,
                contents=user_message,
                config=genai.types.GenerateContentConfig(
                    system_instruction=full_system,
                    max_output_tokens=1024,
                    temperature=0.7,
                ),
            )
        )

        reply = response.text or "Sorry, I couldn't generate a response."
        if len(reply) > 1500:
            reply = reply[:1497] + "..."
        return reply

    except Exception:
        logger.exception("Gemini chat failed")
        return "Sorry, something went wrong while processing your message. Please try again."

from __future__ import annotations

import logging
import os

from twilio.rest import Client

logger = logging.getLogger("iot_monitor.twilio")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            raise RuntimeError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set")
        _client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _client


def send_whatsapp(to: str, body: str) -> dict:
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    client = _get_client()
    message = client.messages.create(
        body=body[:1600],
        from_=TWILIO_WHATSAPP_FROM,
        to=to,
    )
    logger.info("WhatsApp sent — SID=%s to=%s status=%s", message.sid, to, message.status)
    return {
        "sid": message.sid,
        "status": message.status,
        "to": to,
    }

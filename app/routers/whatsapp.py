from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.services import ai_chat, twilio_service

logger = logging.getLogger("iot_monitor.whatsapp")
router = APIRouter(prefix="/whatsapp")

TWIML_EMPTY = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


class SendRequest(BaseModel):
    to: str
    message: str


class SendResponse(BaseModel):
    sid: str
    status: str
    to: str


async def _handle_incoming(body: str, sender: str):
    try:
        logger.info("Processing WhatsApp from %s: %s", sender, body[:100])
        reply = await ai_chat.chat(body)
        twilio_service.send_whatsapp(to=sender, body=reply)
        logger.info("Reply sent to %s (%d chars)", sender, len(reply))
    except Exception:
        logger.exception("Failed to handle incoming WhatsApp from %s", sender)
        try:
            twilio_service.send_whatsapp(
                to=sender,
                body="Sorry, something went wrong processing your message. Please try again.",
            )
        except Exception:
            logger.exception("Failed to send error reply to %s", sender)


@router.post(
    "/webhook",
    summary="Twilio incoming WhatsApp webhook",
    description=(
        "Receives incoming WhatsApp messages from Twilio. "
        "Processes the message with Gemini AI and sends a reply back via Twilio."
    ),
)
async def webhook(
    background_tasks: BackgroundTasks,
    Body: str = Form(""),
    From: str = Form(""),
    To: str = Form(""),
    MessageSid: str = Form(""),
):
    logger.info("Webhook received — SID=%s From=%s Body=%s", MessageSid, From, Body[:80])

    if Body.strip():
        background_tasks.add_task(_handle_incoming, Body.strip(), From)

    return Response(content=TWIML_EMPTY, media_type="application/xml")


@router.post(
    "/send",
    response_model=SendResponse,
    summary="Send a WhatsApp message",
    description="Manually send a WhatsApp message to a specified number via Twilio.",
)
async def send_message(req: SendRequest):
    try:
        result = twilio_service.send_whatsapp(to=req.to, body=req.message)
        return SendResponse(**result)
    except Exception as exc:
        logger.exception("POST /whatsapp/send failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

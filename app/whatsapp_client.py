"""WhatsApp Cloud API helpers (send + parse)."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from . import config

log = logging.getLogger(__name__)

GRAPH = "https://graph.facebook.com/v20.0"


def send_text(to_phone: str, body: str) -> Dict[str, Any]:
    """Send a plain text WhatsApp message. `to_phone` must be E.164 without '+'."""
    url = f"{GRAPH}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone.lstrip("+"),
        "type": "text",
        "text": {"preview_url": True, "body": body[:4096]},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    if r.status_code >= 300:
        log.error("WhatsApp send failed: %s %s", r.status_code, r.text)
        r.raise_for_status()
    return r.json()


def parse_inbound(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract the first user-text message from a Meta webhook envelope.
    Returns dict or None for non-message events (statuses, system, etc.)."""
    try:
        entry = (payload.get("entry") or [{}])[0]
        change = (entry.get("changes") or [{}])[0]
        value = change.get("value") or {}
        messages = value.get("messages") or []
        if not messages:
            return None
        msg = messages[0]
        if msg.get("type") != "text":
            return {
                "from": msg.get("from", ""),
                "text": "",
                "type": msg.get("type", ""),
                "msg_id": msg.get("id", ""),
            }
        contact = (value.get("contacts") or [{}])[0]
        return {
            "from": msg.get("from", ""),
            "text": (msg.get("text") or {}).get("body", "").strip(),
            "type": "text",
            "msg_id": msg.get("id", ""),
            "name": ((contact.get("profile") or {}).get("name", "")),
        }
    except Exception:
        log.exception("Failed to parse inbound webhook payload")
        return None

"""WhatsApp Cloud API helpers (send + parse)."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

from . import config

log = logging.getLogger(__name__)

GRAPH = "https://graph.facebook.com/v20.0"

TEMPLATE_REPLY = "trooper_task_reply"
TEMPLATE_NEW_TASK = "trooper_new_task_notify"


def _post_message(payload: dict) -> Dict[str, Any]:
    url = f"{GRAPH}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    if r.status_code >= 300:
        log.error("WhatsApp send failed: %s %s", r.status_code, r.text)
    return {"status": r.status_code, "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text}


def send_template(
    to_phone: str,
    template_name: str,
    params: List[str],
    lang: str = "en",
) -> Dict[str, Any]:
    """Send an approved template message (works outside the 24h window)."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone.lstrip("+"),
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in params],
                }
            ],
        },
    }
    return _post_message(payload)


def send_text(to_phone: str, body: str, trooper_name: str = "") -> Dict[str, Any]:
    """Send a text message. Falls back to template if freeform fails (24h expired)."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone.lstrip("+"),
        "type": "text",
        "text": {"preview_url": True, "body": body[:4096]},
    }
    result = _post_message(payload)

    if result["status"] >= 300:
        log.warning("Freeform failed (status %s), trying template fallback", result["status"])
        name = trooper_name or to_phone
        tpl_result = send_template(to_phone, TEMPLATE_REPLY, [name, body[:900]])
        if tpl_result["status"] < 300:
            log.info("Template fallback succeeded for %s", to_phone)
            return tpl_result.get("body", tpl_result)
        log.error("Template fallback also failed: %s", tpl_result)

    if result["status"] >= 300:
        raise requests.HTTPError(f"WhatsApp send failed: {result}")

    return result.get("body", result)


def send_new_task_notification(
    to_phone: str,
    trooper_name: str,
    task_id: str,
    content_name: str,
) -> Dict[str, Any]:
    """Proactive notification for a new task (always uses template, no 24h limit)."""
    return send_template(
        to_phone,
        TEMPLATE_NEW_TASK,
        [trooper_name, task_id, content_name],
    )


def download_media(media_id: str) -> Optional[bytes]:
    """Download a media file from WhatsApp by its media ID.
    Returns raw bytes or None on failure."""
    headers = {"Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}"}
    try:
        meta_r = requests.get(f"{GRAPH}/{media_id}", headers=headers, timeout=15)
        if meta_r.status_code >= 300:
            log.error("Media meta fetch failed: %s %s", meta_r.status_code, meta_r.text)
            return None
        url = meta_r.json().get("url")
        if not url:
            return None
        dl_r = requests.get(url, headers=headers, timeout=30)
        if dl_r.status_code >= 300:
            log.error("Media download failed: %s", dl_r.status_code)
            return None
        return dl_r.content
    except Exception:
        log.exception("Failed to download media %s", media_id)
        return None


def parse_inbound(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract the first user message from a Meta webhook envelope.
    Handles text and image types. Returns dict or None for non-message events."""
    try:
        entry = (payload.get("entry") or [{}])[0]
        change = (entry.get("changes") or [{}])[0]
        value = change.get("value") or {}
        messages = value.get("messages") or []
        if not messages:
            return None
        msg = messages[0]
        contact = (value.get("contacts") or [{}])[0]
        msg_type = msg.get("type", "")
        base = {
            "from": msg.get("from", ""),
            "msg_id": msg.get("id", ""),
            "type": msg_type,
            "name": ((contact.get("profile") or {}).get("name", "")),
        }
        if msg_type == "text":
            base["text"] = (msg.get("text") or {}).get("body", "").strip()
        elif msg_type == "image":
            img = msg.get("image") or {}
            base["text"] = (img.get("caption") or "").strip()
            base["media_id"] = img.get("id", "")
            base["mime_type"] = img.get("mime_type", "image/jpeg")
        else:
            base["text"] = ""
        return base
    except Exception:
        log.exception("Failed to parse inbound webhook payload")
        return None

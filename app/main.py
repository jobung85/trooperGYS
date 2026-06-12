"""Flask web server: WhatsApp webhook + tiny health/poller endpoints."""
from __future__ import annotations

import logging
import os
import threading
from typing import Tuple

from flask import Flask, jsonify, request

from . import command_handler, config, poller, whatsapp_client

log = logging.getLogger(__name__)

app = Flask(__name__)


@app.get("/")
def root():
    return {"ok": True, "service": "trooper-whatsapp-bot"}


@app.get("/health")
def health():
    return {"ok": True, "troopers": [t.display_name for t in config.TROOPERS]}


# ─── WhatsApp webhook ─────────────────────────────────────────────────

@app.get("/webhook")
def webhook_verify() -> Tuple[str, int]:
    """Meta verifies your webhook by GET-ing this URL once.
    See https://developers.facebook.com/docs/graph-api/webhooks/getting-started"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge", "")
    if mode == "subscribe" and token == config.WHATSAPP_VERIFY_TOKEN:
        log.info("Webhook verified.")
        return challenge, 200
    log.warning("Webhook verification failed (mode=%s, token=%s)", mode, token)
    return "forbidden", 403


@app.post("/webhook")
def webhook_receive():
    payload = request.get_json(silent=True) or {}

    # Log delivery statuses so we can debug failed sends
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for st in value.get("statuses", []):
                status = st.get("status")
                recipient = st.get("recipient_id")
                errors = st.get("errors", [])
                if errors:
                    log.warning("DELIVERY %s to %s — errors: %s", status, recipient, errors)
                else:
                    log.info("DELIVERY %s to %s", status, recipient)

    msg = whatsapp_client.parse_inbound(payload)
    if not msg:
        return jsonify(status="ignored"), 200

    from_phone = msg["from"]
    msg_type = msg.get("type", "")
    text = msg.get("text", "")

    # Handle image messages (screenshot proof for /done)
    if msg_type == "image":
        log.info("← %s: [image] media_id=%s", from_phone, msg.get("media_id"))
        try:
            reply = command_handler.handle_image(
                from_phone,
                msg.get("media_id", ""),
                msg.get("mime_type", "image/jpeg"),
            )
        except Exception:
            log.exception("Image handler crashed")
            reply = "Sorry, something went wrong processing your image."
        if reply:
            trooper = config.trooper_by_phone(from_phone)
            trooper_name = trooper.display_name if trooper else from_phone
            try:
                whatsapp_client.send_text(from_phone, reply, trooper_name=trooper_name)
            except Exception:
                log.exception("Failed to send WA reply")
        return jsonify(status="ok"), 200

    if msg_type != "text":
        return jsonify(status="ignored"), 200

    log.info("← %s: %s", from_phone, text)

    try:
        reply = command_handler.handle(from_phone, text)
    except Exception:
        log.exception("Handler crashed")
        reply = "Sorry, something went wrong. Jonathan has been notified."

    if reply is None:
        return jsonify(status="ignored"), 200

    trooper = config.trooper_by_phone(from_phone)
    trooper_name = trooper.display_name if trooper else from_phone
    try:
        whatsapp_client.send_text(from_phone, reply, trooper_name=trooper_name)
    except Exception:
        log.exception("Failed to send WA reply")

    return jsonify(status="ok"), 200


# ─── Manual poll trigger ──────────────────────────────────────────────

@app.post("/internal/poll")
def trigger_poll():
    """Optional: secret-protected manual trigger of the poller.
    Use it for testing. Render Cron Job runs `poll_once.py` directly."""
    secret = request.headers.get("X-Trigger-Secret")
    if secret != config.WHATSAPP_VERIFY_TOKEN:
        return "forbidden", 403

    def _run():
        try:
            poller.run_once()
        except Exception:
            log.exception("Poll run failed")

    threading.Thread(target=_run, daemon=True).start()
    return jsonify(status="started"), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

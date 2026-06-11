"""Full integration test — prints JSON summary for Jonathan."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import requests

from app import command_handler, config, notion_client, whatsapp_client

JONATHAN = "6281216977718"
GRAPH = "https://graph.facebook.com/v20.0"
WEBHOOK_URL = "https://handcraft-procedure-unluckily.ngrok-free.dev/webhook"


def _meta_get(path: str, params: dict | None = None) -> dict:
    p = dict(params or {})
    p["access_token"] = config.WHATSAPP_ACCESS_TOKEN
    r = requests.get(f"{GRAPH}/{path}", params=p, timeout=30)
    try:
        return {"status": r.status_code, "body": r.json()}
    except Exception:
        return {"status": r.status_code, "body": r.text}


def _meta_post_messages(payload: dict) -> dict:
    url = f"{GRAPH}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    try:
        return {"status": r.status_code, "body": r.json()}
    except Exception:
        return {"status": r.status_code, "body": r.text}


def main() -> int:
    out: dict = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "waba_id": config.WHATSAPP_BUSINESS_ACCOUNT_ID,
            "phone_number_id": config.WHATSAPP_PHONE_NUMBER_ID,
            "webhook_url": WEBHOOK_URL,
            "verify_token_set": bool(config.WHATSAPP_VERIFY_TOKEN),
            "troopers": [t.display_name for t in config.TROOPERS],
        },
        "meta": {},
        "notion": {},
        "commands": {},
        "whatsapp_send": {},
        "webhook": {},
    }

    # Meta checks
    out["meta"]["token"] = _meta_get(
        "debug_token",
        {"input_token": config.WHATSAPP_ACCESS_TOKEN},
    )
    out["meta"]["phone"] = _meta_get(
        config.WHATSAPP_PHONE_NUMBER_ID,
        {
            "fields": "id,display_phone_number,verified_name,status,"
            "code_verification_status,account_mode,quality_rating,name_status"
        },
    )
    out["meta"]["waba"] = _meta_get(
        config.WHATSAPP_BUSINESS_ACCOUNT_ID,
        {"fields": "id,name,account_review_status,business_verification_status"},
    )
    out["meta"]["subscribed_apps"] = _meta_get(
        f"{config.WHATSAPP_BUSINESS_ACCOUNT_ID}/subscribed_apps"
    )
    out["meta"]["templates"] = _meta_get(
        f"{config.WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates",
        {"limit": 5},
    )

    # Notion
    try:
        t1 = notion_client.find_main_task_by_id("0001")
        t2 = notion_client.find_main_task_by_id("0002")
        pending = notion_client.list_pending_for_trooper("Sdr Jonathan")
        out["notion"] = {
            "ok": True,
            "task_0001": t1,
            "task_0002": t2,
            "jonathan_pending_count": len(pending),
            "jonathan_pending_sample": pending[:3],
        }
    except Exception as e:
        out["notion"] = {"ok": False, "error": str(e)}

    # Command handler (offline)
    cmds = {}
    for raw in ["/help", "/tasks", "/info 0001", "/lang id", "/help"]:
        cmds[raw] = command_handler.handle(JONATHAN, raw)
    out["commands"] = cmds

    # WhatsApp sends
    out["whatsapp_send"]["freeform"] = _meta_post_messages(
        {
            "messaging_product": "whatsapp",
            "to": JONATHAN,
            "type": "text",
            "text": {
                "body": (
                    "Trooper Bot — setup test (freeform). "
                    "If you see this, outbound messaging works. Reply /help."
                )
            },
        }
    )
    out["whatsapp_send"]["template_order"] = _meta_post_messages(
        {
            "messaging_product": "whatsapp",
            "to": JONATHAN,
            "type": "template",
            "template": {
                "name": "jaspers_market_order_confirmation_v1",
                "language": {"code": "en_US"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": "Jonathan"},
                            {"type": "text", "text": "SETUP-TEST"},
                            {"type": "text", "text": "today"},
                        ],
                    }
                ],
            },
        }
    )

    # Webhook verify (GET challenge simulation)
    try:
        r = requests.get(
            WEBHOOK_URL,
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": config.WHATSAPP_VERIFY_TOKEN,
                "hub.challenge": "trooper-challenge-123",
            },
            timeout=15,
        )
        out["webhook"]["verify_get"] = {
            "status": r.status_code,
            "body": r.text[:200],
            "ok": r.status_code == 200 and r.text.strip() == "trooper-challenge-123",
        }
    except Exception as e:
        out["webhook"]["verify_get"] = {"ok": False, "error": str(e)}

    try:
        r = requests.get("http://localhost:5000/health", timeout=5)
        out["webhook"]["local_health"] = {"status": r.status_code, "body": r.json()}
    except Exception as e:
        out["webhook"]["local_health"] = {"error": str(e)}

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Send an approved template message (required for LIVE numbers on first contact)."""
from __future__ import annotations

import sys

import requests

from app import config

GRAPH = "https://graph.facebook.com/v20.0"


def send_template(
    to_phone: str,
    template_name: str,
    lang: str = "en_US",
    components: list | None = None,
) -> dict:
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone.lstrip("+"),
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang},
        },
    }
    if components:
        payload["template"]["components"] = components

    url = f"{GRAPH}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    print("status:", r.status_code)
    print(r.text)
    r.raise_for_status()
    return r.json()


def main() -> int:
    to = sys.argv[1] if len(sys.argv) > 1 else "6281216977718"
    name = sys.argv[2] if len(sys.argv) > 2 else "jaspers_market_plain_text_v1"

    components = None
    if name == "jaspers_market_order_confirmation_v1":
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "Jonathan"},
                    {"type": "text", "text": "TROOPER-TEST"},
                    {"type": "text", "text": "today"},
                ],
            }
        ]

    send_template(to, name, components=components)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

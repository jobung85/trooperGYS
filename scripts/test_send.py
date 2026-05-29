"""Quick CLI to verify WhatsApp credentials.
Usage:   python -m scripts.test_send 6281234567890 "hello from bot"
"""
from __future__ import annotations

import sys

from app import whatsapp_client


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: test_send <phone-no-plus> <message>")
        return 1
    phone, msg = sys.argv[1], " ".join(sys.argv[2:])
    print(whatsapp_client.send_text(phone, msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())

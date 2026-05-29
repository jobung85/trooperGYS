"""Centralised env loader + trooper roster."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_MAIN_TASK_DB = os.environ["NOTION_MAIN_TASK_DB"]
NOTION_TASK_TRACKER_DB = os.environ["NOTION_TASK_TRACKER_DB"]

WHATSAPP_PHONE_NUMBER_ID = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
WHATSAPP_ACCESS_TOKEN = os.environ["WHATSAPP_ACCESS_TOKEN"]
WHATSAPP_VERIFY_TOKEN = os.environ["WHATSAPP_VERIFY_TOKEN"]

TIMEZONE = os.environ.get("TIMEZONE", "Asia/Jakarta")
TROOPERS_CONFIG = os.environ.get("TROOPERS_CONFIG", "config/troopers.json")
STATE_FILE = os.environ.get("STATE_FILE", ".state/last_poll.json")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@dataclass
class Trooper:
    notion_name: str
    display_name: str
    phone: str
    aliases: List[str]


def _load_roster() -> List[Trooper]:
    path = ROOT / TROOPERS_CONFIG if not Path(TROOPERS_CONFIG).is_absolute() else Path(TROOPERS_CONFIG)
    if not path.exists():
        raise FileNotFoundError(f"Trooper roster not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        Trooper(
            notion_name=t["notion_name"],
            display_name=t["display_name"],
            phone=str(t["phone"]).lstrip("+").replace(" ", ""),
            aliases=t.get("aliases", []),
        )
        for t in raw["troopers"]
    ]


TROOPERS: List[Trooper] = _load_roster()


def trooper_by_phone(phone: str) -> Optional[Trooper]:
    """Find a Trooper by inbound WhatsApp phone (Meta strips the '+')."""
    norm = phone.lstrip("+").replace(" ", "")
    for t in TROOPERS:
        if t.phone == norm:
            return t
    return None


def trooper_by_notion_name(name: str) -> Optional[Trooper]:
    for t in TROOPERS:
        if t.notion_name == name:
            return t
    return None

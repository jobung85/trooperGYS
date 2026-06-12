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

WHATSAPP_BUSINESS_ACCOUNT_ID = os.environ.get(
    "WHATSAPP_BUSINESS_ACCOUNT_ID", "1379492034025973"
)
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

ADMIN_PHONE = os.environ.get("ADMIN_PHONE", "6281216977718")


def _load_dynamic_troopers() -> None:
    """Merge any previously approved dynamic troopers from state file."""
    try:
        state_path = Path(STATE_FILE)
        if state_path.exists():
            data = json.loads(state_path.read_text(encoding="utf-8"))
            for phone, info in data.get("dynamic_troopers", {}).items():
                if not trooper_by_phone(phone):
                    TROOPERS.append(Trooper(
                        notion_name=info["name"],
                        display_name=info["name"],
                        phone=phone,
                        aliases=[info["name"]],
                    ))
    except Exception:
        pass


_load_dynamic_troopers()


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


def add_trooper(name: str, phone: str) -> Trooper:
    """Add a new trooper at runtime (from approved registration)."""
    t = Trooper(
        notion_name=name,
        display_name=name,
        phone=phone.lstrip("+").replace(" ", ""),
        aliases=[name],
    )
    TROOPERS.append(t)
    return t


def is_admin(phone: str) -> bool:
    return phone.lstrip("+").replace(" ", "") == ADMIN_PHONE

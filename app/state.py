"""Tiny JSON file persistence for the poller's last-seen cursor.

On Render's Cron Job tier the filesystem is ephemeral *between* runs but
that's fine — we instead persist the cursor in Notion itself by tagging a
sentinel page. As a fallback (local dev / web-service) we use a JSON file."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import config

_PATH = Path(config.STATE_FILE)


def _read() -> dict:
    if _PATH.exists():
        try:
            return json.loads(_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _write(data: dict) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_last_poll_iso() -> Optional[str]:
    return _read().get("last_poll_iso")


def set_last_poll_iso(iso: Optional[str] = None) -> str:
    iso = iso or datetime.now(timezone.utc).isoformat()
    data = _read()
    data["last_poll_iso"] = iso
    _write(data)
    return iso


def get_seen_task_ids() -> set[str]:
    return set(_read().get("seen_task_ids", []))


def add_seen_task_ids(ids: list[str]) -> None:
    data = _read()
    seen = set(data.get("seen_task_ids", []))
    seen.update(ids)
    data["seen_task_ids"] = sorted(seen)[-2000:]
    _write(data)

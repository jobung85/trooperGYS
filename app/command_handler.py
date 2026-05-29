"""Map an inbound WhatsApp text -> action -> reply."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional

import pytz

from . import config, notion_client

log = logging.getLogger(__name__)

HELP_TEXT = (
    "🤖 *Trooper Bot*\n"
    "Commands:\n"
    "• `tasks` — your pending tasks\n"
    "• `tasks all` — pending + last 5 done\n"
    "• `done <Task ID>` — mark a task as Done\n"
    "• `redo <Task ID>` — set a task back to Not started\n"
    "• `help` — show this menu"
)


def handle(from_phone: str, text: str) -> str:
    trooper = config.trooper_by_phone(from_phone)
    if trooper is None:
        return (
            "Hi! 👋 This number isn't registered as a Trooper yet.\n"
            "Please ask Jonathan to add it to the bot config."
        )

    raw = (text or "").strip()
    cmd = raw.lower()

    if not cmd or cmd in {"help", "/help", "?", "menu"}:
        return f"Hi {trooper.display_name}!\n\n{HELP_TEXT}"

    if cmd in {"tasks", "/tasks", "pending", "list"}:
        return _format_pending(trooper.notion_name, trooper.display_name)

    if cmd in {"tasks all", "/tasks all", "all"}:
        return _format_all(trooper.notion_name, trooper.display_name)

    m = re.match(r"^(done|finish|finished|selesai)\s+(.+)$", cmd, re.IGNORECASE)
    if m:
        return _mark(trooper.notion_name, raw_split_id(raw), "Done")

    m = re.match(r"^(redo|undo|reopen|belum)\s+(.+)$", cmd, re.IGNORECASE)
    if m:
        return _mark(trooper.notion_name, raw_split_id(raw), "Not started")

    return (
        f"I didn't understand that, {trooper.display_name}.\n\n{HELP_TEXT}"
    )


def raw_split_id(raw: str) -> str:
    """Take everything after the first whitespace and return as-is (preserves original casing of Task ID)."""
    parts = raw.split(None, 1)
    return parts[1].strip() if len(parts) > 1 else ""


def _format_pending(trooper_name: str, display: str) -> str:
    rows = notion_client.list_pending_for_trooper(trooper_name)
    if not rows:
        return f"🎉 {display}, you're clear — no pending tasks."
    lines = [f"📋 *Pending tasks for {display}* ({len(rows)})"]
    for i, r in enumerate(rows, 1):
        lines.append(f"{i}. *{r['task_id']}* — {r['status'] or 'Not started'}")
    lines.append("")
    lines.append("Reply `done <Task ID>` when finished.")
    return "\n".join(lines)


def _format_all(trooper_name: str, display: str) -> str:
    pending = notion_client.list_pending_for_trooper(trooper_name)
    done = notion_client.list_done_for_trooper(trooper_name, limit=5)
    out = [f"📋 *{display}'s board*", "", f"⏳ Pending ({len(pending)}):"]
    if not pending:
        out.append("  – none")
    else:
        for r in pending:
            out.append(f"  • {r['task_id']} — {r['status'] or 'Not started'}")
    out.append("")
    out.append("✅ Recently done (top 5):")
    if not done:
        out.append("  – none")
    else:
        for r in done:
            ts = (r.get("updated_at") or "")[:10]
            out.append(f"  • {r['task_id']}{f' ({ts})' if ts else ''}")
    return "\n".join(out)


def _mark(trooper_name: str, task_id: str, status: str) -> str:
    if not task_id:
        return "Please include a Task ID, e.g. `done T-001`"
    rows = notion_client.find_tracker_rows(task_id, trooper_name)
    if not rows:
        return (
            f"❓ I can't find Task `{task_id}` assigned to you.\n"
            "Send `tasks` to see your list."
        )
    today = datetime.now(pytz.timezone(config.TIMEZONE)).date().isoformat()
    notion_client.update_tracker_status(rows[0]["page_id"], status, comment_iso=today)
    icon = "✅" if status == "Done" else "↩️"
    return f"{icon} Got it. *{task_id}* set to *{status}*."

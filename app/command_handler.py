"""Map an inbound WhatsApp text -> action -> reply.

GROUP-CHAT SAFE:
- Only responds to messages that start with `/`.
- Returns None for everything else, so the Flask handler stays silent.

Commands:
    /help                                   show menu
    /tasks                                  pending list (with names)
    /tasks all                              pending + last 5 done
    /info <Task ID>                         full Main Task details
    /done <Task ID>                         mark Done
    /redo <Task ID>                         reopen
    /create <Task ID> | <Name> | <Link>     create Main Task + fan-out trackers
    /lang en | /lang id                     change language
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import List, Optional

import pytz

from . import config, notion_client, state
from .i18n import t

log = logging.getLogger(__name__)

COMMAND_PREFIX = "/"


def handle(from_phone: str, text: str) -> Optional[str]:
    """Process inbound text. Return reply string or None to stay silent."""
    raw = (text or "").strip()
    if not raw.startswith(COMMAND_PREFIX):
        return None

    body = raw[len(COMMAND_PREFIX):].strip()
    if not body:
        return None

    trooper = config.trooper_by_phone(from_phone)
    if trooper is None:
        return t(None, "not_registered")

    locale = state.get_language(from_phone) or "en"
    cmd_lc = body.lower()
    first_word = body.split(None, 1)[0].lower()
    args = body.split(None, 1)[1].strip() if len(body.split(None, 1)) > 1 else ""

    # ── /lang en | /lang id ──────────────────────────────────────────
    if first_word in {"lang", "language", "bahasa"}:
        return _change_language(from_phone, args)

    # ── /help ────────────────────────────────────────────────────────
    if first_word in {"help", "menu", "start", "commands", "?"}:
        return t(locale, "help_menu")

    # ── /tasks [all] ─────────────────────────────────────────────────
    if first_word in {"tasks", "pending", "list", "tugas"}:
        if args.lower() == "all":
            return _format_all(locale, trooper.notion_name, trooper.display_name)
        return _format_pending(locale, trooper.notion_name, trooper.display_name)

    # ── /info <id> ───────────────────────────────────────────────────
    if first_word in {"info", "detail", "details"}:
        return _format_info(locale, trooper.notion_name, args)

    # ── /create <id> | <name> | <link> ───────────────────────────────
    if first_word in {"create", "new", "buat", "tambah"}:
        return _create_task(locale, args)

    # ── /done <id> ───────────────────────────────────────────────────
    if first_word in {"done", "finish", "finished", "selesai", "sudah"}:
        return _mark(locale, trooper.notion_name, args, "Done")

    # ── /redo <id> ───────────────────────────────────────────────────
    if first_word in {"redo", "undo", "reopen", "belum", "buka"}:
        return _mark(locale, trooper.notion_name, args, "Not started")

    # ── unknown ──────────────────────────────────────────────────────
    return t(locale, "unknown", name=trooper.display_name)


# ─────────────────────────────  helpers  ──────────────────────────────

def _change_language(from_phone: str, arg: str) -> str:
    arg_lc = (arg or "").strip().lower()
    if arg_lc in {"en", "english"}:
        state.set_language(from_phone, "en")
        return t("en", "lang_set")
    if arg_lc in {"id", "indonesia", "bahasa", "bahasa indonesia"}:
        state.set_language(from_phone, "id")
        return t("id", "lang_set")
    locale = state.get_language(from_phone) or "en"
    return t(locale, "lang_usage")


def _format_pending(locale: str, trooper_name: str, display: str) -> str:
    rows = notion_client.list_pending_for_trooper(trooper_name)
    if not rows:
        return t(locale, "no_pending", name=display)

    main_lookup = notion_client.get_main_tasks_by_ids([r["task_id"] for r in rows])

    lines = [t(locale, "pending_header", name=display, count=len(rows))]
    for i, r in enumerate(rows, 1):
        m = main_lookup.get(r["task_id"])
        name = (m or {}).get("content_name") or "(no name)"
        lines.append(t(
            locale, "pending_row",
            idx=i, task_id=r["task_id"], name=name, status=r["status"] or "Not started",
        ))
    lines.append("")
    lines.append(t(locale, "pending_footer"))
    return "\n".join(lines)


def _format_all(locale: str, trooper_name: str, display: str) -> str:
    pending = notion_client.list_pending_for_trooper(trooper_name)
    done = notion_client.list_done_for_trooper(trooper_name, limit=5)
    main_lookup = notion_client.get_main_tasks_by_ids(
        [r["task_id"] for r in pending] + [r["task_id"] for r in done]
    )

    out: List[str] = [t(locale, "pending_header", name=display, count=len(pending))]
    if not pending:
        out.append(t(locale, "no_pending", name=display))
    else:
        for i, r in enumerate(pending, 1):
            m = main_lookup.get(r["task_id"])
            name = (m or {}).get("content_name") or "(no name)"
            out.append(t(
                locale, "pending_row",
                idx=i, task_id=r["task_id"], name=name, status=r["status"] or "Not started",
            ))
    out.append("")
    out.append(t(locale, "done_header"))
    if not done:
        out.append(t(locale, "done_none"))
    else:
        for r in done:
            m = main_lookup.get(r["task_id"])
            name = (m or {}).get("content_name") or "(no name)"
            ts = (r.get("updated_at") or "")[:10]
            out.append(t(locale, "done_row", task_id=r["task_id"], name=name, date=ts or "-"))
    return "\n".join(out)


def _format_info(locale: str, trooper_name: str, task_id: str) -> str:
    if not task_id:
        return t(locale, "missing_task_id")
    main = notion_client.find_main_task_by_id(task_id)
    if not main:
        return t(locale, "info_not_found", task_id=task_id)
    rows = notion_client.find_tracker_rows(task_id, trooper_name)
    status = rows[0]["status"] if rows else t(locale, "info_no_tracker")
    return t(
        locale, "info_block",
        task_id=main["task_id"],
        name=main.get("content_name") or "(no name)",
        created=main.get("create_date") or "-",
        complete=main.get("complete") or "No",
        link=main.get("link") or "(no link)",
        status=status,
    )


def _create_task(locale: str, rest: str) -> str:
    if not rest:
        return t(locale, "create_usage")

    parts = [p.strip() for p in rest.split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return t(locale, "create_usage")

    task_id = parts[0]
    content_name = parts[1]
    link = parts[2] if len(parts) >= 3 and parts[2] else None

    if notion_client.find_main_task_by_id(task_id):
        return t(locale, "create_dup", task_id=task_id)

    today = datetime.now(pytz.timezone(config.TIMEZONE)).date().isoformat()
    notion_client.create_main_task(task_id, content_name, link=link, create_date=today)

    created_for: List[str] = []
    for trooper in config.TROOPERS:
        existing = notion_client.find_tracker_rows(task_id, trooper.notion_name)
        if existing:
            continue
        notion_client.create_tracker_row(task_id, trooper.notion_name)
        created_for.append(trooper.display_name)

    return t(
        locale, "created_main",
        task_id=task_id,
        name=content_name,
        troopers=", ".join(created_for) or "-",
    )


def _mark(locale: str, trooper_name: str, task_id: str, status: str) -> str:
    if not task_id:
        return t(locale, "missing_task_id")
    rows = notion_client.find_tracker_rows(task_id, trooper_name)
    if not rows:
        return t(locale, "task_not_found_for_user", task_id=task_id)
    today = datetime.now(pytz.timezone(config.TIMEZONE)).date().isoformat()
    notion_client.update_tracker_status(rows[0]["page_id"], status, comment_iso=today)
    if status == "Done":
        return t(locale, "marked_done", task_id=task_id)
    return t(locale, "marked_redo", task_id=task_id)

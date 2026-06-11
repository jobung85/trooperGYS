"""Detect new Main Tasks, fan out Task Tracker rows for each Trooper,
and send a WhatsApp notification ONLY to Troopers who got a NEW row.

Idempotent: relies on Notion as the source of truth.
- If Task X has 0 tracker rows  -> create 4, notify 4 troopers.
- If Task X has 2 tracker rows  -> create the 2 missing ones, notify those 2 only.
- If Task X has 4 tracker rows  -> skip (silent no-op).

Designed to run as a GitHub Actions cron every 6 hours.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Iterable, List

from . import config, notion_client, state, whatsapp_client

log = logging.getLogger(__name__)


def _format_new_task(task: dict) -> str:
    lines = [
        "Trooper Bot - New Task",
        f"Task ID: *{task['task_id']}*",
    ]
    if task.get("content_name"):
        lines.append(f"Content: {task['content_name']}")
    if task.get("link"):
        lines.append(f"Link: {task['link']}")
    if task.get("create_date"):
        lines.append(f"Created: {task['create_date']}")
    lines.append("")
    lines.append("Reply with:")
    lines.append(f"- `done {task['task_id']}` once finished")
    lines.append("- `tasks` to see all your pending tasks")
    return "\n".join(lines)


def _ensure_tracker_rows(task_id: str) -> List[str]:
    """Make sure each Trooper has a Task Tracker row for this Task ID.
    Returns the list of trooper notion_names that were *newly* created."""
    created: List[str] = []
    for trooper in config.TROOPERS:
        existing = notion_client.find_tracker_rows(task_id, trooper.notion_name)
        if existing:
            continue
        notion_client.create_tracker_row(task_id, trooper.notion_name)
        created.append(trooper.notion_name)
        log.info("Created tracker row task=%s trooper=%s", task_id, trooper.notion_name)
    return created


def _notify_troopers(task: dict, trooper_names: Iterable[str]) -> int:
    """Send the WA notification via template (works without 24h window)."""
    sent = 0
    for name in trooper_names:
        t = config.trooper_by_notion_name(name)
        if not t:
            continue
        if not t.phone or "X" in t.phone.upper():
            log.warning("Skipping notify: trooper %s has no phone yet", name)
            continue
        try:
            whatsapp_client.send_new_task_notification(
                t.phone,
                t.display_name,
                task["task_id"],
                task.get("content_name", ""),
            )
            sent += 1
            log.info("Notified %s (%s) about %s", t.display_name, t.phone, task["task_id"])
        except Exception:
            log.exception("Failed to notify %s about %s", t.display_name, task["task_id"])
    return sent


def run_once() -> dict:
    """One poll cycle. Returns a small summary dict for logs / health."""
    last = state.get_last_poll_iso()
    if last:
        try:
            since_dt = datetime.fromisoformat(last.replace("Z", "+00:00")) - timedelta(days=1)
        except Exception:
            since_dt = datetime.now(timezone.utc) - timedelta(days=14)
    else:
        since_dt = datetime.now(timezone.utc) - timedelta(days=14)
    since_iso = since_dt.date().isoformat()

    log.info("Polling Main Task DB since %s (last=%s)", since_iso, last)
    tasks = notion_client.query_main_tasks_after(since_iso)
    log.info("Notion returned %d row(s)", len(tasks))

    notified_total = 0
    new_tasks_count = 0
    for task in tasks:
        if not task.get("task_id"):
            continue
        try:
            created = _ensure_tracker_rows(task["task_id"])
            if not created:
                log.debug("Task %s already fully mirrored, skipping notify", task["task_id"])
                continue
            new_tasks_count += 1
            sent = _notify_troopers(task, created)
            notified_total += sent
        except Exception:
            log.exception("Failed processing task %s", task.get("task_id"))

    state.set_last_poll_iso()

    summary = {
        "polled_since": since_iso,
        "fetched": len(tasks),
        "new_tasks_processed": new_tasks_count,
        "messages_sent": notified_total,
    }
    log.info("Poll summary: %s", summary)
    return summary


if __name__ == "__main__":
    run_once()

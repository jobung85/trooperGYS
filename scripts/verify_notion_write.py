"""Idempotent write-permission probe.

Creates a sentinel Task Tracker row with Task ID `__BOT_PROBE__` for one
trooper, then archives (trashes) it again. Safe to re-run.
"""
from __future__ import annotations

import sys

import requests

from app import config, notion_client

PROBE_TASK_ID = "__BOT_PROBE__"


def main() -> int:
    print(f"Notion DB Main Task     = {config.NOTION_MAIN_TASK_DB}")
    print(f"Notion DB Task Tracker  = {config.NOTION_TASK_TRACKER_DB}")

    print("[1/3] Read test: querying Main Task DB...")
    tasks = notion_client.query_main_tasks_after("2026-01-01")
    print(f"      OK ({len(tasks)} task(s) visible)")

    print("[2/3] Write test: creating sentinel Task Tracker row...")
    row = notion_client.create_tracker_row(PROBE_TASK_ID, "Sdr Jonathan")
    print(f"      OK (page_id={row['page_id']})")

    print("[3/3] Cleanup: archiving the sentinel row...")
    page_id = row["page_id"]
    r = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers={
            "Authorization": f"Bearer {config.NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
        json={"archived": True},
        timeout=30,
    )
    r.raise_for_status()
    print("      OK (archived)")
    print()
    print("SUCCESS: Notion connection is fully operational (read + write + archive).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

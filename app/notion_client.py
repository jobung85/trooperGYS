"""Thin Notion REST wrapper for the two Trooper databases."""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterator, List, Optional

import requests

from . import config

log = logging.getLogger(__name__)

API = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {config.NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


# ─────────────────────────────  internals  ──────────────────────────────

def _post(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(f"{API}{path}", headers=HEADERS, json=body, timeout=30)
    if r.status_code >= 300:
        log.error("Notion %s %s -> %s %s", "POST", path, r.status_code, r.text)
        r.raise_for_status()
    return r.json()


def _patch(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.patch(f"{API}{path}", headers=HEADERS, json=body, timeout=30)
    if r.status_code >= 300:
        log.error("Notion %s %s -> %s %s", "PATCH", path, r.status_code, r.text)
        r.raise_for_status()
    return r.json()


def _query_all(database_id: str, body: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    cursor: Optional[str] = None
    while True:
        payload = dict(body)
        if cursor:
            payload["start_cursor"] = cursor
        data = _post(f"/databases/{database_id}/query", payload)
        for r in data.get("results", []):
            yield r
        if not data.get("has_more"):
            return
        cursor = data.get("next_cursor")


# ─────────────────────────────  helpers  ───────────────────────────────

def _title(prop: Dict[str, Any]) -> str:
    arr = prop.get("title") or []
    return "".join(t.get("plain_text", "") for t in arr).strip()


def _rich_text(prop: Dict[str, Any]) -> str:
    arr = prop.get("rich_text") or []
    return "".join(t.get("plain_text", "") for t in arr).strip()


def _select_name(prop: Dict[str, Any]) -> str:
    sel = prop.get("select") or {}
    return sel.get("name", "") if sel else ""


def _status_name(prop: Dict[str, Any]) -> str:
    st = prop.get("status") or {}
    return st.get("name", "") if st else ""


def _date_start(prop: Dict[str, Any]) -> str:
    d = prop.get("date") or {}
    return (d or {}).get("start", "") if d else ""


def _url(prop: Dict[str, Any]) -> str:
    return prop.get("url") or ""


# ─────────────────────────────  Main Task  ─────────────────────────────

def query_main_tasks_after(iso_ts: Optional[str]) -> List[Dict[str, Any]]:
    """Return Main Task pages whose `Create Date` is on/after `iso_ts` (YYYY-MM-DD).
    If iso_ts is None, returns everything (use sparingly — first run only)."""
    body: Dict[str, Any] = {
        "sorts": [{"property": "Create Date", "direction": "ascending"}],
        "page_size": 100,
    }
    if iso_ts:
        body["filter"] = {
            "property": "Create Date",
            "date": {"on_or_after": iso_ts},
        }
    pages = list(_query_all(config.NOTION_MAIN_TASK_DB, body))
    return [_extract_main_task(p) for p in pages]


def _extract_main_task(page: Dict[str, Any]) -> Dict[str, Any]:
    p = page.get("properties", {})
    return {
        "page_id": page["id"],
        "task_id": _title(p.get("Name", {})),
        "content_name": _rich_text(p.get("Content Name", {})),
        "link": _url(p.get("Link", {})),
        "create_date": _date_start(p.get("Create Date", {})),
        "complete": _select_name(p.get("Complete", {})),
        "created_time": page.get("created_time", ""),
    }


# ───────────────────────────  Task Tracker  ────────────────────────────

def find_tracker_rows(task_id: str, trooper_name: Optional[str] = None) -> List[Dict[str, Any]]:
    filters = [{"property": "Task ID", "title": {"equals": task_id}}]
    if trooper_name:
        filters.append({"property": "Trooper", "select": {"equals": trooper_name}})
    body: Dict[str, Any] = {"filter": {"and": filters}, "page_size": 50}
    return [_extract_tracker_row(p) for p in _query_all(config.NOTION_TASK_TRACKER_DB, body)]


def list_pending_for_trooper(trooper_name: str) -> List[Dict[str, Any]]:
    body: Dict[str, Any] = {
        "filter": {
            "and": [
                {"property": "Trooper", "select": {"equals": trooper_name}},
                {"property": "Status", "status": {"does_not_equal": "Done"}},
            ]
        },
        "sorts": [{"property": "Updated at", "direction": "descending"}],
        "page_size": 100,
    }
    return [_extract_tracker_row(p) for p in _query_all(config.NOTION_TASK_TRACKER_DB, body)]


def list_done_for_trooper(trooper_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    body: Dict[str, Any] = {
        "filter": {
            "and": [
                {"property": "Trooper", "select": {"equals": trooper_name}},
                {"property": "Status", "status": {"equals": "Done"}},
            ]
        },
        "sorts": [{"property": "Updated at", "direction": "descending"}],
        "page_size": limit,
    }
    return [_extract_tracker_row(p) for p in _query_all(config.NOTION_TASK_TRACKER_DB, body)][:limit]


def create_tracker_row(task_id: str, trooper_name: str) -> Dict[str, Any]:
    body = {
        "parent": {"database_id": config.NOTION_TASK_TRACKER_DB},
        "properties": {
            "Task ID": {"title": [{"text": {"content": task_id}}]},
            "Trooper": {"select": {"name": trooper_name}},
            "Status": {"status": {"name": "Not started"}},
        },
    }
    page = _post("/pages", body)
    return _extract_tracker_row(page)


def update_tracker_status(page_id: str, status_name: str, comment_iso: Optional[str] = None) -> Dict[str, Any]:
    props: Dict[str, Any] = {"Status": {"status": {"name": status_name}}}
    if comment_iso:
        props["Comment Date"] = {"date": {"start": comment_iso}}
    return _patch(f"/pages/{page_id}", {"properties": props})


def _extract_tracker_row(page: Dict[str, Any]) -> Dict[str, Any]:
    p = page.get("properties", {})
    return {
        "page_id": page["id"],
        "task_id": _title(p.get("Task ID", {})),
        "trooper": _select_name(p.get("Trooper", {})),
        "status": _status_name(p.get("Status", {})),
        "comment_date": _date_start(p.get("Comment Date", {})),
        "updated_at": (p.get("Updated at") or {}).get("last_edited_time", ""),
    }

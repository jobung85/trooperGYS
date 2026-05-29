"""Offline command-handler tests (no WhatsApp API calls).

Bypasses Flask + WhatsApp send and exercises command_handler.handle()
directly so we can verify wiring fast.
"""
from __future__ import annotations

import sys

from app import command_handler, state

JONATHAN = "6281216977718"


def reset() -> None:
    # Clear any saved language so we test the fresh-default path
    data = state._read()
    data.setdefault("preferences", {}).pop(JONATHAN, None)
    state._write(data)


def show(label: str, raw: str) -> None:
    print("=" * 60)
    print(f"INPUT : {raw!r}")
    reply = command_handler.handle(JONATHAN, raw)
    if reply is None:
        print(f"REPLY : <silent (no `/`)>")
    else:
        print(f"REPLY :\n{reply}")
    print()


def main() -> int:
    reset()

    show("plain text (should be silent)", "hello there")
    show("plain /", "/")
    show("/help (default = en)", "/help")
    show("/lang id", "/lang id")
    show("/help (id)", "/help")
    show("/tasks (id)", "/tasks")
    show("/info 0001 (id)", "/info 0001")
    show("/info 0002 (id)", "/info 0002")
    show("/info nonexistent", "/info ZZZZ")
    show("/lang en", "/lang en")
    show("/done MISSING", "/done DOESNOTEXIST")
    show("/create no args", "/create")
    show("/create wrong format", "/create 9999")
    show("unknown", "/foobar")

    print("=" * 60)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Entry point for the Render Cron Job.

Render runs:   python -m scripts.poll_once
"""
from __future__ import annotations

import json
import sys

from app import poller


def main() -> int:
    summary = poller.run_once()
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

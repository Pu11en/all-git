"""Description parsing and catalog synchronization."""

from __future__ import annotations

import re
from typing import Any

GITHUB_LINE = re.compile(  # en dash accepted via \u2013 for channels that typeset it
    r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[-\u2013]\s*(.+?)\s*(https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?))(?:[/?#\s]|$)"
)
TIMESTAMP = re.compile(r"^(\d+):(\d{2})(?::(\d{2}))?$")


def parse_description(description: str) -> list[dict[str, Any]]:
    """Extract repo mentions from a GitHub Awesome video description."""
    mentions: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for line in description.splitlines():
        match = GITHUB_LINE.match(line)
        if match is None:
            continue
        stamp, display, url, owner, name = match.groups()
        seconds = _seconds(stamp)
        if seconds is None:
            continue
        key = (f"{owner.lower()}/{name.lower()}", seconds)
        if key in seen:
            continue
        seen.add(key)
        mentions.append(
            {
                "timestamp_seconds": seconds,
                "display_name": display.strip()[:200],
                "url": url,
                "owner": owner,
                "name": name.rstrip("."),
            }
        )
    return mentions


def _seconds(stamp: str) -> int | None:
    match = TIMESTAMP.match(stamp)
    if match is None:
        return None
    if match.group(3) is None:
        minutes, seconds = int(match.group(1)), int(match.group(2))
        return minutes * 60 + seconds
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + int(match.group(3))

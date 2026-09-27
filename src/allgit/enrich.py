"""Optional GitHub API enrichment for catalog repos."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from allgit.db import Repository

API = "https://api.github.com/repos/{owner}/{name}"
UNAUTHENTICATED_BUDGET = 45


def _token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def _budget() -> int:
    return 5000 if _token() else UNAUTHENTICATED_BUDGET


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "all-git",
    }
    token = _token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class RateLimited(Exception):
    """GitHub refused further requests for now; stop and keep what we have."""


# Repos GitHub will not serve: gone (404/410) or blocked, e.g. DMCA (451).
_DEAD_CODES = {404, 410, 451}


def _fetch(owner: str, name: str) -> dict[str, Any] | None:
    request = urllib.request.Request(API.format(owner=owner, name=name), headers=_headers())
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in _DEAD_CODES:
            return {"dead": True}
        if exc.code in (403, 429):  # primary and secondary rate limits
            raise RateLimited(str(exc)) from exc
        return None
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None
    return {
        "gh_description": data.get("description"),
        "stars": data.get("stargazers_count"),
        "language": data.get("language"),
        "archived": bool(data.get("archived")),
        "pushed_at": data.get("pushed_at"),
        "dead": False,
    }


def enrich(repo: Repository, limit: int | None = None) -> dict[str, int]:
    """Fill GitHub metadata for repos that have none; never raises on API trouble."""
    budget = _budget()
    cap = min(budget, limit) if limit is not None else budget
    pending = repo.repos_missing_meta(limit=cap)
    enriched = dead = skipped = 0
    rate_limited = False
    for row in pending:
        try:
            meta = _fetch(row["owner"], row["name"])
        except RateLimited:
            rate_limited = True
            break
        if meta is None:
            skipped += 1
            continue
        repo.set_repo_meta(row["repo_id"], meta)
        if meta.get("dead"):
            dead += 1
        else:
            enriched += 1
        time.sleep(0.12)
    repo.rebuild_search_index()
    counts = repo.counts()
    return {
        "enriched": enriched,
        "marked_dead": dead,
        "skipped": skipped,
        "rate_limited": int(rate_limited),
        "remaining": counts["repos"] - counts["enriched"],
    }

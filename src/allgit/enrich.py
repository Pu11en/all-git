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


def _fetch(owner: str, name: str) -> dict[str, Any] | None:
    request = urllib.request.Request(API.format(owner=owner, name=name), headers=_headers())
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"dead": True}
        raise
    return {
        "gh_description": data.get("description"),
        "stars": data.get("stargazers_count"),
        "language": data.get("language"),
        "archived": bool(data.get("archived")),
        "pushed_at": data.get("pushed_at"),
        "dead": False,
    }


def enrich(repo: Repository, limit: int | None = None) -> dict[str, int]:
    budget = _budget()
    cap = min(budget, limit) if limit is not None else budget
    pending = repo.repos_missing_meta(limit=cap)
    enriched = 0
    dead = 0
    for row in pending:
        meta = _fetch(row["owner"], row["name"])
        if meta is None:
            continue
        repo.set_repo_meta(row["repo_id"], meta)
        if meta.get("dead"):
            dead += 1
        else:
            enriched += 1
        time.sleep(0.12)
    repo.rebuild_search_index()
    return {"enriched": enriched, "marked_dead": dead, "remaining": max(0, len(pending) - cap + 0)}

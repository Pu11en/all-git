"""Catalog synchronization: listing, descriptions, captions, linking, indexing."""

from __future__ import annotations

import logging
from typing import Any

from filelock import FileLock

from allgit import youtube
from allgit.catalog import parse_description
from allgit.config import CHANNEL_URL, lock_path
from allgit.db import Repository

logger = logging.getLogger(__name__)


def sync_catalog(
    repo: Repository,
    *,
    channel_url: str = CHANNEL_URL,
    fetch_captions: bool = True,
    max_descriptions: int | None = None,
    max_captions: int | None = None,
) -> dict[str, Any]:
    """Bring the catalog up to date with the channel. Serialized via lock."""
    with FileLock(str(lock_path())):
        return _sync(repo, channel_url, fetch_captions, max_descriptions, max_captions)


def _sync(
    repo: Repository,
    channel_url: str,
    fetch_captions: bool,
    max_descriptions: int | None,
    max_captions: int | None,
) -> dict[str, Any]:
    before = repo.counts()
    report: dict[str, Any] = {
        "videos_seen": 0,
        "descriptions_fetched": 0,
        "captions_fetched": 0,
        "errors": [],
    }

    listing = youtube.extract_listing(channel_url)
    report["videos_seen"] = len(listing)
    with repo.reading() as conn:
        known_ids = {r[0] for r in conn.execute("SELECT video_id FROM videos").fetchall()}
    for video in listing:
        if video["video_id"] not in known_ids:
            repo.upsert_video(video)
            known_ids.add(video["video_id"])

    for video in repo.videos_missing_description(limit=max_descriptions):
        try:
            description = youtube.fetch_description(video["video_id"])
        except Exception as exc:
            report["errors"].append(f"{video['video_id']}: {exc}")
            if youtube.is_rate_limited(exc):
                break
            continue
        repo.set_video_description(video["video_id"], description)
        report["descriptions_fetched"] += 1
        if not description:
            continue
        for mention in parse_description(description):
            repo_id = repo.upsert_repo(
                mention["owner"],
                mention["name"],
                mention["url"],
                mention["display_name"],
                video["video_id"],
            )
            repo.add_mention(
                repo_id,
                video["video_id"],
                mention["timestamp_seconds"],
                mention["display_name"],
            )

    if fetch_captions:
        for video in repo.videos_missing_captions(limit=max_captions):
            try:
                chunks = youtube.fetch_caption_chunks(video["video_id"])
            except Exception as exc:
                report["errors"].append(f"captions {video['video_id']}: {exc}")
                if youtube.is_rate_limited(exc):
                    break
                continue
            if chunks:
                repo.replace_chunks(video["video_id"], chunks)
                repo.link_mention_excerpts(video["video_id"])
                report["captions_fetched"] += 1
            repo.set_video_caption_fetched(video["video_id"])

    # Link any video whose captions exist but whose mentions were never joined to
    # them; without this the search index stays name-only for those repos forever.
    relinked = 0
    for video_id in repo.videos_needing_excerpt_link():
        relinked += repo.link_mention_excerpts(video_id)
    report["excerpts_relinked"] = relinked

    repo.rebuild_search_index()
    after = repo.counts()
    report["new_videos"] = after["videos"] - before["videos"]
    report["new_repos"] = after["repos"] - before["repos"]
    report["new_mentions"] = after["mentions"] - before["mentions"]
    report["counts"] = after
    return report

"""YouTube access: channel listing, descriptions, and captions via yt-dlp."""

from __future__ import annotations

import re
import time
from typing import Any

import webvtt

from allgit.config import DEFAULT_LANGUAGE, REQUEST_PAUSE_SECONDS

_ytdl_base: dict[str, Any] = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": False,
    "skip_download": True,
    "sleep_interval_requests": 0,
    "retries": 3,
    "socket_timeout": 30,
}


def _client() -> Any:
    from yt_dlp import YoutubeDL

    return YoutubeDL(dict(_ytdl_base))


def _sleep() -> None:
    time.sleep(REQUEST_PAUSE_SECONDS)


def is_rate_limited(exc: Exception) -> bool:
    message = str(exc).lower()
    return "429" in message or "too many requests" in message


def extract_listing(channel_url: str) -> list[dict[str, Any]]:
    """Return regular videos of a channel as dicts with video_id/title/upload_date."""
    from yt_dlp import YoutubeDL

    options = dict(
        _ytdl_base,
        extract_flat="in_playlist",
        playlistend=1000,
    )
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(f"{channel_url.rstrip('/')}/videos", download=False)
    entries = (info or {}).get("entries") or []
    videos: list[dict[str, Any]] = []
    for entry in entries:
        if not entry:
            continue
        video_id = entry.get("id")
        if not video_id or not _is_video_id(str(video_id)):
            continue
        videos.append(
            {
                "video_id": str(video_id),
                "title": str(entry.get("title") or "Untitled")[:200],
                "upload_date": _normalize_date(entry.get("upload_date")),
                "webpage_url": f"https://youtu.be/{video_id}",
            }
        )
    return videos


def _is_video_id(value: str) -> bool:
    return re.fullmatch(r"[A-Za-z0-9_-]{11}", value) is not None


def _normalize_date(value: Any) -> str | None:
    if isinstance(value, str) and re.fullmatch(r"\d{8}", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return None


def fetch_description(video_id: str) -> str | None:
    """Fetch a video description, tolerating missing values."""
    with _client() as ydl:
        info = ydl.extract_info(f"https://youtu.be/{video_id}", download=False)
    description = (info or {}).get("description")
    return str(description) if description else None


def fetch_caption_chunks(video_id: str, language: str = DEFAULT_LANGUAGE) -> list[dict[str, int | str]]:
    """Fetch caption text as ~45s chunks with millisecond ranges."""
    with _client() as ydl:
        info = ydl.extract_info(f"https://youtu.be/{video_id}", download=False)
    tracks = ((info or {}).get("subtitles") or {}).get(language) or []
    track = next((t for t in tracks if t.get("ext") == "vtt"), None)
    if track is None:
        return []
    vtt_text = ydl.urlopen(track["url"]).read().decode("utf-8", errors="replace")
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile("w", suffix=".vtt", delete=False) as handle:
        handle.write(vtt_text)
        path = handle.name
    chunks: list[dict[str, int | str]] = []
    try:
        buffer: list[str] = []
        start_ms = 0
        end_ms = 0
        for cue in webvtt.read(path):
            cue_start, cue_end = _ms(cue.start), _ms(cue.end)
            if not buffer:
                start_ms = cue_start
            buffer.append(cue.text.replace("\n", " ").strip())
            end_ms = cue_end
            if end_ms - start_ms >= 40_000 or len(" ".join(buffer)) >= 900:
                chunks.append(
                    {
                        "chunk_index": len(chunks),
                        "start_ms": start_ms,
                        "end_ms": end_ms,
                        "text": " ".join(buffer),
                    }
                )
                buffer = []
        if buffer:
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "text": " ".join(buffer),
                }
            )
    finally:
        Path(path).unlink(missing_ok=True)
    return chunks


def _ms(stamp: str) -> int:
    parts = stamp.replace(",", ".").split(":")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return int(seconds * 1000)

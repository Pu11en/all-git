"""Import caption chunks from a Channel Brains archive database into all-git.

Usage:
    uv run python scripts/import_channel_brains.py /path/to/channel_brains.sqlite3 [brain_id]

Skips videos all-git already has chunks for. Safe to re-run.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from allgit.config import get_data_dir
from allgit.db import Repository


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    source = Path(sys.argv[1])
    brain_id = sys.argv[1 + 1] if len(sys.argv) > 2 else None
    if not source.exists():
        raise SystemExit(f"source database not found: {source}")

    repo = Repository(get_data_dir() / "catalog.sqlite3")
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row

    where = "WHERE brain_id = ?" if brain_id else ""
    params = (brain_id,) if brain_id else ()
    videos = src.execute(
        f"""SELECT video_id, title, upload_date FROM videos {where}""", params
    ).fetchall()

    imported = 0
    have = repo.video_ids_with_captions()
    for video in videos:
        video_id = video["video_id"]
        chunks = src.execute(
            """SELECT chunk_index, start_ms, end_ms, text FROM chunks
               WHERE video_id = ? ORDER BY chunk_index""",
            (video_id,),
        ).fetchall()
        if not chunks or video_id in have:
            continue
        repo.upsert_video(
            {
                "video_id": video_id,
                "title": video["title"] or "Untitled",
                "upload_date": None,
                "webpage_url": f"https://youtu.be/{video_id}",
            }
        )
        repo.replace_chunks(video_id, [dict(c) for c in chunks])
        repo.set_video_caption_fetched(video_id)
        imported += 1

    repo.rebuild_search_index()
    src.close()
    print(f"imported captions for {imported} videos; counts: {repo.counts()}")


if __name__ == "__main__":
    main()

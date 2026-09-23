from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'GithubAwesome',
    upload_date TEXT,
    webpage_url TEXT,
    description TEXT,
    description_fetched_at TEXT,
    caption_fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS repos (
    repo_id INTEGER PRIMARY KEY,
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    display_names TEXT NOT NULL DEFAULT '',
    first_seen_video TEXT,
    last_seen_at TEXT,
    mention_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE (owner, name)
);
CREATE TABLE IF NOT EXISTS mentions (
    mention_id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL REFERENCES repos(repo_id) ON DELETE CASCADE,
    video_id TEXT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    timestamp_seconds INTEGER NOT NULL,
    display_name TEXT NOT NULL,
    excerpt TEXT,
    UNIQUE (repo_id, video_id, timestamp_seconds)
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id INTEGER PRIMARY KEY,
    video_id TEXT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    text TEXT NOT NULL,
    UNIQUE (video_id, chunk_index)
);
CREATE TABLE IF NOT EXISTS repo_meta (
    repo_id INTEGER PRIMARY KEY REFERENCES repos(repo_id) ON DELETE CASCADE,
    gh_description TEXT,
    stars INTEGER,
    language TEXT,
    archived INTEGER,
    pushed_at TEXT,
    dead INTEGER NOT NULL DEFAULT 0,
    fetched_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_mentions_repo ON mentions(repo_id);
CREATE INDEX IF NOT EXISTS idx_mentions_video ON mentions(video_id);
CREATE INDEX IF NOT EXISTS idx_chunks_video ON chunks(video_id);
CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(
    repo_id UNINDEXED, owner, name, names, body
);
CREATE TRIGGER IF NOT EXISTS repos_ai AFTER INSERT ON repos BEGIN
    INSERT INTO search_fts (repo_id, owner, name, names, body)
    VALUES (new.repo_id, new.owner, new.name, '', '');
END;
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def clean_tokens(query: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_]{2,}", query)
    return [t for t in tokens if t.lower() not in {"the", "and", "for", "with", "that"}]


class Repository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        with self.transaction() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def transaction(self):
        conn = connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def reading(self):
        conn = connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    # -- videos -------------------------------------------------------
    def upsert_video(self, video: dict[str, Any]) -> None:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO videos (video_id, title, upload_date, webpage_url)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(video_id) DO UPDATE SET
                     title=excluded.title,
                     upload_date=excluded.upload_date,
                     webpage_url=excluded.webpage_url""",
                (
                    video["video_id"],
                    video["title"],
                    video.get("upload_date"),
                    video.get("webpage_url"),
                ),
            )

    def set_video_description(self, video_id: str, description: str | None) -> None:
        with self.transaction() as conn:
            conn.execute(
                "UPDATE videos SET description=?, description_fetched_at=? WHERE video_id=?",
                (description, now_iso(), video_id),
            )

    def set_video_caption_fetched(self, video_id: str) -> None:
        with self.transaction() as conn:
            conn.execute(
                "UPDATE videos SET caption_fetched_at=? WHERE video_id=?", (now_iso(), video_id)
            )

    def videos_missing_description(self, limit: int | None = None) -> list[dict[str, Any]]:
        return self._videos_where("description_fetched_at IS NULL", limit)

    def videos_missing_captions(self, limit: int | None = None) -> list[dict[str, Any]]:
        return self._videos_where("description_fetched_at IS NOT NULL AND caption_fetched_at IS NULL", limit)

    def _videos_where(self, where: str, limit: int | None) -> list[dict[str, Any]]:
        sql = f"SELECT * FROM videos WHERE {where} ORDER BY upload_date DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self.reading() as conn:
            return [dict(r) for r in conn.execute(sql).fetchall()]

    def videos_needing_excerpt_link(self) -> list[str]:
        """Videos whose captions exist but whose mentions were never linked to them.

        Mentions are created from the description pass and excerpts from the caption
        pass. When those land in different runs the link is missed, and because
        caption_fetched_at is already set the caption pass never revisits the video.
        """
        with self.reading() as conn:
            return [
                r[0]
                for r in conn.execute(
                    """SELECT DISTINCT m.video_id FROM mentions m
                       WHERE (m.excerpt IS NULL OR m.excerpt = '')
                         AND EXISTS (SELECT 1 FROM chunks c WHERE c.video_id = m.video_id)"""
                ).fetchall()
            ]

    def video_ids_with_captions(self) -> set[str]:
        with self.reading() as conn:
            return {r[0] for r in conn.execute("SELECT DISTINCT video_id FROM chunks")}

    def replace_chunks(self, video_id: str, chunks: list[dict[str, Any]]) -> None:
        with self.transaction() as conn:
            conn.execute("DELETE FROM chunks WHERE video_id=?", (video_id,))
            conn.executemany(
                """INSERT OR REPLACE INTO chunks
                   (video_id, chunk_index, start_ms, end_ms, text) VALUES (?,?,?,?,?)""",
                [
                    (
                        video_id,
                        int(c["chunk_index"]),
                        int(c["start_ms"]),
                        int(c["end_ms"]),
                        c["text"],
                    )
                    for c in chunks
                ],
            )

    # -- repos and mentions --------------------------------------------
    def upsert_repo(self, owner: str, name: str, url: str, display_name: str, video_id: str) -> int:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT repo_id, display_names FROM repos WHERE owner=? AND name=?",
                (owner, name),
            ).fetchone()
            if row is None:
                conn.execute(
                    """INSERT INTO repos (owner, name, url, display_names, first_seen_video, last_seen_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (owner, name, url, display_name, video_id, now_iso()),
                )
                repo_id = int(
                    conn.execute(
                        "SELECT repo_id FROM repos WHERE owner=? AND name=?", (owner, name)
                    ).fetchone()[0]
                )
            else:
                repo_id = int(row["repo_id"])
                names = [n for n in row["display_names"].split("|") if n]
                if display_name and display_name not in names:
                    names.append(display_name)
                conn.execute(
                    """UPDATE repos SET display_names=?, last_seen_at=? WHERE repo_id=?""",
                    ("|".join(names), now_iso(), repo_id),
                )
            return repo_id

    def add_mention(
        self, repo_id: int, video_id: str, timestamp_seconds: int, display_name: str
    ) -> None:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO mentions (repo_id, video_id, timestamp_seconds, display_name, excerpt)
                   VALUES (?, ?, ?, ?, NULL)
                   ON CONFLICT(repo_id, video_id, timestamp_seconds) DO NOTHING""",
                (repo_id, video_id, timestamp_seconds, display_name),
            )
            conn.execute(
                "UPDATE repos SET mention_count=(SELECT COUNT(*) FROM mentions WHERE repo_id=?)",
                (repo_id,),
            )

    def link_mention_excerpts(self, video_id: str) -> int:
        """Attach the nearest caption chunk to each mention of one video."""
        with self.transaction() as conn:
            mentions = conn.execute(
                "SELECT mention_id, timestamp_seconds FROM mentions WHERE video_id=?",
                (video_id,),
            ).fetchall()
            chunks = conn.execute(
                "SELECT chunk_id, start_ms, end_ms, text FROM chunks WHERE video_id=? ORDER BY start_ms",
                (video_id,),
            ).fetchall()
            if not chunks:
                return 0
            linked = 0
            for m in mentions:
                ts_ms = int(m["timestamp_seconds"]) * 1000
                best = min(
                    chunks,
                    key=lambda c: abs(((c["start_ms"] + c["end_ms"]) // 2) - ts_ms),
                    default=None,
                )
                if best is None:
                    continue
                if abs(((best["start_ms"] + best["end_ms"]) // 2) - ts_ms) > 120_000:
                    continue
                conn.execute(
                    "UPDATE mentions SET excerpt=? WHERE mention_id=?",
                    (best["text"][:600], m["mention_id"]),
                )
                linked += 1
            return linked

    def rebuild_search_index(self) -> None:
        with self.transaction() as conn:
            rows = conn.execute(
                """SELECT r.repo_id, r.owner, r.name, r.display_names,
                          COALESCE(m.gh_description, '') AS gh,
                          (SELECT GROUP_CONCAT(COALESCE(x.excerpt, ''), ' ')
                           FROM mentions x WHERE x.repo_id = r.repo_id) AS prose
                   FROM repos r LEFT JOIN repo_meta m ON m.repo_id = r.repo_id"""
            ).fetchall()
            conn.execute("DELETE FROM search_fts")
            conn.executemany(
                "INSERT INTO search_fts (repo_id, owner, name, names, body) VALUES (?,?,?,?,?)",
                [
                    (
                        r["repo_id"],
                        r["owner"],
                        r["name"],
                        r["display_names"],
                        f"{r['gh']} {r['prose'] or ''}"[:20000],
                    )
                    for r in rows
                ],
            )

    def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        tokens = clean_tokens(query)
        if not tokens:
            return []
        match = " OR ".join(f'"{t}"' for t in tokens)
        with self.reading() as conn:
            rows = conn.execute(
                """SELECT f.repo_id, bm25(search_fts, 3.0, 3.0, 2.0, 1.0) AS score
                   FROM search_fts f WHERE search_fts MATCH ?
                   ORDER BY score LIMIT ?""",
                (match, int(limit)),
            ).fetchall()
            results = []
            for row in rows:
                detail = conn.execute(
                    """SELECT r.*, m.stars, m.language, m.archived, m.dead,
                              (SELECT COUNT(*) FROM mentions x WHERE x.repo_id=r.repo_id) AS mentions
                       FROM repos r LEFT JOIN repo_meta m ON m.repo_id=r.repo_id
                       WHERE r.repo_id=?""",
                    (row["repo_id"],),
                ).fetchone()
                if detail is None:
                    continue
                mention = conn.execute(
                    """SELECT x.*, v.title AS video_title FROM mentions x
                       JOIN videos v ON v.video_id = x.video_id
                       WHERE x.repo_id=? ORDER BY x.timestamp_seconds LIMIT 1""",
                    (row["repo_id"],),
                ).fetchone()
                d = dict(detail)
                if mention is not None:
                    d["evidence_video"] = mention["video_id"]
                    d["evidence_title"] = mention["video_title"]
                    d["evidence_timestamp"] = mention["timestamp_seconds"]
                    d["evidence_url"] = f"https://youtu.be/{mention['video_id']}?t={mention['timestamp_seconds']}"
                    d["evidence_excerpt"] = mention["excerpt"]
                results.append(d)
            return results

    def get_repo(self, owner: str, name: str) -> dict[str, Any] | None:
        with self.reading() as conn:
            row = conn.execute(
                """SELECT r.*, m.stars, m.language, m.archived, m.dead,
                          m.gh_description, m.pushed_at
                   FROM repos r LEFT JOIN repo_meta m ON m.repo_id=r.repo_id
                   WHERE lower(r.owner)=lower(?) AND lower(r.name)=lower(?)""",
                (owner, name),
            ).fetchone()
            if row is None:
                return None
            detail = dict(row)
            detail["mentions"] = [
                dict(m)
                for m in conn.execute(
                    """SELECT x.video_id, x.timestamp_seconds, x.display_name, x.excerpt,
                              v.title AS video_title,
                              'https://youtu.be/' || x.video_id || '?t=' || x.timestamp_seconds AS url
                       FROM mentions x JOIN videos v ON v.video_id=x.video_id
                       WHERE x.repo_id=? ORDER BY x.timestamp_seconds""",
                    (row["repo_id"],),
                ).fetchall()
            ]
            return detail

    def counts(self) -> dict[str, int]:
        with self.reading() as conn:
            return {
                "videos": conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0],
                "descriptions": conn.execute(
                    "SELECT COUNT(*) FROM videos WHERE description_fetched_at IS NOT NULL"
                ).fetchone()[0],
                "captioned_videos": conn.execute(
                    "SELECT COUNT(DISTINCT video_id) FROM chunks"
                ).fetchone()[0],
                "repos": conn.execute("SELECT COUNT(*) FROM repos").fetchone()[0],
                "mentions": conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0],
                "enriched": conn.execute(
                    "SELECT COUNT(*) FROM repo_meta WHERE fetched_at IS NOT NULL"
                ).fetchone()[0],
                "dead": conn.execute(
                    "SELECT COUNT(*) FROM repo_meta WHERE dead=1"
                ).fetchone()[0],
            }

    def repos_missing_meta(self, limit: int) -> list[dict[str, Any]]:
        with self.reading() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    """SELECT r.repo_id, r.owner, r.name FROM repos r
                       LEFT JOIN repo_meta m ON m.repo_id=r.repo_id
                       WHERE m.repo_id IS NULL OR m.fetched_at IS NULL
                       LIMIT ?""",
                    (int(limit),),
                ).fetchall()
            ]

    def set_repo_meta(self, repo_id: int, meta: dict[str, Any]) -> None:
        with self.transaction() as conn:
            conn.execute(
                """INSERT INTO repo_meta (repo_id, gh_description, stars, language, archived, dead, pushed_at, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(repo_id) DO UPDATE SET
                     gh_description=excluded.gh_description, stars=excluded.stars,
                     language=excluded.language, archived=excluded.archived,
                     dead=excluded.dead, pushed_at=excluded.pushed_at,
                     fetched_at=excluded.fetched_at""",
                (
                    repo_id,
                    meta.get("gh_description"),
                    meta.get("stars"),
                    meta.get("language"),
                    1 if meta.get("archived") else 0,
                    1 if meta.get("dead") else 0,
                    meta.get("pushed_at"),
                    now_iso(),
                ),
            )

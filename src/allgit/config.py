from __future__ import annotations

import os
from pathlib import Path

VERSION = "0.1.3"
APP_NAME = "allgit"
CHANNEL_URL = "https://www.youtube.com/@GithubAwesome"
DEFAULT_LANGUAGE = "en"
MAX_SEARCH_RESULTS = 20
REQUEST_PAUSE_SECONDS = 0.25
BUNDLED_CATALOG_ENV = "ALLGIT_BUNDLED_CATALOG"


def get_data_dir() -> Path:
    """Return ALLGIT_HOME when set, otherwise the platform user data directory."""
    env = os.environ.get("ALLGIT_HOME")
    if env:
        return Path(env)
    return Path(platformdirs_data_path())


def platformdirs_data_path() -> Path:
    import platformdirs

    return Path(platformdirs.user_data_path(APP_NAME))


def bundled_catalog_path() -> Path | None:
    """Path to the catalog shipped inside the package, if present."""
    env = os.environ.get(BUNDLED_CATALOG_ENV)
    if env:
        path = Path(env)
        return path if path.exists() else None
    path = Path(__file__).parent / "catalog.sqlite3"
    return path if path.exists() else None


def _coverage(path: Path) -> tuple[int, int]:
    """(videos, captioned videos) in a catalog; (0, 0) when unreadable."""
    import sqlite3

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            videos = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
            captioned = conn.execute("SELECT COUNT(DISTINCT video_id) FROM chunks").fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error:
        return (0, 0)
    return (videos, captioned)


def catalog_path() -> Path:
    """User catalog location; seeded from the bundled catalog on first use.

    An upgraded package ships a newer bundled catalog, so a local catalog with
    less coverage than the bundled one is replaced by it.
    """
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "catalog.sqlite3"
    seed = bundled_catalog_path()
    if seed is not None and (not path.exists() or _coverage(seed) > _coverage(path)):
        staged = data_dir / "catalog.sqlite3.new"
        staged.write_bytes(seed.read_bytes())
        for suffix in ("-wal", "-shm"):
            Path(f"{path}{suffix}").unlink(missing_ok=True)
        os.replace(staged, path)
    return path


def lock_path() -> Path:
    return get_data_dir() / "update.lock"

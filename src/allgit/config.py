from __future__ import annotations

import os
from pathlib import Path

VERSION = "0.1.0"
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


def catalog_path() -> Path:
    """User catalog location; seeded from the bundled catalog on first use."""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "catalog.sqlite3"
    if not path.exists():
        seed = bundled_catalog_path()
        if seed is not None:
            path.write_bytes(seed.read_bytes())
    return path


def lock_path() -> Path:
    return get_data_dir() / "update.lock"

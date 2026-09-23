"""Refresh the bundled catalog from the live channel and export it into the package.

Runs the standard update against the user catalog location, then copies the
resulting database into src/allgit/catalog.sqlite3 for committing.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from allgit.config import catalog_path
from allgit.db import Repository
from allgit.sync import sync_catalog


def main() -> None:
    target = catalog_path()
    repo = Repository(target)
    report = sync_catalog(repo)
    print(report["counts"])
    destination = Path(__file__).resolve().parents[1] / "src" / "allgit" / "catalog.sqlite3"
    shutil.copyfile(target, destination)
    print(f"bundled catalog written to {destination}")


if __name__ == "__main__":
    main()

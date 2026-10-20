"""Refresh the bundled catalog from the live channel and export it into the package.

Runs the standard update against the user catalog location, then writes a
compact copy to src/allgit/catalog.sqlite3 for committing. The copy is only
rewritten when the catalog's coverage changed, so a refresh that found nothing
new leaves the committed file (and git history) untouched. Pass --force to
export regardless.
"""

from __future__ import annotations

import sys
from pathlib import Path

from allgit.config import catalog_path
from allgit.db import Repository
from allgit.enrich import enrich
from allgit.sync import sync_catalog

DESTINATION = Path(__file__).resolve().parents[1] / "src" / "allgit" / "catalog.sqlite3"


def main() -> None:
    force = "--force" in sys.argv[1:]
    repo = Repository(catalog_path())
    before = repo.counts()
    report = sync_catalog(repo)
    print(report["counts"])
    print(enrich(repo))
    after = repo.counts()
    if after == before and DESTINATION.exists() and not force:
        print("catalog coverage unchanged; bundled copy left as is")
        return
    repo.export(DESTINATION)
    print(f"bundled catalog written to {DESTINATION}")


if __name__ == "__main__":
    main()

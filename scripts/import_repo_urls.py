"""Add repos from a list of GitHub URLs (for example a scrape of curated X posts).

Usage:
    uv run python scripts/import_repo_urls.py URLS_FILE [--source x] [--enrich]

URLS_FILE is any text containing github.com/owner/name links, one or many per
line. Repos already in the catalog are left as they are, so re-running is
safe. With --enrich, GitHub metadata is fetched for repos that have none
(set GITHUB_TOKEN for a larger budget). The search index is rebuilt either way.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from allgit.catalog import parse_repo_urls
from allgit.config import catalog_path
from allgit.db import SOURCE_X, Repository
from allgit.enrich import enrich


def import_urls(repo: Repository, text: str, source: str) -> int:
    before = repo.counts()["repos"]
    for entry in parse_repo_urls(text):
        repo.upsert_repo(entry["owner"], entry["name"], entry["url"], "", None, source=source)
    return repo.counts()["repos"] - before


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("urls_file", type=Path)
    parser.add_argument("--source", default=SOURCE_X, help="origin label stored on new repos")
    parser.add_argument("--enrich", action="store_true", help="fetch GitHub metadata afterwards")
    args = parser.parse_args()

    repo = Repository(catalog_path())
    added = import_urls(repo, args.urls_file.read_text(encoding="utf-8"), args.source)
    print(f"added {added} repos from {args.urls_file} (source={args.source})")
    if args.enrich:
        print(enrich(repo))
    repo.repair()
    repo.rebuild_search_index()
    print(repo.counts())


if __name__ == "__main__":
    main()

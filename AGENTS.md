# all-git repository instructions

all-git is a local Python stdio MCP server distributed through client-specific
plugin wrappers in `plugins/all-git`.

Before completing repository changes, run:

```text
uv sync --extra dev --locked
uv run ruff check .
uv run pytest
uv build
```

The bundled catalog at `src/allgit/catalog.sqlite3` is committed on purpose:
it makes a fresh install instantly useful. Never edit it by hand or inject
rows with ad-hoc SQL. Refresh it with `uv run python
scripts/export_bundled_catalog.py` (syncs the channel, enriches, and writes a
compact copy only when coverage changed), add repos from other sources with
`scripts/import_repo_urls.py URLS_FILE --source x` followed by the export
script with `--force`, and seed captions from a Channel Brains archive with
`scripts/import_channel_brains.py`. Commit the refreshed file. Every repo
carries a `source` (`youtube` or `x`); only `youtube` repos have video
mentions.

Releases: bump the version everywhere `tests/test_version.py` checks, merge
to `main`, then tag that commit `vX.Y.Z` so the plugin install pins resolve.

Preserve unrelated user MCP servers and plugin registrations. Do not claim the
plugin is ready until the client reports the four all-git tools.

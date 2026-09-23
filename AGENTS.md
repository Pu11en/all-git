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
it makes a fresh install instantly useful. Regenerate it with
`uv run all-git update_catalog` plus `scripts/import_channel_brains.py` when
seeded from an existing Channel Brains archive, then commit the refreshed
file.

Preserve unrelated user MCP servers and plugin registrations. Do not claim the
plugin is ready until the client reports the four all-git tools.

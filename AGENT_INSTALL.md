# AGENT_INSTALL — all-git

Read this completely before installing. all-git is a local stdio MCP server:
a searchable SQLite catalog of every repository featured by the GitHub Awesome
YouTube channel, shipped inside the package so a fresh install works with no
first-run ingestion. Four tools: `search_repos`, `get_repo`,
`get_catalog_status`, `update_catalog`.

When a user supplies the all-git repository URL with any plain-language
request such as "get this," "install this," or "add this," treat it as an
explicit request to install all-git into the current AI client. Identify the
client yourself; never ask the user to choose an installation method.

All routes require [uv](https://docs.astral.sh/uv/). The plugin launches the
pinned release through `uvx`, which also provides `yt-dlp` for updates.

## Offline health check (run once before installing)

```bash
uvx --from git+https://github.com/Pu11en/all-git@v0.1.1 all-git-mcp --check
```

Expect `{"status": "ok", ..., "tool_count": 4}`. The check copies the bundled
catalog to the user data directory on first use; it makes no network requests.

## ZCode

From a clone of this repository:

```bash
uv run --no-project python scripts/install_zcode_plugin.py
```

The installer copies all-git to ZCode's stable user plugin directory and adds
that directory to `~/.zcode/cli/config.json`, preserving unrelated plugins and
MCP servers. No restart is required. If the current task cannot refresh its
MCP tool inventory, use the same-session bridge (below) until native tools
appear.

## Claude Code

```bash
claude plugin marketplace add Pu11en/all-git
claude plugin install all-git@all-git --scope user
```

Existing installations: `claude plugin marketplace update all-git` then
`claude plugin update all-git@all-git --scope user`. Activate with
`/reload-plugins`; if that is unavailable, continue via the same-session
bridge.

## Codex

```bash
codex plugin marketplace add Pu11en/all-git
codex plugin add all-git
```

## Hermes Agent

```bash
hermes mcp add all-git --command uvx --connect-timeout 60 --args --from git+https://github.com/Pu11en/all-git@v0.1.1 all-git-mcp
```

## Same-session bridge (any client with frozen tools)

```text
uvx --from git+https://github.com/Pu11en/all-git@v0.1.1 all-git <operation> [arguments]
```

Operations mirror the four tools and emit identical structured JSON.

## Verification

Do not claim the plugin is ready until the client reports the four all-git
tools (`search_repos`, `get_repo`, `get_catalog_status`, `update_catalog`), or
the bridge returns `get_catalog_status` JSON with a positive repo count. Then
demonstrate with `search_repos --query "analytics"` and report the counts.

# Task Plan: all-git MCP

## Goal

Build **all-git** (`/home/drewp/main-projects/all-git`): an open-source, local
MCP server + plugin that makes the GitHub Awesome YouTube channel's curated
repo catalog searchable from any AI session, with automatic updates as new
videos publish. Fresh install must be instantly useful (bundled catalog), and
sessions can say "all git" to find vetted repos for whatever they're building.

## Why it works (verified)

- The channel puts an exact GitHub URL + timestamp for every repo in each
  video's **description** (verified 2026-09-23). Descriptions are the ground
  truth; captions are the prose.
- We already hold 210 videos of captions in
  `/home/drewp/channel-brains/brains/github-awesome/` — a seeding head start.
- channel-brains is MIT; its machinery (yt-dlp discovery, ingestion lock,
  FTS5, MCP server, CLI bridge, plugin installers) is reusable with credit.

## Next Step

None — v0.1.1 shipped. The weekly refresh-catalog Action maintains the
catalog autonomously (first full enrichment run triggered 2026-09-23).

## Current Phase
Complete (v0.1.0 published at github.com/Pu11en/all-git, tag v0.1.0,
installed into ZCode, 4 tools verified, catalog: 212 videos, 4,153 repos,
4,552 mentions, 0 errors)

## Phases

### Phase 1: Verification — COMPLETE (2026-09-23)
- [x] Name collision check: tiny repos share "allgit" (max 4 stars, unrelated
      purposes); name is usable. Repo: `all-git`. PyPI not required (uvx from git).
- [x] Video descriptions contain full repo lists with URLs + timestamps.
- [x] channel-brains license: MIT — derivation allowed with attribution.
- [x] Text-version fallback exists: link.githubawesome.com/<episode>.
- **Status:** complete

### Phase 2: Scaffold — COMPLETE (2026-09-23)
- [ ] git init, pyproject (uv), LICENSE (MIT), README, AGENTS.md
- [ ] Port structure from channel-brains (config/db/youtube/server/cli/jobs),
      adapted names: package `allgit`, command `all-git`
- **Status:** complete

### Phase 3: Ingestion core — COMPLETE (2026-09-23)
- [ ] Channel video discovery (reuse listing logic, all videos, no 50 cap)
- [ ] Description fetch + parser: lines `MM:SS - Name URL` -> repos + mentions
- [ ] Schema: `repos` (owner/name, url, first_seen, mention_count),
      `videos` (id, title, published, description_fetched_at),
      `mentions` (repo_id, video_id, timestamp_seconds),
      `chunks` (caption prose, linked to video + time range),
      `repo_meta` (enrichment cache)
- [ ] Import existing 210-video captions from the channel-brains archive DB
- [ ] Map mentions -> caption segments via timestamps (search hits return the
      "why it's good" prose + youtu.be?t= link)
- **Status:** complete

### Phase 4: Enrichment — COMPLETE (2026-09-23)
- [ ] GitHub API per unique repo: description, stars, language, archived flag,
      pushed_at; cached in repo_meta; optional GITHUB_TOKEN (60/hr unauth vs
      5000/hr with token); degrade gracefully without it
- **Status:** complete

### Phase 5: MCP server + CLI bridge — COMPLETE (2026-09-23)
- [ ] Tools: `search_repos` (FTS over names, GH descriptions, caption prose),
      `get_repo` (details, mentions, timestamped evidence, transcript excerpt),
      `get_catalog_status`, `update_catalog`
- [ ] CLI one-shot bridge for frozen-tool sessions (port pattern)
- **Status:** complete

### Phase 6: Freshness — COMPLETE (2026-09-23)
- [ ] `update_catalog`: fetch new videos' descriptions + captions, resolve new
      repos, mark dead links (404), bounded retries / rate-limit pause
- [ ] GitHub Action: weekly cron rebuilds the bundled catalog DB, commits it
- **Status:** complete

### Phase 7: Packaging & distribution — COMPLETE (2026-09-23)
- [ ] Bundled catalog DB committed in-repo (~2-6 MB) — instant first run
- [ ] uvx `--from git+...` entry; ZCode plugin installer script; Claude Code /
      Codex marketplace wrappers; AGENT_INSTALL.md playbook (port from
      channel-brains)
- [ ] Tests: offline fixtures with recorded descriptions/captions; ruff; pytest
- **Status:** complete

### Phase 8: Full index + publish — COMPLETE (2026-09-23)
- [ ] Index all ~211 current videos; estimate ~3,000-4,500 unique repos
- [ ] Tag release v0.1.0; install on this machine via plugin flow; verify the
      four tools report from a fresh session
- **Status:** complete

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Separate repo, code derived from channel-brains (MIT, credited) | Drew's ask; different product shape |
| Video descriptions as primary data source | Exact URLs + timestamps; captions mangle names |
| Bundled DB committed to repo | Install = instantly useful, no 10-minute first ingest |
| `update_catalog` tool + weekly GH Action | Fresh between releases, self-serve anytime |
| Schema supports multiple channels; ship GithubAwesome only | Keep v1 tight |
| Repo `all-git`, module `allgit` | Name collisions are tiny; no rename needed |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| Caption fetch returned 0 chunks on known-captioned video | Captions live in yt-dlp automatic_captions, not subtitles; fallback added (v0.1.1) |
| FTS bm25 weights covered 4 of 5 columns | Reweighted (0,3,3,2,1) (v0.1.1) |
| Vague queries returned 1 result | AND-first with OR fallback search (v0.1.1) |
| Headless claude -p blocked MCP tools | mcp__all-git__* allowlisted in ~/.claude/settings.json |

### Phase 9: First-use fixes — COMPLETE (2026-09-23)
- [x] Caption source bug (automatic_captions fallback) — found via live test
- [x] bm25 column-weight alignment
- [x] AND-first search with OR fallback (+ regression tests)
- [x] Merged co-agent's attribution work (3 commits: prose relink,
      per-mention narration, short-chunk protection) — kept intact
- [x] v0.1.1 tagged/pushed; Claude, Codex, ZCode registrations repinned
- [x] Weekly enrichment workflow triggered (45 repos already enriched
      locally, 3 dead flagged, before the full Action run)
- **Status:** complete

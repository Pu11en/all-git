# Findings & Decisions

## Requirements
- Searchable, session-available catalog of repos covered by the GitHub
  Awesome YouTube channel (https://www.youtube.com/@GithubAwesome)
- Delivered as MCP server + plugin wrappers, "all git" as the magic phrase
- Must update as new videos publish; fresh install must work immediately
- Free, open-source, local; MIT; Windows/WSL/browser friendly

## Research Findings

### Video descriptions are structured ground truth (verified 2026-09-23)
Sample: video fOU0lDCeNwo (Trending Weekly #13) description contains, per
repo: `MM:SS - Display Name https://github.com/owner/repo` — 26 repos with
exact URLs AND timestamps. Also links a text version per episode
(`https://link.githubawesome.com/weekly13`) and has chapter markers.
Implication: no caption-name disambiguation needed; descriptions solve it.
Example mangle fixed: captions "UIUX Pro Max" -> real repo
`nextlevelbuilder/ui-ux-pro-max-skill`.

### Scale estimate
211 channel videos x ~17-26 repos each => roughly 3,600-5,500 mentions,
likely ~3,000-4,500 unique repos. SQLite + FTS5 trivially handles this.

### Name availability (checked 2026-09-23 via GitHub search API)
- `inventhouse/allgit` (4 stars, git multiplexer), `ToasterPanic/allgit`
  (2 stars, raw file server) — unrelated, tiny; name usable.
- No PyPI requirement: distribute via `uvx --from git+https://github.com/...`

### Reusable assets on this machine
- channel-brains (MIT): yt-dlp listing/caption machinery, ingestion lock,
  resume, FTS5 repo pattern, MCP server + CLI bridge, plugin installers
  (scripts/install_zcode_plugin.py), AGENT_INSTALL.md playbook, uv ruff
  pytest build workflow
- Existing 210-video caption DB:
  /home/drewp/channel-brains/brains/github-awesome/channel_brains.sqlite3
  (brain 6b9c30148fa6) — seeds all-git's caption prose on day one
- Live shared DB: ~/.local/share/channel-brains-mcp/channel_brains.sqlite3

### Text-version fallback
Each episode has a text page (link.githubawesome.com/<episode>) — parser
fallback if description format ever changes.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Descriptions primary, captions secondary | URLs+timestamps exact in descriptions |
| Bundled snapshot DB committed in repo | Zero-setup first run; weekly Action refreshes |
| Mention->caption join via timestamps | Search results carry "why it's good" prose + youtu.be?t= links |
| Optional GITHUB_TOKEN enrichment | 60/hr unauth is too slow for ~4k repos; 5k/hr token finishes in one run; tool degrades gracefully without it |

## Issues Encountered
| Issue | Resolution |
|-------|------------|

## Risks / Holes addressed
| Risk | Mitigation |
|------|------------|
| YouTube rate limits on update | Port channel-brains bounded-retry + pause/resume |
| yt-dlp breakage (YouTube changes) | Pin yt-dlp version; bump in weekly Action |
| Repo link rot (renamed/deleted) | update pass validates, marks dead |
| Channel format change | Parser tolerant + text-version page fallback |
| GH API limits | Optional token + cache + degraded mode |
| Legal | Public descriptions/captions, local personal tool, MIT code, same posture as channel-brains |

## Resources
- channel-brains repo: /home/drewp/channel-brains (AGENTS.md quality gates)
- Channel: https://www.youtube.com/@GithubAwesome
- Sample description fetch: `.venv/bin/yt-dlp --skip-download --print description <url>`

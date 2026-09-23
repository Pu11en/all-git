# Progress Log

## Session: 2026-09-23

### Current Status
- **Phase:** 1 complete (verification) -> Phase 2 next (scaffold)
- **Started:** 2026-09-23

### Actions Taken
- Created /home/drewp/main-projects/all-git with planning session (PLAN_ID
  2026-09-23-all-git-mcp)
- Verified video descriptions carry exact repo URLs + timestamps (fOU0lDCeNwo)
- Checked GitHub name collisions ("allgit" free enough; max 4-star sharers)
- Confirmed channel-brains is MIT (derivation OK with credit)
- Wrote task_plan.md (8 phases) and findings.md

### Test Results
- n/a (planning session; no code yet)

### Next
- Phase 2: scaffold repo (git init, pyproject via uv, LICENSE, README),
  port structure from channel-brains with adapted names

### Session: 2026-09-23 (build run)
- Phase 2-8 execution started. Status: in_progress

### Session: 2026-09-23 (build run) — COMPLETE

- Phase 2: scaffolded repo (git, pyproject/hatchling, MIT, README, AGENTS.md)
- Phase 3: schema (videos/repos/mentions/chunks/repo_meta/FTS5), description
  parser, sync engine with lock; imported 210 videos of captions from the
  channel-brains archive (brain 6b9c30148fa6)
- Phase 4: enrichment module (GITHUB_TOKEN-aware, 45/hr unauth budget)
- Phase 5: MCP server (4 tools) + `all-git` CLI bridge; --check preflight
- Phase 6: update_catalog + weekly GitHub Action (refresh-catalog.yml) with
  enrichment wired in; scripts/export_bundled_catalog.py
- Phase 7: bundled 5.2 MB catalog at src/allgit/catalog.sqlite3; plugin
  wrappers (.zcode/.claude/.codex + SKILL.md); AGENT_INSTALL.md; marketplace
  manifests; ZCode installer script (adapted, preserves other plugins)
- Phase 8: live sync 212/212 descriptions (0 errors) => 4,153 repos, 4,552
  mentions; ruff clean; 19 tests pass; uv build ok; published
  github.com/Pu11en/all-git; tag v0.1.0; pinned-tag uvx verified; ZCode
  plugin installed (portable-planner preserved)

### Test Results
- ruff: all checks passed
- pytest: 19 passed
- uv build: sdist + wheel (wheel includes bundled catalog)
- Live verification: `all-git-mcp --check` => tool_count 4;
  search_repos 'logo SVG' => op7418/logo-generator-skill,
  shaom/svg-hand-drawn-skill; get_repo coffinxp/crtmon => Weekly #17 @ 3:23

### Errors fixed during build
- hatchling build failed: README.md missing -> wrote it first
- malformed SQL params in upsert_repo + invalid FTS 'rebuild' on standalone
  table -> rewritten
- mcp wraps tool ValueError in ToolError -> test expectation adjusted
- data dir not created on direct Repository(path) -> connect() mkdirs parent
- ruff RUF001 en dash -> escaped as \u2013 in regex

### Session: 2026-09-23 (fix pass) — v0.1.1

- Drew reported first real catalog use from his Discord agent; spot-checked
  findings were genuine catalog entries
- Fixes shipped in v0.1.1: caption automatic_captions fallback (verified 34
  chunks live), bm25 five-column weights, AND-first/OR-fallback search
- Co-agent (drewai) had committed 3 attribution improvements locally; merged
  cleanly on top, adjusted one test to the new attribution model
- Integrity checks: no missing caption attempts (2 videos legitimately have
  no speech); 32 low-chunk videos are short uploads, not corruption;
  enrichment already live (45 enriched, 3 dead flagged)
- v0.1.1 pushed + tagged; ~/.claude.json, codex config.toml, ZCode plugin
  copy all repinned; refresh-catalog workflow triggered for full enrichment

### Test Results (v0.1.1)
- ruff: all checks passed; pytest: 22 passed; uv build: ok (wheel bundles catalog)

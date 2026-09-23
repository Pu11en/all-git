"""One-shot command bridge for clients whose current MCP tool list is frozen."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import anyio

from allgit.config import VERSION, catalog_path
from allgit.db import Repository
from allgit.server import build_server


async def _execute(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    repo = Repository(catalog_path())
    server = build_server(repo)
    result = await server.call_tool(tool, arguments)
    structured = result.structured_content
    if not isinstance(structured, dict):
        raise RuntimeError(f"{tool} failed")
    return structured


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="all-git",
        description="Search the GitHub Awesome repo catalog when MCP tools are frozen.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    commands = parser.add_subparsers(dest="tool", required=True)

    search = commands.add_parser("search_repos", help="search the catalog")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=8)

    repo_cmd = commands.add_parser("get_repo", help="read one repo's entry")
    repo_cmd.add_argument("--owner", required=True)
    repo_cmd.add_argument("--name", required=True)

    commands.add_parser("get_catalog_status", help="local coverage numbers")

    update = commands.add_parser("update_catalog", help="sync with the channel")
    update.add_argument("--no-captions", action="store_true")
    update.add_argument("--no-enrich", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    namespace = build_parser().parse_args(argv)
    arguments: dict[str, Any] = {}
    if namespace.tool == "search_repos":
        arguments = {"query": namespace.query, "limit": namespace.limit}
    elif namespace.tool == "get_repo":
        arguments = {"owner": namespace.owner, "name": namespace.name}
    elif namespace.tool == "update_catalog":
        arguments = {
            "fetch_captions": not namespace.no_captions,
            "enrich_meta": not namespace.no_enrich,
        }
    try:
        output = anyio.run(_execute, namespace.tool, arguments)
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

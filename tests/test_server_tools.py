from pathlib import Path

import pytest
from test_db import seed

from allgit.db import Repository
from allgit.server import TOOL_NAMES, build_server


@pytest.fixture
def server(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ALLGIT_HOME", str(tmp_path))
    repo = Repository(tmp_path / "catalog.sqlite3")
    seed(repo)
    return build_server(repo), repo


async def test_lists_exactly_four_tools(server):
    srv, _ = server
    tools = await srv.list_tools()
    assert tuple(t.name for t in tools) == TOOL_NAMES


async def test_search_repos_returns_hits(server):
    srv, _ = server
    result = await srv.call_tool("search_repos", {"query": "mail", "limit": 5})
    payload = result.structured_content
    assert payload["query"] == "mail"
    assert any("gitmal" in hit["name"] for hit in payload["results"])


async def test_get_repo_details(server):
    srv, _ = server
    result = await srv.call_tool("get_repo", {"owner": "antonmedv", "name": "gitmal"})
    payload = result.structured_content
    assert payload["url"] == "https://github.com/antonmedv/gitmal"
    assert payload["mentions"][0]["url"].startswith("https://youtu.be/")


async def test_get_repo_missing_raises(server):
    srv, _ = server
    with pytest.raises(Exception, match="not in the catalog"):
        await srv.call_tool("get_repo", {"owner": "nope", "name": "nope"})


async def test_get_catalog_status(server):
    srv, _ = server
    result = await srv.call_tool("get_catalog_status", {})
    payload = result.structured_content
    assert payload["repos"] == 2
    assert payload["mentions"] == 2

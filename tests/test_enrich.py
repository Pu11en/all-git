import io
import urllib.error
from pathlib import Path

import pytest

from allgit import enrich as enrichment
from allgit.db import Repository


def make_repo(tmp_path: Path, names: list[str]) -> Repository:
    repo = Repository(tmp_path / "catalog.sqlite3")
    repo.upsert_video({"video_id": "fOU0lDCeNwo", "title": "Weekly"})
    for name in names:
        repo.upsert_repo("o", name, f"https://github.com/o/{name}", name, "fOU0lDCeNwo")
    return repo


def fake_urlopen(codes: dict[str, int], headers: dict[str, str] | None = None):
    def opener(request, timeout=0):
        name = request.full_url.rsplit("/", 1)[-1]
        code = codes.get(name, 200)
        if code != 200:
            raise urllib.error.HTTPError(request.full_url, code, "no", headers or {}, io.BytesIO())
        return io.BytesIO(b'{"description": "d", "stargazers_count": 5, "language": "Go"}')

    return opener


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(enrichment.time, "sleep", lambda _s: None)


def test_blocked_repo_is_marked_dead_not_fatal(tmp_path, monkeypatch):
    repo = make_repo(tmp_path, ["ok", "dmca", "flaky"])
    monkeypatch.setattr(
        enrichment.urllib.request, "urlopen", fake_urlopen({"dmca": 451, "flaky": 502})
    )
    report = enrichment.enrich(repo)
    assert report["enriched"] == 1
    assert report["marked_dead"] == 1
    assert report["skipped"] == 1
    assert report["remaining"] == 1


def test_rate_limit_stops_quietly(tmp_path, monkeypatch):
    repo = make_repo(tmp_path, ["a", "b"])
    monkeypatch.setattr(
        enrichment.urllib.request,
        "urlopen",
        fake_urlopen({"a": 403, "b": 403}, {"X-RateLimit-Remaining": "0"}),
    )
    report = enrichment.enrich(repo)
    assert report["rate_limited"] == 1
    assert report["enriched"] == 0
    assert report["remaining"] == 2


def test_access_blocked_403_is_dead_not_rate_limit(tmp_path, monkeypatch):
    repo = make_repo(tmp_path, ["blocked", "fine"])
    monkeypatch.setattr(enrichment.urllib.request, "urlopen", fake_urlopen({"blocked": 403}))
    report = enrichment.enrich(repo)
    assert report == {
        "enriched": 1, "marked_dead": 1, "skipped": 0, "rate_limited": 0, "remaining": 0
    }

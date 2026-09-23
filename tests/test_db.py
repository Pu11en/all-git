from pathlib import Path

from allgit.catalog import parse_description
from allgit.db import Repository


def make_repo(tmp_path: Path) -> Repository:
    return Repository(tmp_path / "catalog.sqlite3")


def seed(repo: Repository) -> None:
    repo.upsert_video(
        {
            "video_id": "fOU0lDCeNwo",
            "title": "Weekly #13",
            "upload_date": "2026-08-01",
            "webpage_url": "https://youtu.be/fOU0lDCeNwo",
        }
    )
    description = "00:11 - Gitmal https://github.com/antonmedv/gitmal\n01:25 - Thing https://github.com/other/thing\n"
    repo.set_video_description("fOU0lDCeNwo", description)
    for mention in parse_description(description):
        repo_id = repo.upsert_repo(
            mention["owner"], mention["name"], mention["url"], mention["display_name"], "fOU0lDCeNwo"
        )
        repo.add_mention(repo_id, "fOU0lDCeNwo", mention["timestamp_seconds"], mention["display_name"])
    repo.replace_chunks(
        "fOU0lDCeNwo",
        [
            {"chunk_index": 0, "start_ms": 0, "end_ms": 45000, "text": "gitmal keeps mail"},
            {"chunk_index": 1, "start_ms": 45000, "end_ms": 90000, "text": "thing does exports"},
        ],
    )
    repo.link_mention_excerpts("fOU0lDCeNwo")
    repo.rebuild_search_index()


def test_counts_and_lookup(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    seed(repo)
    counts = repo.counts()
    assert counts["repos"] == 2
    assert counts["mentions"] == 2
    detail = repo.get_repo("antonmedv", "gitmal")
    assert detail is not None
    assert detail["url"] == "https://github.com/antonmedv/gitmal"
    assert detail["mentions"][0]["excerpt"].startswith("gitmal")


def test_case_insensitive_lookup(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    seed(repo)
    assert repo.get_repo("AntonMedv", "GitMal") is not None


def test_search_finds_by_prose(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    seed(repo)
    hits = repo.search("mail")
    assert any(h["name"] == "gitmal" for h in hits)
    empty = repo.search("nonexistentterm")
    assert empty == []


def test_mention_excerpt_within_window(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    seed(repo)
    detail = repo.get_repo("other", "thing")
    assert detail["mentions"][0]["excerpt"] == "thing does exports"


def test_repo_meta_roundtrip(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    seed(repo)
    detail = repo.get_repo("antonmedv", "gitmal")
    repo.set_repo_meta(detail["repo_id"], {"stars": 12, "language": "Go", "dead": False})
    after = repo.get_repo("antonmedv", "gitmal")
    assert after["stars"] == 12
    assert after["language"] == "Go"


def test_straddling_chunk_credits_the_right_repo(tmp_path: Path) -> None:
    """A caption chunk covering two repos must not give one the other's pitch."""
    repo = make_repo(tmp_path)
    repo.upsert_video(
        {
            "video_id": "straddle01",
            "title": "Weekly #14",
            "upload_date": "2026-08-08",
            "webpage_url": "https://youtu.be/straddle01",
        }
    )
    description = (
        "03:51 - Printer https://github.com/acme/printer\n"
        "04:16 - Ledger https://github.com/acme/ledger\n"
    )
    repo.set_video_description("straddle01", description)
    for mention in parse_description(description):
        repo_id = repo.upsert_repo(
            mention["owner"], mention["name"], mention["url"], mention["display_name"], "straddle01"
        )
        repo.add_mention(repo_id, "straddle01", mention["timestamp_seconds"], mention["display_name"])
    printer_pitch = "Printer turns a mailbox into a private print queue. " * 8
    ledger_pitch = "Ledger brings invoicing and receipts into one workspace. " * 8
    repo.replace_chunks(
        "straddle01",
        [
            {
                "chunk_index": 0,
                "start_ms": 231_000,
                "end_ms": 280_000,
                "text": printer_pitch + ledger_pitch,
            }
        ],
    )
    repo.link_mention_excerpts("straddle01")

    ledger = repo.get_repo("acme", "ledger")["mentions"][0]["excerpt"]
    assert ledger.startswith("Ledger")
    assert "print queue" not in ledger

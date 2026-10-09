
from allgit.config import catalog_path


def test_catalog_seeded_from_bundled(tmp_path, monkeypatch):
    data = tmp_path / "home"
    bundled = tmp_path / "bundled"
    bundled.mkdir()
    from allgit.db import Repository

    Repository(bundled / "catalog.sqlite3")
    monkeypatch.setenv("ALLGIT_HOME", str(data))
    monkeypatch.setenv("ALLGIT_BUNDLED_CATALOG", str(bundled / "catalog.sqlite3"))
    path = catalog_path()
    assert path.exists()
    assert path.parent == data


def test_older_local_catalog_replaced_by_newer_bundle(tmp_path, monkeypatch):
    from allgit.db import Repository

    bundled = tmp_path / "bundled.sqlite3"
    newer = Repository(bundled)
    for vid in ("a", "b"):
        newer.upsert_video({"video_id": vid, "title": vid, "webpage_url": vid})
    data = tmp_path / "home"
    data.mkdir()
    older = Repository(data / "catalog.sqlite3")
    older.upsert_video({"video_id": "a", "title": "a", "webpage_url": "a"})
    monkeypatch.setenv("ALLGIT_HOME", str(data))
    monkeypatch.setenv("ALLGIT_BUNDLED_CATALOG", str(bundled))
    path = catalog_path()
    assert Repository(path).counts()["videos"] == 2


def test_fuller_local_catalog_kept(tmp_path, monkeypatch):
    from allgit.db import Repository

    bundled = tmp_path / "bundled.sqlite3"
    Repository(bundled).upsert_video({"video_id": "a", "title": "a", "webpage_url": "a"})
    data = tmp_path / "home"
    data.mkdir()
    local = Repository(data / "catalog.sqlite3")
    for vid in ("a", "b"):
        local.upsert_video({"video_id": vid, "title": vid, "webpage_url": vid})
    monkeypatch.setenv("ALLGIT_HOME", str(data))
    monkeypatch.setenv("ALLGIT_BUNDLED_CATALOG", str(bundled))
    assert Repository(catalog_path()).counts()["videos"] == 2

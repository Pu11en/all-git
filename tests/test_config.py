
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

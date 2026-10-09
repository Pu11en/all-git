import pytest


@pytest.fixture(autouse=True)
def _no_bundled_catalog(monkeypatch, tmp_path):
    """Keep the shipped catalog from replacing small test catalogs."""
    monkeypatch.setenv("ALLGIT_BUNDLED_CATALOG", str(tmp_path / "no-bundled-catalog.sqlite3"))

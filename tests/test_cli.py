import json

from test_db import seed

from allgit.cli import main


def test_cli_search(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ALLGIT_HOME", str(tmp_path))
    from allgit.db import Repository

    seed(Repository(tmp_path / "catalog.sqlite3"))
    code = main(["search_repos", "--query", "mail"])
    out = capsys.readouterr().out
    assert code == 0
    payload = json.loads(out)
    assert any("gitmal" in hit["name"] for hit in payload["results"])


def test_cli_repo(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ALLGIT_HOME", str(tmp_path))
    from allgit.db import Repository

    seed(Repository(tmp_path / "catalog.sqlite3"))
    code = main(["get_repo", "--owner", "antonmedv", "--name", "gitmal"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["owner"] == "antonmedv"


def test_cli_status(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ALLGIT_HOME", str(tmp_path))
    from allgit.db import Repository

    seed(Repository(tmp_path / "catalog.sqlite3"))
    code = main(["get_catalog_status"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["repos"] == 2

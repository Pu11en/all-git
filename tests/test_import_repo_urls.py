import importlib.util
import sys
from pathlib import Path

from allgit.db import SOURCE_X, Repository

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "import_repo_urls.py"


def load_script():
    spec = importlib.util.spec_from_file_location("import_repo_urls", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_import_urls_adds_once(tmp_path: Path) -> None:
    script = load_script()
    repo = Repository(tmp_path / "catalog.sqlite3")
    text = "https://github.com/acme/one\nhttps://github.com/acme/two\nhttps://github.com/ACME/one\n"
    assert script.import_urls(repo, text, SOURCE_X) == 2
    assert script.import_urls(repo, text, SOURCE_X) == 0
    detail = repo.get_repo("acme", "one")
    assert detail["source"] == SOURCE_X
    assert detail["mentions"] == []

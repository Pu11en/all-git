"""Every place the release version or install pin is written must agree."""

import json
import re
from pathlib import Path

from allgit.config import VERSION

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_matches_package_version():
    # Regex rather than tomllib, which only exists from Python 3.11 on.
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'^version = "([^"]+)"', text, re.M).group(1) == VERSION


def test_manifests_carry_the_package_version():
    for manifest in (
        ROOT / "plugins/all-git/.claude-plugin/plugin.json",
        ROOT / "plugins/all-git/.codex-plugin/plugin.json",
        ROOT / "plugins/all-git/.zcode-plugin/plugin.json",
    ):
        assert json.loads(manifest.read_text(encoding="utf-8"))["version"] == VERSION, manifest
    for marketplace in (ROOT / "marketplace.json", ROOT / ".claude-plugin/marketplace.json"):
        plugins = json.loads(marketplace.read_text(encoding="utf-8"))["plugins"]
        assert [p["version"] for p in plugins] == [VERSION], marketplace


def test_install_pins_name_the_package_version():
    pin = re.compile(r"git\+https://github\.com/Pu11en/all-git@v(\d+\.\d+\.\d+)")
    pinned_files = (
        ROOT / "plugins/all-git/.claude-plugin/plugin.json",
        ROOT / "plugins/all-git/.codex-plugin/plugin.json",
        ROOT / "plugins/all-git/.zcode-plugin/plugin.json",
        ROOT / "plugins/all-git/.mcp.json",
        ROOT / "plugins/all-git/skills/all-git/SKILL.md",
        ROOT / "AGENT_INSTALL.md",
    )
    for file in pinned_files:
        pins = pin.findall(file.read_text(encoding="utf-8"))
        assert pins, f"{file} has no pinned install line"
        assert set(pins) == {VERSION}, f"{file} pins {sorted(set(pins))}, package is {VERSION}"

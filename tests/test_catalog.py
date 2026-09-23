from allgit.catalog import parse_description

SAMPLE = """Paid channel subscription: https://www.youtube.com/channel/UC9Rrud/join

This is GitHub Trending Weekly #13, and today we're diving into 26 trending open-source projects.

Text version link: https://link.githubawesome.com/weekly13

00:00 - Introduction
00:11 - Gitmal https://github.com/antonmedv/gitmal
01:25 - UI UX Pro Max https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
10:53 - lazypg https://github.com/rebelice/lazypg 
1:02:03 - Some Hour Tool https://github.com/owner/hour-tool
Not a repo line https://example.com/foo
03:00 - Broken entry (no url)
04:00 - Docs link only https://github.com/owner/repo/blob/main/readme.md

Thank you for watching.
"""


def test_parses_github_mentions_with_timestamps():
    mentions = parse_description(SAMPLE)
    urls = [m["url"] for m in mentions]
    assert "https://github.com/antonmedv/gitmal" in urls
    assert "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill" in urls


def test_ignores_non_repo_lines():
    mentions = parse_description(SAMPLE)
    assert all(m["url"].startswith("https://github.com/") for m in mentions)
    names = [m["display_name"] for m in mentions]
    assert "Introduction" not in names


def test_timestamp_formats():
    mentions = {m["display_name"]: m for m in parse_description(SAMPLE)}
    assert mentions["Gitmal"]["timestamp_seconds"] == 11
    assert mentions["UI UX Pro Max"]["timestamp_seconds"] == 85
    assert mentions["lazypg"]["timestamp_seconds"] == 653
    assert mentions["Some Hour Tool"]["timestamp_seconds"] == 3723


def test_owner_and_name_extraction():
    mentions = parse_description(SAMPLE)
    by_name = {m["name"]: m for m in mentions}
    assert by_name["gitmal"]["owner"] == "antonmedv"
    assert by_name["hour-tool"]["owner"] == "owner"


def test_dedupes_repeated_mentions():
    doubled = SAMPLE + "01:25 - UI UX Pro Max https://github.com/nextlevelbuilder/ui-ux-pro-max-skill\n"
    mentions = parse_description(doubled)
    hits = [m for m in mentions if m["name"] == "ui-ux-pro-max-skill"]
    assert len(hits) == 1

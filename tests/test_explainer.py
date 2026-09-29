import json

import pytest

from repocompass.analysis.context import build_context
from repocompass.analysis.pipeline import Analysis
from repocompass.analysis.tree import build_tree
from repocompass.explainer import PathChecker, extract_json, normalize_guide


@pytest.mark.parametrize(
    "reply",
    [
        '{"a": 1}',
        'Sure! Here is the JSON:\n```json\n{"a": 1}\n```\nHope this helps.',
        '<think>let me plan {not json}</think>{"a": 1}',
        '{"a": 1,}',  # trailing comma from a sloppy model
        'noise {"a": 1} noise',
    ],
)
def test_extract_json_tolerates_model_quirks(reply):
    assert extract_json(reply) == {"a": 1}


@pytest.mark.parametrize("reply", ["no json here", "[1, 2]", "{broken: yes"])
def test_extract_json_rejects_garbage(reply):
    with pytest.raises(ValueError):
        extract_json(reply)


def test_path_checker():
    check = PathChecker(["src/app/main.py", "README.md"])
    assert check.exists("src/app/main.py")
    assert check.exists("./src/app/")
    assert check.exists("`src`")
    assert check.exists("src/app/*")
    assert check.exists("README.md")
    assert not check.exists("src/app/invented.py")
    assert not check.exists("lib/")


def test_normalize_guide_fills_gaps_and_flags_invented_paths():
    raw = {
        "overview": {"summary": " A web framework. ", "difficulty": "Intermediate"},
        "architecture": {"components": ["Router", {"name": "Core", "path": "src/core/"}], "data_flow": "one step"},
        "directories": [{"path": "src/", "purpose": "code"}, {"path": "made-up/", "purpose": "?"}, {"purpose": "no path"}],
        "key_files": "not a list",
        "learning_path": [{"title": "Start", "paths": "src/core/engine.py", "why": "core"}, "Read tests", 42],
        "how_it_works": [{"step": 1, "description": "Request comes in"}, "", None],
        "glossary": [{"term": "WSGI", "meaning": "a Python web server interface"}, {"meaning": "orphan"}],
    }
    guide = normalize_guide(raw, ["src/core/engine.py", "README.md"])

    assert guide["overview"]["summary"] == "A web framework."
    assert guide["overview"]["difficulty"] == "intermediate"
    assert guide["overview"]["problem"] == ""
    assert guide["architecture"]["components"] == [
        {"name": "Router", "path": "", "responsibility": "", "exists": False},
        {"name": "Core", "path": "src/core/", "responsibility": "", "exists": True},
    ]
    assert guide["architecture"]["data_flow"] == ["one step"]
    assert guide["directories"] == [
        {"path": "src/", "purpose": "code", "exists": True},
        {"path": "made-up/", "purpose": "?", "exists": False},
    ]
    assert guide["key_files"] == []
    assert guide["learning_path"] == [
        {"title": "Start", "why": "core", "paths": [{"path": "src/core/engine.py", "exists": True}]},
        {"title": "Read tests", "why": "", "paths": []},
    ]
    assert guide["how_it_works"] == ["Request comes in"]
    assert guide["glossary"] == [{"term": "WSGI", "meaning": "a Python web server interface"}]
    assert guide["contribution"] == {"setup_steps": [], "starter_areas": [], "tips": []}


def _analysis(readme_size: int) -> Analysis:
    paths = ["README.md", "package.json", "src/index.js"]
    report = {
        "repo": {"full_name": "a/b", "ref": "main", "description": "", "topics": []},
        "stats": {"files": 3, "dirs": 1},
        "languages": [],
        "stack": [],
        "entry_points": [{"path": "src/index.js", "reason": "JS entry"}],
        "run_commands": [],
        "community": {"readme": "README.md", "contributing": None},
        "tree": build_tree([{"path": p, "type": "blob", "size": 1} for p in paths]),
    }
    files = {"README.md": "R" * readme_size, "package.json": json.dumps({"name": "b"}), "src/index.js": "console.log(1)"}
    return Analysis("a", "b", "sha", paths, files, report)


def test_context_includes_facts_tree_and_files_in_priority_order():
    context = build_context(_analysis(100), char_budget=50_000)
    order = [context.index(marker) for marker in (
        "FACTS FROM STATIC ANALYSIS", "FOLDER STRUCTURE", "FILE: README.md", "FILE: package.json", "FILE: src/index.js",
    )]
    assert order == sorted(order)


def test_context_respects_budget_and_truncates():
    context = build_context(_analysis(50_000), char_budget=6_000)
    assert len(context) <= 6_000
    assert "[truncated]" in context

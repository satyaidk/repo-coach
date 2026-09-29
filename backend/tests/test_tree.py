from repocompass.analysis.tree import build_tree, compute_stats, render_tree_outline

ENTRIES = [
    {"path": "src", "type": "tree", "size": 0},
    {"path": "src/app.py", "type": "blob", "size": 100},
    {"path": "src/utils", "type": "tree", "size": 0},
    {"path": "src/utils/io.py", "type": "blob", "size": 50},
    {"path": "README.md", "type": "blob", "size": 10},
    {"path": "docs", "type": "tree", "size": 0},
]


def test_build_tree_nests_and_sorts_dirs_first():
    tree = build_tree(ENTRIES)
    assert [c["name"] for c in tree["children"]] == ["docs", "src", "README.md"]
    src = tree["children"][1]
    assert [c["name"] for c in src["children"]] == ["utils", "app.py"]
    assert src["count"] == 2  # recursive file count
    assert tree["count"] == 3
    assert tree["children"][0] == {"name": "docs", "type": "dir", "children": [], "count": 0}


def test_build_tree_handles_files_without_explicit_parent_entries():
    tree = build_tree([{"path": "a/b/c.txt", "type": "blob", "size": 1}])
    assert tree["children"][0]["children"][0]["children"][0]["name"] == "c.txt"


def test_outline_limits_files_per_dir_and_depth():
    entries = [{"path": f"pkg/f{i}.py", "type": "blob", "size": 1} for i in range(20)]
    entries.append({"path": "pkg/deep/er/est/x.py", "type": "blob", "size": 1})
    outline = render_tree_outline(build_tree(entries), max_depth=2, max_files_per_dir=5)
    assert "pkg/ (21 files)" in outline
    assert "... and 15 more files" in outline
    assert "  deep/ (1 files)" in outline
    assert "est/" not in outline  # deeper than max_depth


def test_outline_caps_total_lines():
    entries = [{"path": f"d{i}/f.py", "type": "blob", "size": 1} for i in range(50)]
    outline = render_tree_outline(build_tree(entries), max_lines=10)
    assert len(outline.splitlines()) == 11
    assert outline.endswith("more lines not shown)")


def test_stats():
    stats = compute_stats(ENTRIES)
    assert stats["files"] == 3 and stats["dirs"] == 3
    assert stats["size_bytes"] == 160
    assert stats["top_extensions"][0] == {"ext": ".py", "count": 2}

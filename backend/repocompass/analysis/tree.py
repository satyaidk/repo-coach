"""Turn GitHub's flat list of paths into a nested tree (for the UI) and a compact outline (for the LLM)."""

from collections import Counter
from pathlib import PurePosixPath


def build_tree(entries: list[dict]) -> dict:
    """Nested `{name, type, children}` dirs and `{name, type, size}` files; dirs carry a recursive file `count`."""
    root: dict = {"name": "", "type": "dir", "children": {}}
    for entry in entries:
        parts = entry["path"].split("/")
        node = root
        for part in parts[:-1]:
            node = node["children"].setdefault(part, {"name": part, "type": "dir", "children": {}})
        name = parts[-1]
        if entry["type"] == "tree":
            node["children"].setdefault(name, {"name": name, "type": "dir", "children": {}})
        else:
            node["children"][name] = {"name": name, "type": "file", "size": entry.get("size", 0)}
    return _finalize(root)


def _finalize(node: dict) -> dict:
    if node["type"] == "file":
        return node
    children = [_finalize(child) for child in node["children"].values()]
    children.sort(key=lambda c: (c["type"] != "dir", c["name"].lower()))
    node["children"] = children
    node["count"] = sum(c["count"] if c["type"] == "dir" else 1 for c in children)
    return node


def render_tree_outline(
    tree: dict, max_depth: int = 3, max_files_per_dir: int = 8, max_lines: int = 250
) -> str:
    """Indented outline like `src/ (42 files)` that fits in an LLM prompt, even for huge repos."""
    lines: list[str] = []

    def walk(node: dict, depth: int) -> None:
        indent = "  " * depth
        dirs = [c for c in node["children"] if c["type"] == "dir"]
        files = [c for c in node["children"] if c["type"] == "file"]
        for d in dirs:
            lines.append(f"{indent}{d['name']}/ ({d['count']} files)")
            if depth + 1 < max_depth:
                walk(d, depth + 1)
        for f in files[:max_files_per_dir]:
            lines.append(f"{indent}{f['name']}")
        if len(files) > max_files_per_dir:
            lines.append(f"{indent}... and {len(files) - max_files_per_dir} more files")

    walk(tree, 0)
    if len(lines) > max_lines:
        hidden = len(lines) - max_lines
        lines = lines[:max_lines] + [f"... ({hidden} more lines not shown)"]
    return "\n".join(lines)


def compute_stats(entries: list[dict]) -> dict:
    files = [e for e in entries if e["type"] == "blob"]
    extensions = Counter(PurePosixPath(f["path"]).suffix.lower() or "(no extension)" for f in files)
    return {
        "files": len(files),
        "dirs": len(entries) - len(files),
        "size_bytes": sum(f.get("size", 0) for f in files),
        "max_depth": max((e["path"].count("/") + 1 for e in entries), default=0),
        "top_extensions": [{"ext": ext, "count": n} for ext, n in extensions.most_common(8)],
    }

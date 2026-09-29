"""Choose the most informative files and pack them into a size-limited prompt for the LLM.

Dumping a whole repo into a model is slow, expensive and doesn't fit. Instead we send
facts from static analysis plus a handful of files, in priority order, until the budget runs out.
"""

from pathlib import PurePosixPath

from ..github import GitHubClient
from .pipeline import Analysis, ROOT_CONFIG_FILES
from .stack import is_manifest
from .tree import render_tree_outline

_ARCHITECTURE_DOCS = {"architecture.md", "design.md", "development.md", "hacking.md", "internals.md", "overview.md"}
_MAX_ENTRY_FILES = 6
_SEPARATOR = "\n\n"
_TRUNCATED = "\n... [truncated]"


def _architecture_docs(paths: list[str]) -> list[str]:
    docs = [p for p in paths if p.count("/") <= 2 and PurePosixPath(p).name.lower() in _ARCHITECTURE_DOCS]
    return sorted(docs, key=lambda p: (p.count("/"), p))[:3]


async def fetch_context_files(gh: GitHubClient, analysis: Analysis) -> None:
    """Download entry points and architecture docs (the static pass only fetched manifests and docs)."""
    wanted = [e["path"] for e in analysis.report["entry_points"][:_MAX_ENTRY_FILES]]
    wanted += _architecture_docs(analysis.paths)
    missing = [p for p in wanted if p not in analysis.files]
    if missing:
        analysis.files.update(await gh.get_files(analysis.owner, analysis.name, analysis.commit_sha, missing))


def _facts(report: dict) -> str:
    repo, stats = report["repo"], report["stats"]
    lines = [
        f"Repository: {repo['full_name']} (branch {repo['ref']})",
        f"Description: {repo['description'] or '(none)'}",
        f"Topics: {', '.join(repo['topics']) or '(none)'}",
        f"Size: {stats['files']} files in {stats['dirs']} folders",
        "Languages: " + ", ".join(f"{lang['name']} {lang['percent']}%" for lang in report["languages"][:8]),
        "Detected stack: " + ", ".join(f"{s['name']} ({s['category']})" for s in report["stack"]),
        "Likely entry points:",
        *(f"  - {e['path']}: {e['reason']}" for e in report["entry_points"]),
        "Commands found in config files:",
        *(f"  - {c['command']}" for c in report["run_commands"]),
    ]
    return "\n".join(lines)


def build_context(analysis: Analysis, char_budget: int) -> str:
    report, files = analysis.report, analysis.files
    community = report["community"]
    entry_paths = [e["path"] for e in report["entry_points"][:_MAX_ENTRY_FILES]]

    # (title, text, max chars) in priority order: earlier sections win when space is tight.
    sections: list[tuple[str, str, int]] = [
        ("FACTS FROM STATIC ANALYSIS (reliable)", _facts(report), 4_000),
        ("FOLDER STRUCTURE (dirs show recursive file counts)", render_tree_outline(report["tree"]), 12_000),
    ]
    config_files = [p for p in files if is_manifest(p) or p in ROOT_CONFIG_FILES]

    def add_files(paths: list[str], cap: int) -> None:
        sections.extend((f"FILE: {p}", files[p], cap) for p in paths if p in files)

    add_files([community["readme"]], 10_000)
    add_files([p for p in config_files if "/" not in p], 3_000)
    add_files(entry_paths, 4_000)
    add_files(_architecture_docs(analysis.paths), 5_000)
    add_files([p for p in config_files if "/" in p], 1_500)  # nested manifests, e.g. monorepo packages
    add_files([community["contributing"]], 3_000)

    parts: list[str] = []
    remaining = char_budget
    for title, text, cap in sections:
        header = f"===== {title} =====\n"
        separator = len(_SEPARATOR) if parts else 0
        room = min(cap, remaining - separator - len(header))
        if room < 300:
            break
        body = text if len(text) <= room else text[: room - len(_TRUNCATED)] + _TRUNCATED
        parts.append(header + body)
        remaining -= separator + len(header) + len(body)
    return _SEPARATOR.join(parts)

"""Static analysis: everything we can learn about a repo without AI."""

import asyncio
from dataclasses import dataclass

from ..github import GitHubClient, GitHubError, RepoRef
from .entrypoints import NOISY_DIRS, find_community_files, find_entry_points, find_run_commands
from .stack import detect_stack, is_manifest, list_dependencies
from .tree import build_tree, compute_stats

MAX_MANIFESTS = 20
ROOT_CONFIG_FILES = ("Makefile", "Dockerfile")


@dataclass
class Analysis:
    owner: str
    name: str
    commit_sha: str
    paths: list[str]
    files: dict[str, str]  # contents of every file we downloaded, by path
    report: dict  # the JSON the UI renders


async def _issues_or_empty(gh: GitHubClient, owner: str, name: str, enabled: bool) -> list[dict]:
    if not enabled:
        return []
    try:
        return await gh.get_good_first_issues(owner, name)
    except GitHubError:
        return []  # issues are a bonus; never fail the whole analysis over them


async def analyze_repo(gh: GitHubClient, ref: RepoRef) -> Analysis:
    repo = await gh.get_repo(ref.owner, ref.repo)
    owner, name = repo["owner"]["login"], repo["name"]  # canonical casing, follows renames
    branch = ref.ref or repo["default_branch"]
    sha = await gh.get_commit_sha(owner, name, branch)

    (entries, truncated), languages, issues = await asyncio.gather(
        gh.get_tree(owner, name, sha),
        gh.get_languages(owner, name),
        _issues_or_empty(gh, owner, name, repo.get("has_issues", True)),
    )
    paths = [e["path"] for e in entries if e["type"] == "blob"]
    path_set = set(paths)
    community = find_community_files(paths)

    manifests = sorted(
        (p for p in paths if is_manifest(p) and p.count("/") <= 2 and not NOISY_DIRS.search(p)),
        key=lambda p: (p.count("/"), p),
    )[:MAX_MANIFESTS]
    docs = [community["readme"], community["contributing"]]
    wanted = manifests + [p for p in ROOT_CONFIG_FILES if p in path_set] + [p for p in docs if p]
    files = await gh.get_files(owner, name, sha, wanted)
    manifest_texts = {p: files[p] for p in manifests if p in files}

    total_bytes = sum(languages.values()) or 1
    report = {
        "repo": {
            "owner": owner,
            "name": name,
            "full_name": repo["full_name"],
            "description": repo.get("description") or "",
            "url": repo["html_url"],
            "homepage": repo.get("homepage") or "",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "open_issues": repo.get("open_issues_count", 0),
            "license": (repo.get("license") or {}).get("spdx_id") or "",
            "topics": repo.get("topics", []),
            "archived": repo.get("archived", False),
            "default_branch": repo["default_branch"],
            "ref": branch,
            "commit_sha": sha,
            "pushed_at": repo.get("pushed_at"),
        },
        "languages": [
            {"name": lang, "percent": round(count * 100 / total_bytes, 1)}
            for lang, count in sorted(languages.items(), key=lambda kv: -kv[1])
        ],
        "stats": compute_stats(entries),
        "tree": build_tree(entries),
        "tree_truncated": truncated,
        "stack": detect_stack(paths, manifest_texts),
        "dependencies": list_dependencies(manifest_texts),
        "entry_points": find_entry_points(paths, files, repo_name=name),
        "run_commands": find_run_commands(paths, files),
        "community": community,
        "good_first_issues": issues,
    }
    return Analysis(owner, name, sha, paths, files, report)

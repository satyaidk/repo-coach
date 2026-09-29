"""Thin async client for the parts of the GitHub API we need."""

import asyncio
import re
from dataclasses import dataclass
from urllib.parse import quote

import httpx

API_URL = "https://api.github.com"
RAW_URL = "https://raw.githubusercontent.com"

# GitHub user/org names can't contain dots; repo names can.
_OWNER = r"[A-Za-z0-9\-]+"
_NAME = r"[A-Za-z0-9_.\-]+"
_URL_PATTERNS = [
    # https://github.com/owner/repo(.git)(/tree/<ref>/...)
    re.compile(
        rf"^(?:https?://)?(?:www\.)?github\.com/(?P<owner>{_OWNER})/(?P<repo>{_NAME})"
        rf"(?:/(?:tree|blob)/(?P<ref>[^/?#]+))?(?:[/?#].*)?$"
    ),
    # git@github.com:owner/repo.git
    re.compile(rf"^git@github\.com:(?P<owner>{_OWNER})/(?P<repo>{_NAME})$"),
    # owner/repo
    re.compile(rf"^(?P<owner>{_OWNER})/(?P<repo>{_NAME})$"),
]


class InvalidRepoURL(ValueError):
    pass


class GitHubError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class RepoRef:
    owner: str
    repo: str
    ref: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


def parse_repo_url(text: str) -> RepoRef:
    """Accepts `https://github.com/o/r`, `.../tree/<branch>`, `git@github.com:o/r.git` or `o/r`."""
    cleaned = text.strip().rstrip("/")
    for pattern in _URL_PATTERNS:
        match = pattern.match(cleaned)
        if match:
            repo = match["repo"]
            if repo.endswith(".git"):
                repo = repo[:-4]
            if repo in {"", ".", ".."}:
                break
            ref = match.groupdict().get("ref")
            return RepoRef(match["owner"], repo, ref)
    raise InvalidRepoURL(
        "That doesn't look like a GitHub repository. "
        "Paste something like https://github.com/owner/repo"
    )


class GitHubClient:
    def __init__(self, http: httpx.AsyncClient, token: str = ""):
        self._http = http
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "RepoCompass",
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    async def _get(self, path: str, *, params: dict | None = None, accept: str | None = None) -> httpx.Response:
        headers = dict(self._headers)
        if accept:
            headers["Accept"] = accept
        try:
            resp = await self._http.get(f"{API_URL}{path}", headers=headers, params=params)
        except httpx.HTTPError as exc:
            raise GitHubError(f"Could not reach GitHub: {exc}") from exc

        if resp.status_code == 404:
            raise GitHubError(
                "Repository or branch not found. Check the URL — private repos need a "
                "GITHUB_TOKEN in .env with access to them.",
                404,
            )
        if resp.status_code in (403, 429) and resp.headers.get("x-ratelimit-remaining") == "0":
            raise GitHubError(
                "GitHub API rate limit reached. Add a GITHUB_TOKEN to your .env file "
                "(5,000 requests/hour instead of 60), or wait a bit.",
                429,
            )
        if resp.status_code >= 400:
            raise GitHubError(f"GitHub API error {resp.status_code}: {resp.text[:200]}", 502)
        return resp

    async def get_repo(self, owner: str, repo: str) -> dict:
        return (await self._get(f"/repos/{owner}/{repo}")).json()

    async def get_commit_sha(self, owner: str, repo: str, ref: str) -> str:
        resp = await self._get(
            f"/repos/{owner}/{repo}/commits/{quote(ref, safe='')}",
            accept="application/vnd.github.sha",
        )
        return resp.text.strip()

    async def get_tree(self, owner: str, repo: str, sha: str) -> tuple[list[dict], bool]:
        """Returns (entries, truncated). Each entry has `path`, `type` ('blob'/'tree') and `size`."""
        data = (await self._get(f"/repos/{owner}/{repo}/git/trees/{sha}", params={"recursive": "1"})).json()
        entries = [
            {"path": e["path"], "type": e["type"], "size": e.get("size", 0)}
            for e in data.get("tree", [])
            if e.get("type") in ("blob", "tree")
        ]
        return entries, bool(data.get("truncated"))

    async def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        return (await self._get(f"/repos/{owner}/{repo}/languages")).json()

    async def get_good_first_issues(self, owner: str, repo: str, limit: int = 8) -> list[dict]:
        for label in ("good first issue", "help wanted"):
            items = (
                await self._get(
                    f"/repos/{owner}/{repo}/issues",
                    params={"labels": label, "state": "open", "per_page": 30},
                )
            ).json()
            issues = [
                {
                    "number": item["number"],
                    "title": item["title"],
                    "url": item["html_url"],
                    "labels": [lbl["name"] for lbl in item.get("labels", [])],
                    "comments": item.get("comments", 0),
                }
                for item in items
                if "pull_request" not in item
            ]
            if issues:
                return issues[:limit]
        return []

    async def get_file(self, owner: str, repo: str, sha: str, path: str, max_chars: int = 20_000) -> str | None:
        """Fetch a file via raw.githubusercontent.com (doesn't count against the API rate limit)."""
        url = f"{RAW_URL}/{owner}/{repo}/{sha}/{quote(path)}"
        headers = {"User-Agent": "RepoCompass"}
        if "Authorization" in self._headers:
            headers["Authorization"] = self._headers["Authorization"]
        try:
            resp = await self._http.get(url, headers=headers)
        except httpx.HTTPError:
            return None
        if resp.status_code != 200 or b"\x00" in resp.content[:1024]:
            return None
        return resp.content.decode("utf-8", errors="replace")[:max_chars]

    async def get_files(
        self, owner: str, repo: str, sha: str, paths: list[str], max_chars: int = 20_000
    ) -> dict[str, str]:
        semaphore = asyncio.Semaphore(8)

        async def fetch(path: str) -> tuple[str, str | None]:
            async with semaphore:
                return path, await self.get_file(owner, repo, sha, path, max_chars)

        results = await asyncio.gather(*(fetch(p) for p in dict.fromkeys(paths)))
        return {path: text for path, text in results if text is not None}

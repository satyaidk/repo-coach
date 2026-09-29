"""End-to-end API tests against a fake GitHub and a fake AI model (no network needed)."""

import dataclasses
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from repocompass import main
from repocompass.config import get_settings
from repocompass.github import GitHubClient
from repocompass.llm import LLMProvider

SHA = "0123456789abcdef0123456789abcdef01234567"
FILES = {
    "README.md": "# Widget\nA tiny web app.",
    "requirements.txt": "flask>=3\npytest\n",
    "app.py": "from flask import Flask\napp = Flask(__name__)\n",
    "tests/test_app.py": "def test_ok(): pass\n",
}


def fake_github(request: httpx.Request) -> httpx.Response:
    host, path = request.url.host, request.url.path
    if host == "raw.githubusercontent.com":
        name = path.removeprefix(f"/acme/widget/{SHA}/")
        return httpx.Response(200, text=FILES[name]) if name in FILES else httpx.Response(404)
    routes = {
        "/repos/acme/widget": {
            "name": "widget", "full_name": "acme/widget", "owner": {"login": "acme"},
            "html_url": "https://github.com/acme/widget", "default_branch": "main",
            "description": "A tiny web app", "stargazers_count": 5, "has_issues": True,
        },
        "/repos/acme/widget/languages": {"Python": 900, "HTML": 100},
        f"/repos/acme/widget/git/trees/{SHA}": {
            "tree": [{"path": "tests", "type": "tree"}] + [{"path": p, "type": "blob", "size": 10} for p in FILES],
            "truncated": False,
        },
        "/repos/acme/widget/issues": [
            {"number": 7, "title": "Fix typo", "html_url": "https://x/7", "labels": [{"name": "good first issue"}]},
            {"number": 8, "title": "A PR", "html_url": "https://x/8", "labels": [], "pull_request": {}},
        ],
    }
    if path == "/repos/acme/widget/commits/main":
        return httpx.Response(200, text=SHA)
    if path in routes:
        return httpx.Response(200, json=routes[path])
    return httpx.Response(404, json={"message": "Not Found"})


class FakeProvider(LLMProvider):
    id = "fake"
    label = "Fake"

    def __init__(self, replies):
        super().__init__("fake-model")
        self.replies = list(replies)
        self.prompts = []

    async def complete(self, system, prompt, *, json_mode=False):
        self.prompts.append(prompt)
        return self.replies.pop(0)


GUIDE_REPLY = "```json\n" + json.dumps({
    "overview": {"summary": "A tiny Flask app.", "difficulty": "beginner"},
    "key_files": [{"path": "app.py", "purpose": "creates the app"}, {"path": "server.py", "purpose": "invented"}],
    "learning_path": [{"title": "Open app.py", "paths": ["app.py"], "why": "it's the whole app"}],
}) + "\n```"


@pytest.fixture
def client(tmp_path, monkeypatch):
    settings = dataclasses.replace(get_settings(), cache_dir=tmp_path)
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    main._analyses.clear()
    with TestClient(main.app) as test_client:
        main.app.state.github = GitHubClient(httpx.AsyncClient(transport=httpx.MockTransport(fake_github)))
        yield test_client


def use_provider(monkeypatch, provider):
    monkeypatch.setattr(main, "create_provider", lambda *args: provider)


def test_analyze_returns_static_report(client):
    response = client.post("/api/analyze", json={"url": "https://github.com/acme/widget"})
    assert response.status_code == 200
    report = response.json()
    assert report["repo"]["commit_sha"] == SHA
    assert report["stats"]["files"] == 4
    assert {s["name"] for s in report["stack"]} >= {"Flask", "pytest"}
    assert report["entry_points"][0]["path"] == "app.py"
    assert report["run_commands"][0]["command"] == "pip install -r requirements.txt"
    assert report["good_first_issues"] == [
        {"number": 7, "title": "Fix typo", "url": "https://x/7", "labels": ["good first issue"], "comments": 0}
    ]
    assert report["languages"][0] == {"name": "Python", "percent": 90.0}
    assert report["community"]["tests"] == "tests/test_app.py"


def test_explain_verifies_paths_and_caches(client, monkeypatch):
    provider = FakeProvider([GUIDE_REPLY])
    use_provider(monkeypatch, provider)

    first = client.post("/api/explain", json={"url": "acme/widget", "provider": "fake"}).json()
    assert first["cached"] is False
    assert first["guide"]["overview"]["difficulty"] == "beginner"
    assert [(f["path"], f["exists"]) for f in first["guide"]["key_files"]] == [("app.py", True), ("server.py", False)]
    assert "from flask import Flask" in provider.prompts[0]  # the entry point's code was sent

    second = client.post("/api/explain", json={"url": "acme/widget", "provider": "fake"}).json()
    assert second["cached"] is True
    assert second["guide"] == first["guide"]
    assert len(provider.prompts) == 1


def test_explain_retries_once_on_bad_json(client, monkeypatch):
    provider = FakeProvider(["I think this repo is great!", GUIDE_REPLY])
    use_provider(monkeypatch, provider)
    response = client.post("/api/explain", json={"url": "acme/widget", "provider": "fake"})
    assert response.status_code == 200
    assert len(provider.prompts) == 2


def test_explain_gives_up_after_two_bad_replies(client, monkeypatch):
    use_provider(monkeypatch, FakeProvider(["nope", "still nope"]))
    response = client.post("/api/explain", json={"url": "acme/widget", "provider": "fake"})
    assert response.status_code == 502
    assert "valid JSON" in response.json()["detail"]


def test_bad_url_is_a_400(client):
    response = client.post("/api/analyze", json={"url": "not a repo"})
    assert response.status_code == 400
    assert "github.com/owner/repo" in response.json()["detail"]


def test_missing_repo_is_a_404(client):
    response = client.post("/api/analyze", json={"url": "acme/nothing-here"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_missing_api_key_explains_how_to_fix(client, monkeypatch):
    settings = dataclasses.replace(get_settings(), openai_api_key="")
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    response = client.post("/api/explain", json={"url": "acme/widget", "provider": "openai"})
    assert response.status_code == 502
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_root_points_to_docs(client):
    assert client.get("/").json()["docs"] == "/docs"


def test_cors_allows_the_nextjs_dev_server(client):
    preflight = client.options(
        "/api/analyze",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_rejects_unknown_origins(client):
    response = client.get("/api/providers", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers

"""FastAPI app: the JSON API behind the Next.js app in `frontend/`.

    POST /api/analyze   {url}                        -> static report (tree, stack, entry points...)
    POST /api/explain   {url, provider, model?, refresh?} -> AI-written beginner's guide
    GET  /api/providers                              -> which AI providers are ready to use
"""

import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .analysis.pipeline import Analysis, analyze_repo
from .config import get_settings
from .explainer import explain_repo
from .github import GitHubClient, GitHubError, InvalidRepoURL, parse_repo_url
from .llm import LLMError, create_provider, list_providers

ANALYSIS_TTL_SECONDS = 15 * 60
MAX_CACHED_ANALYSES = 20


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as http:
        app.state.github = GitHubClient(http, get_settings().github_token)
        yield


app = FastAPI(title="RepoCompass API", lifespan=lifespan)
# The browser calls this API directly from the Next.js app (a different port = a different origin).
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().frontend_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# The UI calls /analyze then /explain for the same repo; keep recent analyses so we don't refetch.
_analyses: dict[str, tuple[float, Analysis]] = {}


async def _get_analysis(request: Request, url: str) -> Analysis:
    ref = parse_repo_url(url)
    key = f"{ref.full_name.lower()}@{ref.ref or ''}"
    now = time.monotonic()
    cached = _analyses.get(key)
    if cached and now - cached[0] < ANALYSIS_TTL_SECONDS:
        return cached[1]

    analysis = await analyze_repo(request.app.state.github, ref)
    _analyses[key] = (now, analysis)
    for stale in sorted(_analyses, key=lambda k: _analyses[k][0])[:-MAX_CACHED_ANALYSES]:
        del _analyses[stale]
    return analysis


class AnalyzeRequest(BaseModel):
    url: str


class ExplainRequest(BaseModel):
    url: str
    provider: str
    model: str | None = None
    refresh: bool = False


@app.get("/", include_in_schema=False)
async def index() -> dict:
    origins = get_settings().frontend_origins
    return {"name": "RepoCompass API", "docs": "/docs", "frontend": origins[0] if origins else None}


@app.get("/api/providers")
async def providers() -> dict:
    settings = get_settings()
    return {"default": settings.default_provider, "providers": await list_providers(settings)}


@app.post("/api/analyze")
async def analyze(body: AnalyzeRequest, request: Request) -> dict:
    return (await _get_analysis(request, body.url)).report


@app.post("/api/explain")
async def explain(body: ExplainRequest, request: Request) -> dict:
    settings = get_settings()
    provider = create_provider(body.provider, body.model, settings)
    analysis = await _get_analysis(request, body.url)
    return await explain_repo(request.app.state.github, analysis, provider, settings.cache_dir, body.refresh)


@app.exception_handler(InvalidRepoURL)
async def _bad_url(_: Request, exc: InvalidRepoURL) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=400)


@app.exception_handler(GitHubError)
async def _github_error(_: Request, exc: GitHubError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=exc.status_code)


@app.exception_handler(LLMError)
async def _llm_error(_: Request, exc: LLMError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=502)

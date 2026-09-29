# How to run RepoCompass

This guide covers installing, configuring and developing RepoCompass on your own machine.
For what RepoCompass is and how it works, see the [main README](../README.md).

## Contents

- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Choosing an AI provider](#choosing-an-ai-provider)
- [Troubleshooting](#troubleshooting)
- [Project structure](#project-structure)
- [API reference](#api-reference)
- [Development](#development)

## Requirements

| Tool | Version | Used for |
|---|---|---|
| Python | 3.11 or newer | the backend (`backend/`) |
| Node.js | 20 or newer | the frontend (`frontend/`) |
| Ollama | optional | running AI models locally, for free |

## Quick start

RepoCompass has two parts that run side by side, so you'll use **two terminals**:

- the **backend** (Python + FastAPI) on port **8000**: talks to GitHub, analyzes repos, runs the AI models
- the **frontend** (Next.js + TypeScript + Tailwind CSS) on port **3000**: the web page you use

### 1. Backend (first terminal)

```bash
cd backend
python -m venv .venv

# activate the virtual environment
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
cp .env.example .env            # then fill in what you use (see Configuration)
python -m repocompass           # API on http://127.0.0.1:8000
```

### 2. Frontend (second terminal)

```bash
cd frontend
npm install
npm run dev                     # open http://localhost:3000
```

Open **http://localhost:3000**, paste a GitHub link (or click one of the examples) and press **Analyze repo**.
If both servers are running, you'll see this:

<img src="images/home.png" alt="RepoCompass home page" width="100%">

The folder map, tech stack, entry points, commands and contributor checklist work with **no AI at all**:
choose "No AI (map only)" in the "AI guide by" menu. Add an AI provider (below) to get the written guide.

## Configuration

All backend settings live in `backend/.env`, and `backend/.env.example` documents every one of them.
Restart the backend after changing it.

| Setting | Default | What it does |
|---|---|---|
| `GITHUB_TOKEN` | *(empty)* | Raises GitHub's limit from 60 to 5,000 requests/hour and allows private repos you can access. [Create a token](https://github.com/settings/tokens); no scopes are needed for public repos. |
| `DEFAULT_LLM_PROVIDER` | `ollama` | The provider selected the first time the page loads (the page then remembers your choice). |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | `gpt-5-mini` | OpenAI access. |
| `OPENAI_BASE_URL` | *(empty)* | Point the OpenAI provider at any OpenAI-compatible API (OpenRouter, Groq, LM Studio...). |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | `claude-opus-5-5` | Anthropic (Claude) access. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | `gemini-2.5-flash` | Google Gemini access. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama is running. |
| `OLLAMA_MODEL` | `qwen3:4b-instruct` | Default local model. |
| `OLLAMA_NUM_CTX` | `8192` | Local model context window in tokens. Bigger lets the model read more of the repo but needs more GPU memory. |
| `FRONTEND_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Web addresses allowed to call the API. Add yours if the frontend runs elsewhere. |

The frontend has one optional setting. If the backend isn't at `http://127.0.0.1:8000`, copy
`frontend/.env.example` to `frontend/.env.local` and set `NEXT_PUBLIC_API_URL`.

**Caching:** written guides are saved in `backend/.cache/`, one per repository commit and model. Opening the
same repo again with the same model is instant and costs no tokens. **Rewrite guide** in the UI skips the cache.

## Choosing an AI provider

Pick a provider for each analysis from the **AI guide by** menu, and type any model name in the box next to
it. After a guide is written you can switch model and press **Rewrite guide** to compare the results.

| Provider | Needs | Good to know |
|---|---|---|
| **Ollama** (local) | [Ollama](https://ollama.com) installed and a model pulled, e.g. `ollama pull qwen3:4b-instruct` | Free, private and offline. Speed depends on your GPU. |
| **OpenAI** | `OPENAI_API_KEY` | Also works with OpenAI-compatible services via `OPENAI_BASE_URL`. |
| **Anthropic** | `ANTHROPIC_API_KEY` | Claude models. |
| **Google Gemini** | `GEMINI_API_KEY` | |

**Running models locally on a laptop.** While a guide is being written, run `ollama ps`. If the
`PROCESSOR` column shows a CPU/GPU split instead of `100% GPU`, the model doesn't fit in your GPU's memory and
will be slow. Lower `OLLAMA_NUM_CTX` or use a smaller model. Small models (a few billion parameters) write
shorter, rougher guides than large cloud models, and on a 4 GB laptop GPU a guide can take around 10 minutes.
Ollama's `-cloud` models (e.g. `gpt-oss:120b-cloud`) run on Ollama's servers and are selected the same way
as local ones.

## Troubleshooting

| Message | What to do |
|---|---|
| *Can't reach the RepoCompass API at http://127.0.0.1:8000* | The backend isn't running. Start it with `python -m repocompass` in `backend/` (with its `.venv` active). |
| *GitHub API rate limit reached* | Add a `GITHUB_TOKEN` to `backend/.env` and restart the backend, or wait up to an hour. |
| *Repository or branch not found* | Check the link. Private repos also need a `GITHUB_TOKEN` with access to them. |
| *… needs an API key: set …_API_KEY* | Add that key to `backend/.env` and restart the backend, or pick another provider. |
| *Can't reach Ollama … Start it with `ollama serve`* | Start Ollama (or open the Ollama app). |
| *Ollama model '…' not found* | Download it: `ollama pull <model>`. |
| *Ollama stopped responding for 5 minutes* | The model is too big for your machine. Lower `OLLAMA_NUM_CTX` or choose a smaller model. |
| *… didn't return valid JSON twice in a row* | Small models sometimes produce broken output. Press **Try again**, or switch to a larger model. |
| The provider menu shows "(not set up)" | That provider has no API key in `backend/.env`, or for Ollama, the Ollama server isn't running. |
| A path in the guide is crossed out and marked **not in repo** | Working as intended: the AI mentioned a file that doesn't exist, and RepoCompass flagged it. |

## Project structure

```
.
├── backend/                     Python + FastAPI
│   ├── repocompass/             the Python package
│   │   ├── __main__.py          `python -m repocompass` starts the API
│   │   ├── main.py              FastAPI app: the JSON API (+ CORS for the frontend)
│   │   ├── config.py            settings from backend/.env
│   │   ├── github.py            GitHub API client + URL parsing
│   │   ├── explainer.py         prompt, JSON parsing, path checking, caching
│   │   ├── analysis/
│   │   │   ├── pipeline.py      runs the static analysis for one repo
│   │   │   ├── tree.py          nested tree for the UI, compact outline for the AI
│   │   │   ├── stack.py         tech detection from manifests and config files
│   │   │   ├── entrypoints.py   entry points, run commands, contributor checklist
│   │   │   └── context.py       chooses which files the AI sees, within a size budget
│   │   └── llm/
│   │       ├── base.py          the LLMProvider interface every provider implements
│   │       ├── registry.py      creates a provider by name; lists which are ready
│   │       └── *_provider.py    OpenAI, Anthropic, Gemini, Ollama
│   ├── tests/                   pytest suite (offline: GitHub and the AI are faked)
│   ├── requirements.txt         Python dependencies
│   ├── pyproject.toml           pytest settings
│   └── .env.example             every setting, documented
├── frontend/                    Next.js + TypeScript + Tailwind CSS
│   ├── src/app/                 layout (fonts, theme script), the page, global styles and color tokens
│   ├── src/components/
│   │   ├── explorer.tsx         the main screen: search, loading states, results layout
│   │   ├── file-tree.tsx        the folder map and the file detail panel
│   │   ├── repo-map-context.tsx shared tree state, so any path in the guide can open the map
│   │   ├── sections/            the guide's cards (overview, route, architecture, stack, contributing...)
│   │   └── ui/                  small building blocks (buttons, cards, path chips, copy button)
│   ├── src/lib/                 API client, response types, theme logic, formatting helpers
│   └── .env.example             where the backend lives
└── docs/                        this guide, the PRD and the original project idea
```

**Adding another AI provider** means writing one class with a `complete(system, prompt)` method (see
`backend/repocompass/llm/base.py`) and registering it in `backend/repocompass/llm/registry.py`.
Nothing else changes.

## API reference

The backend is a small JSON API. Interactive documentation is at **http://127.0.0.1:8000/docs** while it's running.

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/analyze` | `{"url": "owner/repo"}` | file tree, stats, languages, stack, dependencies, entry points, commands, contributor checklist, good first issues |
| `POST` | `/api/explain` | `{"url", "provider", "model"?, "refresh"?}` | the AI-written guide, with every path marked as verified or not |
| `GET` | `/api/providers` | | which AI providers are configured, their default and suggested models |

`url` accepts `owner/repo`, `https://github.com/owner/repo`, links to a branch (`.../tree/<branch>`) or a
file, and `git@github.com:owner/repo.git`.

## Development

```bash
# backend/ (with .venv active)
pytest                          # run the tests
python -m repocompass --reload  # restart the API automatically when code changes

# frontend/
npm run dev                     # dev server with hot reload
npm run lint                    # ESLint
npx tsc --noEmit                # TypeScript type check
npm run build                   # production build
```

The backend tests run fully offline: GitHub and the AI models are replaced by fakes, so they're fast and free.

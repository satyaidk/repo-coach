# RepoCompass

Paste a GitHub repository link and get a beginner-friendly map of it:

- **Folder map**: the whole file tree, clickable, with the important files marked
- **Where it starts**: the entry-point files and the commands to install, run and test it
- **Tech stack**: frameworks, libraries, databases, test and build tools, read from config files
- **How it's built**: an architecture summary, diagram, main parts and how data moves between them
- **Your route through the code**: an ordered reading list, with each stop numbered on the folder map
- **Contributing**: how newcomer-ready the repo is, setup steps, good first areas, and open "good first issue" tickets
- **Words to know**: a glossary of the jargon this repo uses

It's for anyone who has opened a big open-source project and thought *"where do I even start?"*

## How it works

```
GitHub URL
   │
   ▼
GitHub API ──► file tree, README, config files, languages, open issues
   │
   ▼
Static analysis (plain Python, no AI) ──► tech stack, entry points, run commands, contributor checklist
   │
   ▼
Context builder ──► picks the most useful files and trims them to fit the model
   │
   ▼
LLM (OpenAI / Claude / Gemini / local Ollama) ──► JSON guide
   │
   ▼
Path checker ──► flags any file the AI mentions that doesn't really exist
```

The main design decision: **facts come from code, explanations come from AI.** Anything that can be read
directly from files (dependencies, entry points, commands) is never guessed by a model. The AI only gets a
small, curated slice of the repo and is asked to explain it. Every path it mentions is checked against the
real tree, so invented files are marked `not in repo` instead of misleading you.

## Setup

RepoCompass has two parts that run side by side:

- **Backend** (`repocompass/`): a Python FastAPI app on port 8000 that talks to GitHub and the AI models
- **Frontend** (`web/`): a Next.js + TypeScript + Tailwind CSS app on port 3000, the page you open

You need Python 3.11+ and Node.js 20+.

**1. Backend** (first terminal):

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env        # then fill in what you use (see below)
python -m repocompass       # API on http://127.0.0.1:8000
```

**2. Frontend** (second terminal):

```bash
cd web
npm install
npm run dev                 # open http://localhost:3000
```

The folder map, stack, entry points and contributor checklist work with **no AI at all**.
Choose "No AI (map only)" in the "AI guide by" menu.

The page has light, dark and "match my system" themes (top-right corner), with Claude orange as the accent.
If the API runs somewhere other than `http://127.0.0.1:8000`, copy `web/.env.example` to `web/.env.local`
and set `NEXT_PUBLIC_API_URL`. If the page runs somewhere other than port 3000, add its address to
`FRONTEND_ORIGINS` in the root `.env`.

## Choosing an AI provider

Pick one per analysis from the "AI guide by" menu, and type any model name in the box next to it.
After a guide is written you can switch model and press "Rewrite guide" to compare them.
Set up whichever providers you want in `.env`:

| Provider | What to set in `.env` | Notes |
|---|---|---|
| Ollama (local) | `OLLAMA_MODEL`, `OLLAMA_NUM_CTX` | Free, private, offline. Install from [ollama.com](https://ollama.com), then `ollama pull qwen3:4b-instruct`. |
| OpenAI | `OPENAI_API_KEY`, `OPENAI_MODEL` | `OPENAI_BASE_URL` also lets you use any OpenAI-compatible API (OpenRouter, Groq, LM Studio...). |
| Anthropic | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | |
| Google Gemini | `GEMINI_API_KEY`, `GEMINI_MODEL` | |

`DEFAULT_LLM_PROVIDER` picks which one is selected the first time the page loads (after that, the page
remembers your last choice). Restart the API after editing `.env`.

**Ollama on a laptop:** local models need enough GPU memory to run fast. Run `ollama ps` while a guide is
being written: if it shows a CPU/GPU split rather than `100% GPU`, lower `OLLAMA_NUM_CTX` or use a smaller model.
Small models (a few billion parameters) write shorter, rougher guides than big cloud models. Ollama's
`-cloud` models (e.g. `gpt-oss:120b-cloud`) run on Ollama's servers but are used exactly like local ones.

**GitHub token (optional):** without one, GitHub allows 60 API requests an hour (roughly 10 analyses).
Add `GITHUB_TOKEN` to `.env` to get 5,000 and to analyze private repos you can access.

Guides are cached in `.cache/` per commit and model, so mapping the same repo again with the same model is
instant and costs no tokens. "Rewrite guide" skips the cache and writes a fresh one.

## Project structure

```
repocompass/             Python backend
├── main.py              FastAPI app: the JSON API (+ CORS for the frontend)
├── github.py            GitHub API client + URL parsing
├── config.py            settings from .env
├── explainer.py         prompt, JSON parsing, path checking, caching
├── analysis/
│   ├── pipeline.py      runs the static analysis for one repo
│   ├── tree.py          nested tree for the UI, compact outline for the AI
│   ├── stack.py         tech detection from manifests and config files
│   ├── entrypoints.py   entry points, run commands, contributor checklist
│   └── context.py       chooses which files the AI sees, within a size budget
├── llm/
│   ├── base.py          the LLMProvider interface every provider implements
│   ├── registry.py      creates a provider by name; lists which are ready
│   └── *_provider.py    OpenAI, Anthropic, Gemini, Ollama
tests/                   pytest suite (offline: GitHub and the AI are faked)

web/                     Next.js frontend
├── src/app/             layout (fonts, theme script), the page, global styles and color tokens
├── src/components/
│   ├── explorer.tsx     the main screen: search, loading states, results layout
│   ├── file-tree.tsx    the folder map and the file detail panel
│   ├── repo-map-context.tsx   shared tree state, so any path in the guide can open the map
│   ├── sections/        the guide's cards (overview, route, architecture, stack, contributing...)
│   └── ui/              small building blocks (buttons, cards, path chips, copy button)
└── src/lib/             API client, response types, theme logic, formatting helpers
```

**Adding another AI provider** means writing one class with a `complete(system, prompt)` method
(see `llm/base.py`) and registering it in `llm/registry.py`. Nothing else changes.

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/analyze` | `{"url": "owner/repo"}` | tree, stack, entry points, commands, checklist, issues |
| `POST` | `/api/explain` | `{"url", "provider", "model"?, "refresh"?}` | the AI guide |
| `GET` | `/api/providers` | | which providers are configured, and their models |

Interactive docs at `http://127.0.0.1:8000/docs`.

## Development

```bash
pytest                         # backend tests
python -m repocompass --reload # restart the API automatically when code changes

cd web
npm run lint                   # ESLint
npx tsc --noEmit               # TypeScript type check
npm run build                  # production build
```

## Ideas for what's next

- Stream the guide section by section, so the first parts appear while the rest is being written
- "Explain this file" on demand for any file in the folder map
- Match good first issues to the skills you already have
- Export the guide as Markdown for your notes
- Compare two similar repos side by side

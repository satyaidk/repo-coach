"""Ask the LLM for a beginner's guide to the repo, then check its answer against the real file tree."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .analysis.context import build_context, fetch_context_files
from .analysis.pipeline import Analysis
from .github import GitHubClient
from .llm import LLMError, LLMProvider

SYSTEM_PROMPT = """You are a senior software engineer mentoring a beginner who wants to understand \
an open-source repository well enough to learn from it and contribute to it.

Rules:
- Explain in plain, friendly English with short sentences. Define jargon the first time you use it.
- Be concrete: name real files and folders from the provided structure. Never invent paths.
- Base everything on the provided context. If something is unclear, say so instead of guessing.
- The "facts from static analysis" section is reliable; trust it over assumptions.
- Reply with ONE JSON object only: no markdown fences, no text before or after it."""

SCHEMA = """{
  "overview": {
    "summary": "2-3 sentences: what this project is and what it does",
    "problem": "what problem it solves and who uses it",
    "difficulty": "beginner | intermediate | advanced",
    "difficulty_reason": "one sentence on why"
  },
  "architecture": {
    "summary": "3-5 sentences on the high-level design and how the big pieces fit together",
    "components": [{"name": "short name", "path": "folder or file", "responsibility": "what it does"}],
    "data_flow": ["how a request or input moves through the components, one step per item"],
    "mermaid": "flowchart TD\\n  A[\\"CLI\\"] --> B[\\"Core engine\\"]"
  },
  "how_it_works": ["ordered steps of the main workflow, naming the files involved"],
  "directories": [{"path": "folder/", "purpose": "one sentence"}],
  "key_files": [{"path": "path/to/file", "purpose": "one sentence"}],
  "learning_path": [{"title": "step title", "paths": ["files or folders to read"], "why": "what you learn"}],
  "contribution": {
    "setup_steps": ["commands or steps to get it running locally"],
    "starter_areas": [{"path": "folder or file", "why": "why it's a good first place to contribute"}],
    "tips": ["practical advice for a first contribution"]
  },
  "glossary": [{"term": "a concept or tool this repo uses", "meaning": "beginner-friendly definition"}]
}"""


def build_prompt(context: str) -> str:
    return f"""Here is information about a GitHub repository.

{context}

Write a beginner's guide to this repository as a JSON object with exactly this shape:
{SCHEMA}

Guidance:
- directories: the important top-level folders (up to 12), plus key subfolders if the code lives inside one (like src/).
- key_files: up to 12 files a newcomer should know about.
- learning_path: 4-7 steps, starting from the easiest way into the codebase.
- components: 3-8 items. mermaid: 3-10 nodes, every label in double quotes, flowchart syntax only.
- glossary: 4-10 terms from this repo that a beginner might not know.
- Only use paths that appear in the folder structure or files above."""


# ---------------------------------------------------------------------------
# Parsing: models (especially small local ones) don't always return clean JSON.
# ---------------------------------------------------------------------------


def extract_json(text: str) -> dict:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced[1]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in the model's reply")
    candidate = text[start : end + 1]
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        data = json.loads(re.sub(r",\s*([}\]])", r"\1", candidate))  # trailing commas
    if not isinstance(data, dict):
        raise ValueError("The model's reply was JSON but not an object")
    return data


def _text(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):  # e.g. {"step": 1, "description": "..."}
        return " — ".join(_text(v) for v in value.values() if not isinstance(v, (int, float)))
    return "" if value is None else str(value)


def _texts(value) -> list[str]:
    items = value if isinstance(value, list) else [value] if value else []
    return [t for t in (_text(v) for v in items) if t]


def _records(value, keys: tuple[str, ...]) -> list[dict]:
    records = []
    for item in value if isinstance(value, list) else []:
        if isinstance(item, dict):
            records.append({k: _text(item.get(k)) for k in keys})
        elif isinstance(item, str) and item.strip():
            records.append({keys[0]: item.strip(), **{k: "" for k in keys[1:]}})
    return records


class PathChecker:
    """Answers "does this path really exist in the repo?" for anything the model mentions."""

    def __init__(self, paths: list[str]):
        self.files = set(paths)
        self.dirs = {"/".join(p.split("/")[:i]) for p in paths for i in range(1, p.count("/") + 1)}

    def exists(self, path: str) -> bool:
        clean = path.strip().strip("`").removeprefix("./").rstrip("*").strip("/")
        return clean == "" or clean in self.files or clean in self.dirs

    def mark(self, records: list[dict], require_path: bool = True) -> list[dict]:
        return [
            {**r, "exists": bool(r["path"]) and self.exists(r["path"])}
            for r in records
            if r["path"] or not require_path
        ]


def normalize_guide(raw: dict, paths: list[str]) -> dict:
    """Coerce whatever the model returned into the exact shape the UI expects, flagging unknown paths."""
    check = PathChecker(paths)
    overview = raw.get("overview") if isinstance(raw.get("overview"), dict) else {}
    arch = raw.get("architecture") if isinstance(raw.get("architecture"), dict) else {}
    contrib = raw.get("contribution") if isinstance(raw.get("contribution"), dict) else {}
    difficulty = _text(overview.get("difficulty")).lower()

    learning_path = []
    for step in raw.get("learning_path") if isinstance(raw.get("learning_path"), list) else []:
        if isinstance(step, dict):
            learning_path.append({
                "title": _text(step.get("title")),
                "why": _text(step.get("why")),
                "paths": [{"path": p, "exists": check.exists(p)} for p in _texts(step.get("paths"))],
            })  # fmt: skip
        elif isinstance(step, str) and step.strip():
            learning_path.append({"title": step.strip(), "why": "", "paths": []})

    return {
        "overview": {
            "summary": _text(overview.get("summary")),
            "problem": _text(overview.get("problem")),
            "difficulty": difficulty if difficulty in ("beginner", "intermediate", "advanced") else "",
            "difficulty_reason": _text(overview.get("difficulty_reason")),
        },
        "architecture": {
            "summary": _text(arch.get("summary")),
            "components": check.mark(
                _records(arch.get("components"), ("name", "path", "responsibility")), require_path=False
            ),
            "data_flow": _texts(arch.get("data_flow")),
            "mermaid": _text(arch.get("mermaid")),
        },
        "how_it_works": _texts(raw.get("how_it_works")),
        "directories": check.mark(_records(raw.get("directories"), ("path", "purpose"))),
        "key_files": check.mark(_records(raw.get("key_files"), ("path", "purpose"))),
        "learning_path": learning_path,
        "contribution": {
            "setup_steps": _texts(contrib.get("setup_steps")),
            "starter_areas": check.mark(_records(contrib.get("starter_areas"), ("path", "why"))),
            "tips": _texts(contrib.get("tips")),
        },
        "glossary": [g for g in _records(raw.get("glossary"), ("term", "meaning")) if g["term"]],
    }


def _cache_file(cache_dir: Path, analysis: Analysis, provider: LLMProvider) -> Path:
    model = re.sub(r"[^A-Za-z0-9._-]", "_", provider.model)
    name = f"{analysis.owner}__{analysis.name}__{analysis.commit_sha[:12]}__{provider.id}__{model}.json"
    return cache_dir / "explanations" / name


async def explain_repo(
    gh: GitHubClient, analysis: Analysis, provider: LLMProvider, cache_dir: Path, refresh: bool = False
) -> dict:
    """Returns `{provider, model, generated_at, cached, guide}`. Results are cached per commit + model."""
    cache_file = _cache_file(cache_dir, analysis, provider)
    if cache_file.exists() and not refresh:
        return {**json.loads(cache_file.read_text(encoding="utf-8")), "cached": True}

    await fetch_context_files(gh, analysis)
    prompt = build_prompt(build_context(analysis, provider.context_chars))

    guide = None
    for _attempt in range(2):  # small models occasionally produce broken JSON; one retry usually fixes it
        reply = await provider.complete(SYSTEM_PROMPT, prompt, json_mode=True)
        try:
            guide = normalize_guide(extract_json(reply), analysis.paths)
            break
        except ValueError:
            continue
    if guide is None:
        raise LLMError(
            f"{provider.model} didn't return valid JSON twice in a row. "
            "Try again, or switch to a larger model."
        )

    result = {
        "provider": provider.id,
        "model": provider.model,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "guide": guide,
    }
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return {**result, "cached": False}

"""Detect a repo's tech stack from its manifests (package.json, requirements.txt, go.mod...) and config files.

This is plain pattern matching, not AI: facts we can read directly from files should never be guessed.
"""

import json
import re
import tomllib
from fnmatch import fnmatchcase, translate
from pathlib import PurePosixPath

LANGUAGE = "Language"
FRAMEWORK = "Framework"
LIBRARY = "Library"
DATABASE = "Database & ORM"
TESTING = "Testing"
TOOLING = "Build & Tooling"
DEVOPS = "DevOps & Infra"

# ---------------------------------------------------------------------------
# Dependency tables. A key matches a dependency with the same name, or any
# dependency "under" it (`@aws-sdk` matches `@aws-sdk/client-s3`, a Go module
# matches its `/v2` major versions).
# ---------------------------------------------------------------------------

NPM = {
    "react": ("React", FRAMEWORK),
    "next": ("Next.js", FRAMEWORK),
    "vue": ("Vue", FRAMEWORK),
    "nuxt": ("Nuxt", FRAMEWORK),
    "svelte": ("Svelte", FRAMEWORK),
    "@sveltejs/kit": ("SvelteKit", FRAMEWORK),
    "@angular/core": ("Angular", FRAMEWORK),
    "solid-js": ("SolidJS", FRAMEWORK),
    "astro": ("Astro", FRAMEWORK),
    "@remix-run": ("Remix", FRAMEWORK),
    "gatsby": ("Gatsby", FRAMEWORK),
    "express": ("Express", FRAMEWORK),
    "fastify": ("Fastify", FRAMEWORK),
    "koa": ("Koa", FRAMEWORK),
    "hono": ("Hono", FRAMEWORK),
    "@nestjs/core": ("NestJS", FRAMEWORK),
    "electron": ("Electron", FRAMEWORK),
    "react-native": ("React Native", FRAMEWORK),
    "expo": ("Expo", FRAMEWORK),
    "typescript": ("TypeScript", LANGUAGE),
    "vite": ("Vite", TOOLING),
    "webpack": ("webpack", TOOLING),
    "rollup": ("Rollup", TOOLING),
    "esbuild": ("esbuild", TOOLING),
    "parcel": ("Parcel", TOOLING),
    "turbo": ("Turborepo", TOOLING),
    "@babel/core": ("Babel", TOOLING),
    "eslint": ("ESLint", TOOLING),
    "prettier": ("Prettier", TOOLING),
    "jest": ("Jest", TESTING),
    "vitest": ("Vitest", TESTING),
    "mocha": ("Mocha", TESTING),
    "cypress": ("Cypress", TESTING),
    "@playwright/test": ("Playwright", TESTING),
    "@testing-library": ("Testing Library", TESTING),
    "tailwindcss": ("Tailwind CSS", LIBRARY),
    "styled-components": ("styled-components", LIBRARY),
    "sass": ("Sass", LIBRARY),
    "@mui/material": ("Material UI", LIBRARY),
    "@radix-ui": ("Radix UI", LIBRARY),
    "redux": ("Redux", LIBRARY),
    "@reduxjs/toolkit": ("Redux Toolkit", LIBRARY),
    "zustand": ("Zustand", LIBRARY),
    "@tanstack/react-query": ("TanStack Query", LIBRARY),
    "axios": ("Axios", LIBRARY),
    "graphql": ("GraphQL", LIBRARY),
    "@apollo/client": ("Apollo Client", LIBRARY),
    "socket.io": ("Socket.IO", LIBRARY),
    "three": ("Three.js", LIBRARY),
    "d3": ("D3", LIBRARY),
    "zod": ("Zod", LIBRARY),
    "@aws-sdk": ("AWS SDK", LIBRARY),
    "prisma": ("Prisma", DATABASE),
    "@prisma/client": ("Prisma", DATABASE),
    "mongoose": ("Mongoose (MongoDB)", DATABASE),
    "mongodb": ("MongoDB", DATABASE),
    "sequelize": ("Sequelize", DATABASE),
    "typeorm": ("TypeORM", DATABASE),
    "drizzle-orm": ("Drizzle ORM", DATABASE),
    "pg": ("PostgreSQL", DATABASE),
    "mysql2": ("MySQL", DATABASE),
    "redis": ("Redis", DATABASE),
    "ioredis": ("Redis", DATABASE),
    "@supabase/supabase-js": ("Supabase", DATABASE),
    "firebase": ("Firebase", DATABASE),
}

PYPI = {
    "django": ("Django", FRAMEWORK),
    "flask": ("Flask", FRAMEWORK),
    "fastapi": ("FastAPI", FRAMEWORK),
    "starlette": ("Starlette", FRAMEWORK),
    "tornado": ("Tornado", FRAMEWORK),
    "aiohttp": ("aiohttp", FRAMEWORK),
    "streamlit": ("Streamlit", FRAMEWORK),
    "gradio": ("Gradio", FRAMEWORK),
    "scrapy": ("Scrapy", FRAMEWORK),
    "djangorestframework": ("Django REST framework", FRAMEWORK),
    "werkzeug": ("Werkzeug", LIBRARY),
    "jinja2": ("Jinja", LIBRARY),
    "scipy": ("SciPy", LIBRARY),
    "polars": ("Polars", LIBRARY),
    "opencv-python": ("OpenCV", LIBRARY),
    "pillow": ("Pillow", LIBRARY),
    "xgboost": ("XGBoost", LIBRARY),
    "boto3": ("AWS SDK (boto3)", LIBRARY),
    "sqlmodel": ("SQLModel", DATABASE),
    "selenium": ("Selenium", TESTING),
    "playwright": ("Playwright", TESTING),
    "torch": ("PyTorch", LIBRARY),
    "tensorflow": ("TensorFlow", LIBRARY),
    "keras": ("Keras", LIBRARY),
    "jax": ("JAX", LIBRARY),
    "scikit-learn": ("scikit-learn", LIBRARY),
    "transformers": ("Hugging Face Transformers", LIBRARY),
    "langchain": ("LangChain", LIBRARY),
    "llama-index": ("LlamaIndex", LIBRARY),
    "openai": ("OpenAI SDK", LIBRARY),
    "anthropic": ("Anthropic SDK", LIBRARY),
    "pandas": ("pandas", LIBRARY),
    "numpy": ("NumPy", LIBRARY),
    "matplotlib": ("Matplotlib", LIBRARY),
    "pydantic": ("Pydantic", LIBRARY),
    "requests": ("Requests", LIBRARY),
    "httpx": ("HTTPX", LIBRARY),
    "beautifulsoup4": ("Beautiful Soup", LIBRARY),
    "click": ("Click (CLI)", LIBRARY),
    "typer": ("Typer (CLI)", LIBRARY),
    "rich": ("Rich", LIBRARY),
    "celery": ("Celery", LIBRARY),
    "sqlalchemy": ("SQLAlchemy", DATABASE),
    "alembic": ("Alembic", DATABASE),
    "psycopg2": ("PostgreSQL", DATABASE),
    "psycopg2-binary": ("PostgreSQL", DATABASE),
    "psycopg": ("PostgreSQL", DATABASE),
    "asyncpg": ("PostgreSQL", DATABASE),
    "pymongo": ("MongoDB", DATABASE),
    "redis": ("Redis", DATABASE),
    "pytest": ("pytest", TESTING),
    "tox": ("tox", TESTING),
    "nox": ("nox", TESTING),
    "hypothesis": ("Hypothesis", TESTING),
    "uvicorn": ("Uvicorn", TOOLING),
    "gunicorn": ("Gunicorn", TOOLING),
    "ruff": ("Ruff", TOOLING),
    "black": ("Black", TOOLING),
    "mypy": ("mypy", TOOLING),
    "sphinx": ("Sphinx", TOOLING),
    "mkdocs": ("MkDocs", TOOLING),
}

GO = {
    "github.com/gin-gonic/gin": ("Gin", FRAMEWORK),
    "github.com/labstack/echo": ("Echo", FRAMEWORK),
    "github.com/gofiber/fiber": ("Fiber", FRAMEWORK),
    "github.com/go-chi/chi": ("chi", FRAMEWORK),
    "github.com/gorilla/mux": ("Gorilla Mux", FRAMEWORK),
    "github.com/spf13/cobra": ("Cobra (CLI)", LIBRARY),
    "github.com/spf13/viper": ("Viper (config)", LIBRARY),
    "github.com/charmbracelet/bubbletea": ("Bubble Tea (TUI)", LIBRARY),
    "google.golang.org/grpc": ("gRPC", LIBRARY),
    "go.uber.org/zap": ("zap (logging)", LIBRARY),
    "github.com/prometheus/client_golang": ("Prometheus", LIBRARY),
    "k8s.io/client-go": ("Kubernetes client", LIBRARY),
    "gorm.io/gorm": ("GORM", DATABASE),
    "github.com/jackc/pgx": ("PostgreSQL", DATABASE),
    "go.mongodb.org/mongo-driver": ("MongoDB", DATABASE),
    "github.com/redis/go-redis": ("Redis", DATABASE),
    "github.com/go-redis/redis": ("Redis", DATABASE),
    "github.com/stretchr/testify": ("Testify", TESTING),
}

CARGO = {
    "tokio": ("Tokio (async runtime)", LIBRARY),
    "actix-web": ("Actix Web", FRAMEWORK),
    "axum": ("Axum", FRAMEWORK),
    "rocket": ("Rocket", FRAMEWORK),
    "warp": ("Warp", FRAMEWORK),
    "tauri": ("Tauri", FRAMEWORK),
    "bevy": ("Bevy", FRAMEWORK),
    "leptos": ("Leptos", FRAMEWORK),
    "yew": ("Yew", FRAMEWORK),
    "serde": ("Serde", LIBRARY),
    "clap": ("clap (CLI)", LIBRARY),
    "reqwest": ("reqwest", LIBRARY),
    "tonic": ("Tonic (gRPC)", LIBRARY),
    "ratatui": ("Ratatui (TUI)", LIBRARY),
    "wasm-bindgen": ("WebAssembly", LIBRARY),
    "diesel": ("Diesel", DATABASE),
    "sqlx": ("SQLx", DATABASE),
    "sea-orm": ("SeaORM", DATABASE),
}

COMPOSER = {
    "laravel/framework": ("Laravel", FRAMEWORK),
    "symfony": ("Symfony", FRAMEWORK),
    "slim/slim": ("Slim", FRAMEWORK),
    "doctrine/orm": ("Doctrine", DATABASE),
    "phpunit/phpunit": ("PHPUnit", TESTING),
}

RUBYGEMS = {
    "rails": ("Ruby on Rails", FRAMEWORK),
    "sinatra": ("Sinatra", FRAMEWORK),
    "hanami": ("Hanami", FRAMEWORK),
    "jekyll": ("Jekyll", FRAMEWORK),
    "sidekiq": ("Sidekiq", LIBRARY),
    "devise": ("Devise (auth)", LIBRARY),
    "pg": ("PostgreSQL", DATABASE),
    "rspec": ("RSpec", TESTING),
    "rspec-rails": ("RSpec", TESTING),
    "puma": ("Puma", TOOLING),
}

# Manifests we can't fully parse: (regex, name, category), searched in the file text.
TEXT_RULES: dict[str, list[tuple[str, str, str]]] = {
    "pom.xml|build.gradle|build.gradle.kts": [
        (r"spring-boot", "Spring Boot", FRAMEWORK),
        (r"io\.quarkus", "Quarkus", FRAMEWORK),
        (r"io\.micronaut", "Micronaut", FRAMEWORK),
        (r"io\.ktor", "Ktor", FRAMEWORK),
        (r"com\.android\.(application|library)", "Android", FRAMEWORK),
        (r"hibernate", "Hibernate", DATABASE),
        (r"lombok", "Lombok", LIBRARY),
        (r"junit", "JUnit", TESTING),
        (r"mockito", "Mockito", TESTING),
    ],
    "pubspec.yaml": [
        (r"^\s*flutter:", "Flutter", FRAMEWORK),
        (r"firebase_core", "Firebase", DATABASE),
        (r"flutter_bloc", "BLoC", LIBRARY),
        (r"riverpod", "Riverpod", LIBRARY),
    ],
    "*.csproj": [
        (r"Microsoft\.AspNetCore|Microsoft\.NET\.Sdk\.Web", "ASP.NET Core", FRAMEWORK),
        (r"EntityFrameworkCore", "Entity Framework Core", DATABASE),
        (r"Maui", ".NET MAUI", FRAMEWORK),
        (r"xunit", "xUnit", TESTING),
        (r"NUnit", "NUnit", TESTING),
    ],
    "mix.exs": [
        (r":phoenix\b", "Phoenix", FRAMEWORK),
        (r":ecto", "Ecto", DATABASE),
    ],
}

# Files whose mere presence tells us something. Patterns without "/" match the
# file name anywhere; patterns with "/" match the full path.
FILE_RULES: list[tuple[str, str, str]] = [
    ("Dockerfile", "Docker", DEVOPS),
    ("Dockerfile.*", "Docker", DEVOPS),
    ("docker-compose*.y*ml", "Docker Compose", DEVOPS),
    ("compose.y*ml", "Docker Compose", DEVOPS),
    (".github/workflows/*", "GitHub Actions", DEVOPS),
    (".gitlab-ci.yml", "GitLab CI", DEVOPS),
    (".circleci/*", "CircleCI", DEVOPS),
    ("Jenkinsfile", "Jenkins", DEVOPS),
    ("*.tf", "Terraform", DEVOPS),
    ("Chart.yaml", "Helm", DEVOPS),
    ("k8s/*", "Kubernetes", DEVOPS),
    ("*/k8s/*", "Kubernetes", DEVOPS),
    ("vercel.json", "Vercel", DEVOPS),
    ("netlify.toml", "Netlify", DEVOPS),
    ("fly.toml", "Fly.io", DEVOPS),
    ("Procfile", "Heroku", DEVOPS),
    ("serverless.yml", "Serverless Framework", DEVOPS),
    (".devcontainer/*", "Dev Containers", DEVOPS),
    ("Makefile", "Make", TOOLING),
    ("CMakeLists.txt", "CMake", TOOLING),
    ("meson.build", "Meson", TOOLING),
    ("WORKSPACE", "Bazel", TOOLING),
    ("MODULE.bazel", "Bazel", TOOLING),
    ("package-lock.json", "npm", TOOLING),
    ("yarn.lock", "Yarn", TOOLING),
    ("pnpm-lock.yaml", "pnpm", TOOLING),
    ("bun.lock*", "Bun", TOOLING),
    ("poetry.lock", "Poetry", TOOLING),
    ("uv.lock", "uv", TOOLING),
    ("Pipfile.lock", "Pipenv", TOOLING),
    ("pdm.lock", "PDM", TOOLING),
    ("gradlew", "Gradle", TOOLING),
    ("pom.xml", "Maven", TOOLING),
    ("turbo.json", "Turborepo", TOOLING),
    ("nx.json", "Nx", TOOLING),
    ("lerna.json", "Lerna", TOOLING),
    ("pnpm-workspace.yaml", "pnpm workspaces (monorepo)", TOOLING),
    (".pre-commit-config.yaml", "pre-commit", TOOLING),
    (".eslintrc*", "ESLint", TOOLING),
    ("eslint.config.*", "ESLint", TOOLING),
    (".prettierrc*", "Prettier", TOOLING),
    ("biome.json*", "Biome", TOOLING),
    ("vite.config.*", "Vite", TOOLING),
    ("webpack.config.*", "webpack", TOOLING),
    ("mkdocs.yml", "MkDocs", TOOLING),
    ("docusaurus.config.*", "Docusaurus", TOOLING),
    ("docs/conf.py", "Sphinx", TOOLING),
    (".storybook/*", "Storybook", TOOLING),
    ("*.ipynb", "Jupyter Notebooks", TOOLING),
    ("tsconfig.json", "TypeScript", LANGUAGE),
    ("deno.json*", "Deno", LANGUAGE),
    ("next.config.*", "Next.js", FRAMEWORK),
    ("nuxt.config.*", "Nuxt", FRAMEWORK),
    ("angular.json", "Angular", FRAMEWORK),
    ("svelte.config.*", "Svelte", FRAMEWORK),
    ("astro.config.*", "Astro", FRAMEWORK),
    ("manage.py", "Django", FRAMEWORK),
    ("tailwind.config.*", "Tailwind CSS", LIBRARY),
    ("schema.prisma", "Prisma", DATABASE),
    ("alembic.ini", "Alembic", DATABASE),
    ("pytest.ini", "pytest", TESTING),
    ("conftest.py", "pytest", TESTING),
    ("tox.ini", "tox", TESTING),
    ("jest.config.*", "Jest", TESTING),
    ("vitest.config.*", "Vitest", TESTING),
    ("playwright.config.*", "Playwright", TESTING),
    ("cypress.config.*", "Cypress", TESTING),
]

# Big repos have tens of thousands of paths, so compile the globs once.
_FILE_RULES_COMPILED = [
    (re.compile(translate(pattern)), "/" in pattern, tech, category) for pattern, tech, category in FILE_RULES
]

_MANIFEST_NAMES = {
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile", "go.mod",
    "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts", "Gemfile",
    "composer.json", "pubspec.yaml", "mix.exs",
}  # fmt: skip


def is_manifest(path: str) -> bool:
    name = PurePosixPath(path).name
    return name in _MANIFEST_NAMES or fnmatchcase(name, "requirements*.txt") or name.endswith(".csproj")


# ---------------------------------------------------------------------------
# Manifest parsers: each returns the set of dependency names in a file.
# ---------------------------------------------------------------------------

_PY_REQ = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
_PY_QUOTED_REQ = re.compile(r"""['"]([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*(?:[<>=!~;][^'"]*)?['"]""")
_GO_REQ = re.compile(r"^\s*(?:require\s+)?([a-z0-9.\-]+\.[a-z]+/\S+)\s+v\d", re.MULTILINE)
_GEM = re.compile(r"""^\s*gem\s+['"]([^'"]+)['"]""", re.MULTILINE)


def _normalize_py(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _json_keys(text: str, sections: tuple[str, ...]) -> set[str]:
    try:
        data = json.loads(text)
    except ValueError:
        return set()
    names: set[str] = set()
    for section in sections:
        deps = data.get(section) if isinstance(data, dict) else None
        if isinstance(deps, dict):
            names.update(deps)
    return names


def _toml(text: str) -> dict:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}


def _requirements_names(lines: list[str]) -> set[str]:
    names = set()
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if line and not line.startswith("-"):
            match = _PY_REQ.match(line)
            if match:
                names.add(_normalize_py(match[1]))
    return names


def _pyproject_names(text: str) -> set[str]:
    data = _toml(text)
    project = data.get("project", {})
    specs: list = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        specs += group
    for group in data.get("dependency-groups", {}).values():
        specs += group
    names = _requirements_names([s for s in specs if isinstance(s, str)])

    poetry = data.get("tool", {}).get("poetry", {})
    poetry_sections = [poetry.get("dependencies", {}), poetry.get("dev-dependencies", {})]
    poetry_sections += [g.get("dependencies", {}) for g in poetry.get("group", {}).values()]
    for section in poetry_sections:
        names.update(_normalize_py(n) for n in section if n.lower() != "python")
    return names


def _cargo_names(text: str) -> set[str]:
    data = _toml(text)
    names: set[str] = set()
    for key in ("dependencies", "dev-dependencies", "build-dependencies"):
        names.update(data.get(key, {}))
    names.update(data.get("workspace", {}).get("dependencies", {}))
    return names


def _parse_manifest(path: str, text: str) -> tuple[set[str], dict]:
    """Returns (dependency names, table to match them against)."""
    name = PurePosixPath(path).name
    if name == "package.json":
        return _json_keys(text, ("dependencies", "devDependencies", "peerDependencies")), NPM
    if fnmatchcase(name, "requirements*.txt") or name == "setup.cfg":
        return _requirements_names(text.splitlines()), PYPI
    if name == "pyproject.toml":
        return _pyproject_names(text), PYPI
    if name == "setup.py":
        return {_normalize_py(n) for n in _PY_QUOTED_REQ.findall(text)}, PYPI
    if name == "Pipfile":
        data = _toml(text)
        return {_normalize_py(n) for n in [*data.get("packages", {}), *data.get("dev-packages", {})]}, PYPI
    if name == "go.mod":
        return {m.lower() for m in _GO_REQ.findall(text)}, GO
    if name == "Cargo.toml":
        return _cargo_names(text), CARGO
    if name == "composer.json":
        return _json_keys(text, ("require", "require-dev")), COMPOSER
    if name == "Gemfile":
        return set(_GEM.findall(text)), RUBYGEMS
    return set(), {}


def _lookup(dep: str, table: dict) -> tuple[str, str] | None:
    dep = dep.lower()
    for key, value in table.items():
        if dep == key or dep.startswith(key + "/"):
            return value
    return None


def list_dependencies(manifests: dict[str, str], limit: int = 80) -> list[dict]:
    """Raw dependency names from top-level manifests, so anything our tables don't know is still visible."""
    result = []
    for path in sorted(manifests, key=lambda p: (p.count("/"), p)):
        if path.count("/") <= 1:
            deps, _ = _parse_manifest(path, manifests[path])
            if deps:
                result.append({"source": path, "names": sorted(deps)[:limit], "total": len(deps)})
    return result


def detect_stack(paths: list[str], manifests: dict[str, str]) -> list[dict]:
    """Returns `[{name, category, source}]`, deduplicated by name, shallowest evidence first."""
    found: dict[str, dict] = {}

    def add(name: str, category: str, source: str) -> None:
        found.setdefault(name, {"name": name, "category": category, "source": source})

    for path in sorted(manifests, key=lambda p: (p.count("/"), p)):
        text = manifests[path]
        deps, table = _parse_manifest(path, text)
        for dep in sorted(deps):
            hit = _lookup(dep, table)
            if hit:
                add(*hit, path)
        name = PurePosixPath(path).name
        for patterns, rules in TEXT_RULES.items():
            if any(fnmatchcase(name, p) for p in patterns.split("|")):
                for regex, tech, category in rules:
                    if re.search(regex, text, re.MULTILINE):
                        add(tech, category, path)

    for path in sorted(paths, key=lambda p: (p.count("/"), p)):
        name = PurePosixPath(path).name
        for regex, matches_full_path, tech, category in _FILE_RULES_COMPILED:
            if tech not in found and regex.match(path if matches_full_path else name):
                add(tech, category, path)

    return list(found.values())

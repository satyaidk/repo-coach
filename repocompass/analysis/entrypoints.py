"""Find where a project starts running and how to run it: the first things a newcomer needs."""

import json
import re
import tomllib

# (path regex, why it matters, priority: lower = more important)
_PATH_RULES = [
    (r"(^|/)__main__\.py$", "Runs when you do `python -m <package>`", 1),
    (r"^(src/)?[^/]+/__init__\.py$", "Package root: what `import <package>` loads", 2.5),
    (r"(^|/)manage\.py$", "Django's command-line entry (runserver, migrations...)", 1),
    (r"(^|/)(wsgi|asgi)\.py$", "Web server entry: the WSGI/ASGI app object lives here", 2),
    (r"(^|/)(main|app|server|run|cli)\.py$", "Python script entry point", 2),
    (r"(^|/)main\.go$", "Go program entry (`func main`)", 1),
    (r"^src/main\.rs$", "Rust binary entry (`fn main`)", 1),
    (r"^src/lib\.rs$", "Rust library root: the public API starts here", 2),
    (r"^src/bin/[^/]+\.rs$", "Extra Rust binary", 3),
    (r"^(src/)?app/layout\.(tsx|jsx|ts|js)$", "Next.js root layout (wraps every page)", 1),
    (r"^(src/)?pages/_app\.(tsx|jsx|ts|js)$", "Next.js pages entry (wraps every page)", 1),
    (r"^(src/)?(main|index)\.(tsx|jsx)$", "Frontend bootstrap: mounts the app into the page", 1),
    (r"^[^/]+/(src/)?(main|index)\.(tsx|jsx)$", "Frontend bootstrap of an app in this repo", 2),
    (r"^(src/)?App\.(tsx|jsx|vue|svelte)$", "Root UI component", 2),
    (r"^(src/)?(index|main|server|app)\.(js|ts|mjs|cjs)$", "JavaScript/TypeScript entry point", 1),
    (r"^(packages|apps)/[^/]+/(src/)?(index|main|server|app)\.(js|ts|mjs|tsx)$", "Entry of one package in this monorepo", 2),
    (r"(^|/)[A-Z]\w*Application\.(java|kt)$", "Spring Boot application class (`main` method)", 1),
    (r"(^|/)Main\.(java|kt)$", "JVM program entry (`main` method)", 2),
    (r"(^|/)Program\.cs$", ".NET program entry", 1),
    (r"^lib/main\.dart$", "Flutter app entry", 1),
    (r"(^|/)main\.(c|cc|cpp)$", "C/C++ program entry (`main`)", 2),
    (r"^config/routes\.rb$", "Rails routes: maps URLs to controllers", 1),
    (r"^(public/)?index\.php$", "PHP front controller", 2),
    (r"^index\.html$", "Static site / frontend HTML entry", 3),
]
_COMPILED_RULES = [(re.compile(p), reason, prio) for p, reason, prio in _PATH_RULES]

# Entry-looking files in these folders are usually not *the* entry point.
NOISY_DIRS = re.compile(
    r"(^|/)(tests?|__tests__|examples?|samples?|demos?|fixtures?|docs?|benchmarks?|vendor|third_party|scripts)/"
)

_TEST_FILE = re.compile(
    r"(^|/)(tests?|__tests__|spec)/|_test\.go$|\.(test|spec)\.[jt]sx?$|(^|/)test_[^/]+\.py$|_spec\.rb$"
)
_MAKE_TARGET =re.compile(r"^([A-Za-z][\w-]*)\s*:(?!=)", re.MULTILINE)
_USEFUL_TARGETS = ["install", "setup", "deps", "dev", "run", "start", "serve", "build", "test", "lint"]
_USEFUL_SCRIPTS = ["dev", "start", "serve", "build", "test", "lint"]


def _json(text: str | None) -> dict:
    try:
        data = json.loads(text or "")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _toml(text: str | None) -> dict:
    try:
        return tomllib.loads(text or "")
    except tomllib.TOMLDecodeError:
        return {}


def _module_to_path(module: str, paths: set[str]) -> str | None:
    base = module.split(":")[0].replace(".", "/")
    for candidate in (f"{base}.py", f"src/{base}.py", f"{base}/__init__.py", f"src/{base}/__init__.py"):
        if candidate in paths:
            return candidate
    return None


def find_entry_points(paths: list[str], files: dict[str, str], repo_name: str = "", limit: int = 10) -> list[dict]:
    """Returns `[{path, reason}]`, most likely entry points first."""
    path_set = set(paths)
    scored: dict[str, tuple[float, str]] = {}

    def add(path: str, reason: str, priority: float) -> None:
        if path in path_set and (path not in scored or priority < scored[path][0]):
            scored[path] = (priority, reason)

    # Go libraries usually have a root file named after the package (gin -> gin.go).
    if repo_name:
        add(f"{repo_name.lower()}.go", "Main file of this Go package (its public API starts here)", 1.5)

    for path in paths:
        depth = path.count("/")
        if depth > 4:
            continue
        for regex, reason, priority in _COMPILED_RULES:
            if regex.search(path):
                penalty = 3 if NOISY_DIRS.search(path) else 0
                add(path, reason, priority + penalty + depth * 0.25)
                break

    package = _json(files.get("package.json"))
    if isinstance(package.get("main"), str):
        add(package["main"].removeprefix("./"), "Package entry (`main` in package.json)", 0.5)
    bins = package.get("bin")
    if isinstance(bins, str):
        bins = {package.get("name", "cli"): bins}
    if isinstance(bins, dict):
        for command, target in bins.items():
            if isinstance(target, str):
                add(target.removeprefix("./"), f"CLI command `{command}` (bin in package.json)", 0.5)

    pyproject = _toml(files.get("pyproject.toml"))
    scripts = dict(pyproject.get("project", {}).get("scripts", {}))
    scripts.update(pyproject.get("tool", {}).get("poetry", {}).get("scripts", {}))
    for command, target in scripts.items():
        if isinstance(target, str):
            path = _module_to_path(target, path_set)
            if path:
                add(path, f"CLI command `{command}` → `{target}` (pyproject.toml)", 0.5)

    ranked = sorted(scored.items(), key=lambda item: (item[1][0], item[0]))
    # Entry-looking files under tests/, examples/... only help if there's nothing better.
    main_ones = [item for item in ranked if not NOISY_DIRS.search(item[0])]
    if len(main_ones) >= 3:
        ranked = main_ones
    return [{"path": path, "reason": reason} for path, (_, reason) in ranked[:limit]]


def _node_package_manager(path_set: set[str]) -> str:
    if "pnpm-lock.yaml" in path_set:
        return "pnpm"
    if "yarn.lock" in path_set:
        return "yarn"
    if "bun.lockb" in path_set or "bun.lock" in path_set:
        return "bun"
    return "npm"


def find_run_commands(paths: list[str], files: dict[str, str]) -> list[dict]:
    """Setup/run/test commands we can read straight from config files: `[{command, source, note}]`."""
    path_set = set(paths)
    commands: list[dict] = []

    def add(command: str, source: str, note: str = "") -> None:
        if all(c["command"] != command for c in commands):
            commands.append({"command": command, "source": source, "note": note})

    if "package.json" in files:
        pm = _node_package_manager(path_set)
        add(f"{pm} install", "package.json", "Install JavaScript dependencies")
        scripts = _json(files["package.json"]).get("scripts", {})
        if isinstance(scripts, dict):
            for name in _USEFUL_SCRIPTS:
                if isinstance(scripts.get(name), str):
                    run = f"{pm} run {name}" if pm in ("npm", "bun") else f"{pm} {name}"
                    add(run, "package.json", scripts[name])

    if "uv.lock" in path_set:
        add("uv sync", "uv.lock", "Create a virtualenv and install Python dependencies")
    elif "poetry.lock" in path_set:
        add("poetry install", "poetry.lock", "Install Python dependencies")
    elif "Pipfile" in path_set:
        add("pipenv install --dev", "Pipfile", "Install Python dependencies")
    elif "requirements.txt" in path_set:
        add("pip install -r requirements.txt", "requirements.txt", "Install Python dependencies")
    elif "pyproject.toml" in path_set or "setup.py" in path_set:
        add("pip install -e .", "pyproject.toml" if "pyproject.toml" in path_set else "setup.py",
            "Install this package in editable mode")  # fmt: skip
    if "manage.py" in path_set:
        add("python manage.py runserver", "manage.py", "Start the Django dev server")

    if "Cargo.toml" in path_set:
        add("cargo build", "Cargo.toml", "Compile the project")
        add("cargo test", "Cargo.toml", "Run the tests")
    if "go.mod" in path_set:
        add("go build ./...", "go.mod", "Compile every package")
        add("go test ./...", "go.mod", "Run the tests")

    makefile = files.get("Makefile")
    if makefile:
        targets = set(_MAKE_TARGET.findall(makefile))
        for target in _USEFUL_TARGETS:
            if target in targets:
                add(f"make {target}", "Makefile")

    compose = next((p for p in ("docker-compose.yml", "docker-compose.yaml", "compose.yaml", "compose.yml")
                    if p in path_set), None)  # fmt: skip
    if compose:
        add("docker compose up", compose, "Start the whole stack in containers")

    return commands


def find_community_files(paths: list[str]) -> dict[str, str | None]:
    """Signals that a repo welcomes contributors (maps each kind to its path, or None)."""
    by_lower = {p.lower(): p for p in paths}

    def first(*candidates: str) -> str | None:
        return next((by_lower[c] for c in candidates if c in by_lower), None)

    def first_prefix(prefix: str) -> str | None:
        return next((p for lower, p in by_lower.items() if lower.startswith(prefix)), None)

    def in_common_places(name: str) -> tuple[str, ...]:
        return tuple(f"{folder}{name}.{ext}" for folder in ("", ".github/", "docs/") for ext in ("md", "rst", "txt"))

    test_paths = [p for p in paths if _TEST_FILE.search(p)]
    return {
        "readme": first("readme.md", "readme.rst", "readme.txt", "readme"),
        "contributing": first(*in_common_places("contributing")),
        "code_of_conduct": first(*in_common_places("code_of_conduct")),
        "license": first("license", "license.md", "license.txt", "copying"),
        "security": first(*in_common_places("security")),
        "issue_templates": first_prefix(".github/issue_template"),
        "pr_template": first(".github/pull_request_template.md", "pull_request_template.md"),
        "tests": min(test_paths, key=lambda p: (p.count("/"), p), default=None),
        "ci": first_prefix(".github/workflows/") or first(".gitlab-ci.yml", ".circleci/config.yml"),
    }

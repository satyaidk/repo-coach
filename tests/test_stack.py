import json

from repocompass.analysis.stack import detect_stack, is_manifest, list_dependencies


def names(stack):
    return {s["name"] for s in stack}


def test_package_json_dependencies():
    manifest = json.dumps({
        "dependencies": {"react": "^18", "@tanstack/react-query": "5", "@aws-sdk/client-s3": "3"},
        "devDependencies": {"vite": "5", "vitest": "1", "typescript": "5"},
    })
    stack = detect_stack(["package.json"], {"package.json": manifest})
    assert {"React", "TanStack Query", "AWS SDK", "Vite", "Vitest", "TypeScript"} <= names(stack)
    react = next(s for s in stack if s["name"] == "React")
    assert react == {"name": "React", "category": "Framework", "source": "package.json"}


def test_python_manifests():
    requirements = "Django>=4.2  # web\n-r base.txt\npsycopg2-binary==2.9\n\nPyTest\n"
    pyproject = """
[project]
dependencies = ["fastapi>=0.100", "SQLAlchemy[asyncio]"]
[project.optional-dependencies]
dev = ["ruff"]
[tool.poetry.dependencies]
python = "^3.11"
celery = "*"
"""
    stack = detect_stack(
        ["requirements.txt", "pyproject.toml"],
        {"requirements.txt": requirements, "pyproject.toml": pyproject},
    )
    assert {"Django", "PostgreSQL", "pytest", "FastAPI", "SQLAlchemy", "Ruff", "Celery"} <= names(stack)


def test_setup_py_only_reads_requirement_strings():
    setup = 'setup(description="uses requests a lot", install_requires=["flask>=2", "click"])'
    assert names(detect_stack(["setup.py"], {"setup.py": setup})) == {"Flask", "Click (CLI)"}


def test_go_and_cargo():
    go_mod = "module example.com/app\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.1\n\tgorm.io/gorm v1.25.0\n)\n"
    cargo = '[dependencies]\ntokio = { version = "1" }\naxum = "0.7"\n[dev-dependencies]\nsqlx = "0.7"\n'
    stack = detect_stack(["go.mod", "Cargo.toml"], {"go.mod": go_mod, "Cargo.toml": cargo})
    assert {"Gin", "GORM", "Tokio (async runtime)", "Axum", "SQLx"} <= names(stack)


def test_go_module_major_versions_match():
    go_mod = "require github.com/labstack/echo/v4 v4.11.0\n"
    assert "Echo" in names(detect_stack(["go.mod"], {"go.mod": go_mod}))


def test_text_rules_for_jvm():
    pom = "<artifactId>spring-boot-starter-web</artifactId><artifactId>junit-jupiter</artifactId>"
    assert {"Spring Boot", "JUnit", "Maven"} <= names(detect_stack(["pom.xml"], {"pom.xml": pom}))


def test_file_presence_rules():
    paths = [
        "Dockerfile", ".github/workflows/ci.yml", "infra/main.tf", "pnpm-lock.yaml",
        "deploy/k8s/app.yaml", "tsconfig.json", "web/next.config.mjs",
    ]
    assert {
        "Docker", "GitHub Actions", "Terraform", "pnpm", "Kubernetes", "TypeScript", "Next.js",
    } <= names(detect_stack(paths, {}))


def test_file_rules_are_case_sensitive():
    assert "Docker" not in names(detect_stack(["dockerfile.md"], {}))


def test_broken_manifests_are_ignored():
    stack = detect_stack(["package.json", "pyproject.toml"], {"package.json": "{oops", "pyproject.toml": "[[bad"})
    assert stack == []


def test_is_manifest():
    assert is_manifest("package.json")
    assert is_manifest("backend/requirements-dev.txt")
    assert is_manifest("src/App/App.csproj")
    assert not is_manifest("README.md")


def test_list_dependencies_only_top_levels():
    manifests = {
        "package.json": json.dumps({"dependencies": {"b": "1", "a": "1"}}),
        "a/b/package.json": json.dumps({"dependencies": {"deep": "1"}}),
    }
    assert list_dependencies(manifests) == [{"source": "package.json", "names": ["a", "b"], "total": 2}]

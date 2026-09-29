import json

from repocompass.analysis.entrypoints import find_community_files, find_entry_points, find_run_commands


def entry_paths(paths, files=None, **kwargs):
    return [e["path"] for e in find_entry_points(paths, files or {}, **kwargs)]


def test_python_package_entries_rank_above_test_apps():
    paths = [
        "src/flask/__main__.py", "src/flask/app.py", "src/flask/__init__.py", "src/flask/cli.py",
        "tests/test_apps/app.py", "examples/tutorial/app.py",
    ]
    found = entry_paths(paths)
    assert found[0] == "src/flask/__main__.py"
    assert "tests/test_apps/app.py" not in found  # dropped: enough real entry points exist


def test_noisy_entries_kept_when_nothing_better():
    assert entry_paths(["examples/demo/main.py"]) == ["examples/demo/main.py"]


def test_package_json_main_and_bin():
    package = json.dumps({"name": "tool", "main": "./lib/index.js", "bin": {"tool": "./bin/cli.js"}})
    found = entry_paths(["lib/index.js", "bin/cli.js", "package.json"], {"package.json": package})
    assert set(found[:2]) == {"lib/index.js", "bin/cli.js"}


def test_pyproject_scripts_point_to_modules():
    pyproject = '[project.scripts]\nmytool = "mytool.cli:main"\n'
    found = find_entry_points(["src/mytool/cli.py"], {"pyproject.toml": pyproject})
    assert found[0]["path"] == "src/mytool/cli.py"
    assert "mytool" in found[0]["reason"]


def test_go_library_root_file():
    assert entry_paths(["gin.go", "context.go", "render/json.go"], repo_name="gin") == ["gin.go"]


def test_frontend_and_monorepo_entries():
    found = entry_paths(["src/main.tsx", "src/App.tsx", "web-app/index.tsx", "packages/ui/src/index.ts"])
    assert found[0] == "src/main.tsx"
    assert {"src/App.tsx", "web-app/index.tsx", "packages/ui/src/index.ts"} <= set(found)


def test_paths_that_do_not_exist_are_never_returned():
    package = json.dumps({"main": "dist/index.js"})  # build output, not committed
    assert entry_paths(["src/index.ts"], {"package.json": package}) == ["src/index.ts"]


def test_run_commands_from_config_files():
    package = json.dumps({"scripts": {"dev": "vite", "test": "vitest", "postinstall": "x"}})
    makefile = "install:\n\tpip install .\ntest: install\n\tpytest\nVAR := 1\n"
    paths = ["package.json", "yarn.lock", "requirements.txt", "Makefile", "docker-compose.yml"]
    commands = [c["command"] for c in find_run_commands(paths, {"package.json": package, "Makefile": makefile})]
    assert commands == [
        "yarn install", "yarn dev", "yarn test",
        "pip install -r requirements.txt",
        "make install", "make test",
        "docker compose up",
    ]


def test_community_files():
    paths = [
        "README.md", "docs/CONTRIBUTING.rst", "LICENSE", ".github/ISSUE_TEMPLATE/bug.md",
        ".github/workflows/ci.yml", "examples/x/tests/t.py", "tests/test_core.py",
    ]
    found = find_community_files(paths)
    assert found["readme"] == "README.md"
    assert found["contributing"] == "docs/CONTRIBUTING.rst"
    assert found["license"] == "LICENSE"
    assert found["issue_templates"] == ".github/ISSUE_TEMPLATE/bug.md"
    assert found["tests"] == "tests/test_core.py"  # the shallowest match wins
    assert found["code_of_conduct"] is None


def test_go_style_tests_count_as_tests():
    assert find_community_files(["gin.go", "gin_test.go"])["tests"] == "gin_test.go"

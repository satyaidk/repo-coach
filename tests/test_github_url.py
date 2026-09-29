import pytest

from repocompass.github import InvalidRepoURL, RepoRef, parse_repo_url


@pytest.mark.parametrize(
    "text, expected",
    [
        ("https://github.com/pallets/flask", RepoRef("pallets", "flask")),
        ("https://github.com/pallets/flask/", RepoRef("pallets", "flask")),
        ("https://github.com/pallets/flask.git", RepoRef("pallets", "flask")),
        ("http://www.github.com/pallets/flask", RepoRef("pallets", "flask")),
        ("github.com/pallets/flask", RepoRef("pallets", "flask")),
        ("  pallets/flask  ", RepoRef("pallets", "flask")),
        ("git@github.com:pallets/flask.git", RepoRef("pallets", "flask")),
        ("https://github.com/pallets/flask/tree/3.0.x", RepoRef("pallets", "flask", "3.0.x")),
        ("https://github.com/pallets/flask/tree/main/src/flask", RepoRef("pallets", "flask", "main")),
        ("https://github.com/pallets/flask/blob/main/README.md", RepoRef("pallets", "flask", "main")),
        ("https://github.com/pallets/flask/issues/42", RepoRef("pallets", "flask")),
        ("https://github.com/vercel/next.js", RepoRef("vercel", "next.js")),
    ],
)
def test_parses_common_url_shapes(text, expected):
    assert parse_repo_url(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", "flask", "https://gitlab.com/a/b", "https://github.com/pallets", "github.com/pallets", "not a url at all"],
)
def test_rejects_non_repo_input(text):
    with pytest.raises(InvalidRepoURL):
        parse_repo_url(text)

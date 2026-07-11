import pytest

from app.utils.github_url import InvalidGitHubURLError, parse_github_repository


@pytest.mark.parametrize(
    ("source", "owner", "name"),
    [
        ("https://github.com/octocat/Hello-World", "octocat", "Hello-World"),
        ("http://github.com/octocat/Hello-World.git", "octocat", "Hello-World"),
        ("github.com/octocat/Hello-World", "octocat", "Hello-World"),
        ("octocat/Hello-World", "octocat", "Hello-World"),
    ],
)
def test_parse_github_repository_valid(source: str, owner: str, name: str) -> None:
    repo_ref = parse_github_repository(source)
    assert repo_ref.owner == owner
    assert repo_ref.name == name
    assert repo_ref.clone_url == f"https://github.com/{owner}/{name}.git"


@pytest.mark.parametrize(
    "source",
    [
        "",
        "not-a-url",
        "https://gitlab.com/octocat/Hello-World",
        "https://github.com/octocat",
        "https://github.com/octocat/repo/extra",
        "octocat/repo;rm -rf /",
        "https://github.com/-bad/repo",
    ],
)
def test_parse_github_repository_invalid(source: str) -> None:
    with pytest.raises(InvalidGitHubURLError):
        parse_github_repository(source)

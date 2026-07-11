import re
from dataclasses import dataclass
from urllib.parse import urlparse

GITHUB_HOSTS = frozenset({"github.com", "www.github.com"})

OWNER_PATTERN = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$")
REPO_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")

FORBIDDEN_CHARACTERS = frozenset("\n\r\0;|&$`<>\"'\\")


class InvalidGitHubURLError(ValueError):
    """Raised when a repository reference is not a valid public GitHub URL."""


@dataclass(frozen=True)
class GitHubRepositoryRef:
    owner: str
    name: str

    @property
    def clone_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.name}.git"

    @property
    def html_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.name}"


def _validate_segment(value: str, pattern: re.Pattern[str], label: str) -> str:
    if not pattern.fullmatch(value):
        raise InvalidGitHubURLError(f"Invalid GitHub {label}")
    return value


def parse_github_repository(source: str) -> GitHubRepositoryRef:
    """Parse and validate a GitHub repository URL or owner/name shorthand."""
    normalized = source.strip()
    if not normalized:
        raise InvalidGitHubURLError("Repository URL is required")

    if any(char in normalized for char in FORBIDDEN_CHARACTERS):
        raise InvalidGitHubURLError("Repository URL contains invalid characters")

    if "github.com" not in normalized.lower():
        parts = normalized.strip("/").split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise InvalidGitHubURLError(
                "Provide a GitHub URL or owner/repository name"
            )
        owner = _validate_segment(parts[0], OWNER_PATTERN, "owner")
        repo = _validate_segment(
            parts[1].removesuffix(".git"),
            REPO_PATTERN,
            "repository name",
        )
        return GitHubRepositoryRef(owner=owner, name=repo)

    candidate = normalized
    if not candidate.startswith(("http://", "https://")):
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    if parsed.netloc.lower() not in GITHUB_HOSTS:
        raise InvalidGitHubURLError("Only github.com repositories are supported")

    if parsed.scheme not in {"http", "https"}:
        raise InvalidGitHubURLError("Repository URL must use HTTP or HTTPS")

    path_parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(path_parts) != 2:
        raise InvalidGitHubURLError("Repository URL must include owner and name only")

    owner = _validate_segment(path_parts[0], OWNER_PATTERN, "owner")
    repo = _validate_segment(
        path_parts[1].removesuffix(".git"),
        REPO_PATTERN,
        "repository name",
    )
    return GitHubRepositoryRef(owner=owner, name=repo)

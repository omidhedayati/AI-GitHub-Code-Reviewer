import shutil
import subprocess
import uuid
from pathlib import Path

from app.config.settings import Settings
from app.utils.github_url import GitHubRepositoryRef


class GitCloneError(Exception):
    """Raised when git clone fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class GitService:
    """Safe git operations using subprocess without shell invocation."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._workspace_root = Path(settings.repos_workspace_root)

    def ensure_workspace(self) -> None:
        self._workspace_root.mkdir(parents=True, exist_ok=True)

    def resolve_clone_directory(
        self,
        user_id: uuid.UUID,
        repository_id: uuid.UUID,
    ) -> Path:
        base = self._workspace_root.resolve()
        target = (base / str(user_id) / str(repository_id)).resolve()
        if base not in target.parents and target != base:
            raise ValueError("Invalid clone path")
        return target

    def clone_repository(
        self,
        repo_ref: GitHubRepositoryRef,
        destination: Path,
        *,
        branch: str | None = None,
    ) -> str:
        self.ensure_workspace()
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            shutil.rmtree(destination)

        command = [
            "git",
            "clone",
            "--depth",
            str(self._settings.git_clone_depth),
        ]
        if branch:
            command.extend(["--branch", branch])
        command.extend([repo_ref.clone_url, str(destination)])

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self._settings.git_clone_timeout_seconds,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or exc.stdout or "Git clone failed").strip()
            raise GitCloneError(stderr) from exc
        except subprocess.TimeoutExpired as exc:
            raise GitCloneError("Git clone timed out") from exc

        return self.detect_default_branch(destination)

    def detect_default_branch(self, repository_path: Path) -> str:
        result = subprocess.run(
            ["git", "-C", str(repository_path), "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()

    def remove_repository(self, repository_path: str | Path) -> None:
        resolved = Path(repository_path).resolve()
        base = self._workspace_root.resolve()
        if base not in resolved.parents:
            raise ValueError("Refusing to delete path outside workspace")
        if resolved.exists():
            shutil.rmtree(resolved)

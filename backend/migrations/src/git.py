import subprocess
from pathlib import Path


def commit(path: str, message: str) -> None:
    """Commit changes to the Git repository at the specified path.

    Args:
        path (str): Path to the Git repository.
        message (str): Commit message.

    """
    cwd = Path(path).absolute()
    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=cwd,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=cwd,
            check=True,
        )
        print(f"Committed changes in {cwd} with message: {message}")
    except subprocess.CalledProcessError as e:
        print(f"Error committing changes in {cwd}: {e}")

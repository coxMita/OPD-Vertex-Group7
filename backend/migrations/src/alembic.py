import re
import subprocess
import tempfile


def run_downgrade(service_name: str, steps: int) -> None:
    """Run Alembic downgrade for the specified service by the given number of steps.

    Args:
        service_name (str): Name of the service.
        steps (int): Number of steps to downgrade.

    """
    print(f"Running downgrade for service: {service_name} by {steps} steps...")
    cmd = [
        "docker",
        "exec",
        "-it",
        service_name,
        "uv",
        "run",
        "alembic",
        "downgrade",
        str(steps),
    ]
    subprocess.run(
        cmd,
        check=True,
        shell=False,
    )


def run_upgrade(service_name: str) -> None:
    """Run Alembic upgrade to head for the specified service.

    Args:
        service_name (str): Name of the service.

    """
    print(f"Running migrations for service: {service_name}")
    cmd = [
        "docker",
        "exec",
        "-it",
        service_name,
        "uv",
        "run",
        "alembic",
        "upgrade",
        "head",
    ]
    subprocess.run(
        cmd,
        check=True,
        shell=False,
    )


def create_new_revision(service_name: str, message: str) -> str:
    """Create a new Alembic revision with autogeneration. Make sure that the container is running.

    Args:
        service_name (str): Name of the service.
        message (str): Message for the new revision.

    Returns:
        str: Path to the generated Alembic revision file.

    """  # noqa: E501
    cmd = [
        "docker",
        "exec",
        "-it",
        service_name,
        "uv",
        "run",
        "alembic",
        "revision",
        "--autogenerate",
        "-m",
        message,
    ]
    print("Creating new revision...")
    result = subprocess.run(
        cmd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
    )
    print("Alembic revision command output:", result.stdout)
    return _get_file_path_from_output(result.stdout)


def _get_file_path_from_output(output: str) -> str:
    match = re.search(r"Generating (.*?\.py)", output)
    if not match:
        raise RuntimeError("Could not find generated Alembic file path in output.")

    file_path = match.group(1)
    print("Detected Alembic file:", file_path)
    return file_path


def fix_auto_string_in_revisions(service_name: str, file_path: str) -> None:
    """Fix AutoString to String in the specified Alembic revision file.

    Args:
        service_name (str): Name of the service.
        file_path (str): Path to the Alembic revision file inside the container.

    """
    file_content = _get_file_content(service_name, file_path)
    updated_content = _replace_auto_string_with_sa_string(file_content)
    _write_file_content(service_name, file_path, updated_content)


def _get_file_content(service_name: str, file_path: str) -> str:
    """Get the content of a file inside a Docker container.

    Args:
        service_name (str): Name of the service.
        file_path (str): Path to the file inside the container.

    Returns:
        str: Content of the file.

    """
    read_cmd = ["docker", "exec", service_name, "cat", file_path]
    return subprocess.check_output(read_cmd, text=True)


def _replace_auto_string_with_sa_string(content: str) -> str:
    """Replace AutoString with sa.String in the given content.

    Args:
        content (str): Original file content.

    Returns:
        str: Updated file content.

    """
    return content.replace("sqlmodel.sql.sqltypes.AutoString()", "sa.String()")


def _write_file_content(service_name: str, file_path: str, content: str) -> None:
    """Write content to a file inside a Docker container.

    Args:
        service_name (str): Name of the service.
        file_path (str): Path to the file inside the container.
        content (str): Content to write to the file.

    """
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    copy_cmd = ["docker", "cp", tmp_path, f"{service_name}:{file_path}"]
    subprocess.run(copy_cmd, check=True, shell=False)
    print("Updated Alembic file written back to container.")

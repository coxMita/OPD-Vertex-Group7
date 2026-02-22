import subprocess


def start_rabbitmq() -> None:
    """Start the RabbitMQ service using Docker Compose."""
    print("*** Starting RabbitMQ service ***")
    subprocess.run(
        ["docker", "compose", "up", "-d", "rabbitmq"], check=True, shell=False
    )


def start_service(service_name: str) -> None:
    """Start a specific service using Docker Compose.

    Args:
        service_name (str): Name of the service to start.

    """
    print(f"*** Starting service: {service_name} ***")
    subprocess.run(
        ["docker", "compose", "up", "-d", service_name], check=True, shell=False
    )


def stop_all_containers() -> None:
    """Stop all running Docker containers using Docker Compose."""
    print("*** Stopping all running containers ***")
    subprocess.run(["docker", "compose", "down"], check=True, shell=False)


def prune_volume(volume: str) -> None:
    """Prune Docker volumes for the specified service if prune is True.

    Args:
        volume (str): Docker volume name.

    """
    print(f"Pruning Docker volume: {volume}")
    if volume is None:
        print("No docker-volume specified in the configuration.")
        return
    subprocess.run(
        ["docker", "volume", "rm", volume],
        check=False,
        shell=False,
    )


def copy_file_from_container(
    service_name: str, source_path: str, destination_path: str
) -> None:
    """Copy a file from a Docker container to the host machine.

    Args:
        service_name (str): Name of the Docker service/container.
        source_path (str): Path to the file inside the container.
        destination_path (str): Path on the host machine where the file will be copied.

    """
    subprocess.run(
        ["docker", "cp", f"{service_name}:{source_path}", destination_path],
        check=True,
        shell=False,
    )

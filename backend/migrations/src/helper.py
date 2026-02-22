from dataclasses import dataclass
from typing import Any

from src.alembic import (
    create_new_revision,
    fix_auto_string_in_revisions,
    run_downgrade,
    run_upgrade,
)
from src.docker import (
    copy_file_from_container,
    prune_volume,
    start_service,
    stop_all_containers,
)
from src.git import commit


@dataclass(frozen=True)
class CommandLineArgs:
    """Command line arguments for migration operations.

    Attributes:
        operation (str): Operation to perform ("revision" or "upgrade" or "downgrade").
        steps (int | None): Number of steps to downgrade (only for downgrade operation).
        message (str | None): Message for the new revision.
        service_name (str | None): Name of the service to run migrations for.
        prune (bool): Whether to prune Docker volumes before running migrations.
        commit_changes (bool): Whether to commit changes to Git after creating a revision.

    """  # noqa: E501

    operation: str
    steps: int | None
    message: str | None
    service_name: str | None
    prune: bool
    commit_changes: bool


@dataclass(frozen=True)
class RevisionConfig:
    """Configuration for running revision steps.

    Attributes:
        message (str): Message for the new revision.
        prune (bool): Whether to prune Docker volumes before running migrations.
        service_name (str): Name of the service.
        services (list[Any]): List of service configurations.
        commit_changes (bool): Whether to commit changes to Git after creating a revision.

    """  # noqa: E501

    message: str
    prune: bool
    service_name: str
    services: list[Any]
    commit_changes: bool


def run_downgrade_steps(service_name: str, steps: int) -> None:
    """Run the steps to downgrade the database schema for the specified service.

    Args:
        service_name (str): Name of the service.
        steps (int): Number of steps to downgrade.

    """
    start_service(service_name)
    run_downgrade(service_name, steps)


def run_revision_steps(config: RevisionConfig) -> None:
    """Run the steps to create a new Alembic revision for the specified service.

    Args:
        config (RevisionConfig): Configuration for running revision steps.

    """
    if config.prune:
        prune_volume(config.services[0].get("docker-volume"))
        run_upgrade(config.service_name)
    start_service(config.service_name)
    file_path = create_new_revision(config.service_name, config.message)
    fix_auto_string_in_revisions(config.service_name, file_path)
    run_upgrade(config.service_name)
    versions_path = config.services[0].get("migrations-versions-path")
    copy_file_from_container(config.service_name, file_path, versions_path)
    if config.commit_changes:
        commit(versions_path, f"feat: migration - {config.message}")


def run_upgrade_steps(prune: bool, service: dict) -> None:
    """Run the steps to upgrade the database schema for the specified service.

    Args:
        prune (bool): Whether to prune Docker volumes before running migrations.
        service (dict): Service configuration.

    """
    name = service.get("name")
    if prune:
        prune_volume(service.get("docker-volume"))
    start_service(name)
    run_upgrade(name)


def filter_services(config: dict, service_name: str | None) -> list[Any]:
    """Filter services from the configuration based on the service name.

    Args:
        config (dict): Configuration dictionary.
        service_name (str | None): Name of the service to filter by.

    Returns:
        list[Any]: List of filtered services.

    """
    services = config.get("services", [])
    if service_name is not None:
        services = [s for s in services if s.get("name") == service_name]
    return services


def prepare_environment() -> None:
    """Prepare the environment by stopping all containers and starting RabbitMQ."""
    stop_all_containers()
    start_service("rabbitmq")  # start rabbitmq because it takes a while to be ready

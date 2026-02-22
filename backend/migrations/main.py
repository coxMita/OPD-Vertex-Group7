import argparse
from pathlib import Path

from src.args_validator import validate_args
from src.config_parser import parse_config_file
from src.docker import stop_all_containers
from src.helper import (
    CommandLineArgs,
    RevisionConfig,
    filter_services,
    run_downgrade_steps,
    run_revision_steps,
    run_upgrade_steps, prepare_environment,
)


def run_migrations(config: dict, cl_args: CommandLineArgs) -> None:
    """Run migrations for the specified service or all services if none is specified.

    Args:
        config (dict): Configuration dictionary.
        cl_args (CommandLineArgs): Command line arguments.

    """  # noqa: E501
    services = filter_services(config, cl_args.service_name)
    error = validate_args(services, cl_args)
    if error:
        print(error)
        return

    prepare_environment()
    match cl_args.operation:
        case "downgrade":
            run_downgrade_steps(cl_args.service_name, cl_args.steps)
            print(f"*** Downgrade completed for service: {cl_args.service_name} ***")
        case "revision":
            config = RevisionConfig(
                message=cl_args.message,
                prune=cl_args.prune,
                service_name=cl_args.service_name,
                services=services,
                commit_changes=cl_args.commit_changes,
            )
            run_revision_steps(config)
            print(
                f"*** Revision created "
                f"{'and committed ' if cl_args.commit_changes else ''}"
                f"for service: {cl_args.service_name} ***"
            )
        case "upgrade":
            for service in services:
                run_upgrade_steps(cl_args.prune, service)
            print("*** All migrations completed ***")

    stop_all_containers()


def main() -> None:
    """Execute main function to parse arguments and run migrations."""
    parser = argparse.ArgumentParser(
        description="A simple tool automate migrations with alembic for multiple databases."  # noqa: E501
    )
    parser.add_argument(
        "operation",
        choices=["revision", "upgrade", "downgrade"],
        help="Operation to perform.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        help="Number of steps to downgrade (only for downgrade operation).",
    )
    parser.add_argument(
        "-m", "--message", type=str, help="Message for the new revision."
    )
    parser.add_argument(
        "--service",
        type=str,
        help="Specify a particular service to run migrations for.",
    )
    parser.add_argument(
        "--prune-volumes",
        action="store_true",
        help="Prune Docker volumes before running migrations.",
    )

    parser.add_argument(
        "--commit",
        action="store_true",
        help="Commit changes to the Git repository after creating a revision.",
    )

    args = parser.parse_args()
    config = parse_config_file(Path("config/services.json"))
    command_line_args = CommandLineArgs(
        operation=args.operation,
        steps=args.steps,
        message=args.message,
        service_name=args.service,
        prune=args.prune_volumes,
        commit_changes=args.commit,
    )
    run_migrations(
        config,
        command_line_args,
    )


if __name__ == "__main__":
    main()

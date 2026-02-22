from src.helper import CommandLineArgs


def validate_args(services: list, cl_args: CommandLineArgs) -> str | None:
    """Return an error message if arguments are invalid, otherwise None.

    Args:
        services (list): List of services to validate against.
        cl_args (CommandLineArgs): Command line arguments.

    Returns:
        str | None: Error message if invalid, otherwise None.

    """
    if not services:
        return f"No services found for the specified name: {cl_args.service_name}"

    if cl_args.operation == "downgrade":
        downgrade_error = _validate_downgrade_config(services, cl_args)
        if downgrade_error:
            return downgrade_error

    if cl_args.operation == "revision":
        revision_error = _validate_revision_config(services, cl_args)
        if revision_error:
            return revision_error

    return None


def _validate_downgrade_config(services: list, cl_args: CommandLineArgs) -> str | None:
    """Validate downgrade operation arguments.

    Args:
        services (list): List of services to validate against.
        cl_args (CommandLineArgs): Command line arguments.

    Returns:
        str | None: Error message if invalid, otherwise None.

    """
    if cl_args.steps is None:
        return "Number of steps is required for downgrade operation."
    if cl_args.steps > 0:
        return "Number of steps for downgrade must be a negative integer."
    if len(services) > 1:
        return (
            "Downgrade operation can only be performed on a single service at a time."
        )
    return None


def _validate_revision_config(services: list, cl_args: CommandLineArgs) -> str | None:
    """Validate revision configuration arguments.

    Args:
        services (list): List of services to validate against.
        cl_args (CommandLineArgs): Command line arguments.

    Returns:
        str | None: Error message if invalid, otherwise None.

    """
    if len(services) > 1:
        return "Revision operation can only be performed on a single service at a time."
    if cl_args.message is None:
        return "Message is required for creating a new revision."
    return None

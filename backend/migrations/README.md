# Migrations Tool

This tool automates database migrations for multiple services using Alembic. It provides commands to create revisions, upgrade databases, and perform downgrades in a controlled way.

Before running any migrations, ensure that the Docker images for all services are rebuilt so that the containers reflect the latest code changes.

## Prerequisites

* Docker images for all involved services built with the latest project changes

## Usage

The tool exposes three main operations:

* `revision`: Create a new Alembic migration revision for a specific service.
* `upgrade`: Apply all pending migrations for one or more services.
* `downgrade`: Revert migrations for a specific service by a given number of steps.

General structure:

```
uv run main.py <operation> [options]
```

## Commands

### Create a new migration revision

Revisions can only be created for a single service, and a message describing the revision is required.

```
uv run main.py revision --service SERVICE_NAME -m "Message"
```

Optional: automatically commit the created revision file.

```
uv run main.py revision --service SERVICE_NAME -m "Message" --commit
```

### Upgrade migrations

Upgrades run for all services unless a specific service is provided.

Upgrade all services:

```
uv run main.py upgrade
```

Upgrade a specific service:

```
uv run main.py upgrade --service SERVICE_NAME
```

Optionally prune Docker volumes before running:

```
uv run main.py upgrade --prune-volumes
```

### Downgrade migrations

Downgrades can only be performed on a single service and require a negative step count (for example, `-1`, `-2`, etc.).

```
uv run main.py downgrade --service SERVICE_NAME --steps -1
```

## Configuration

Services are defined in:

```
config/services.json
```

Each service entry is used to determine how migrations should be executed.

## Help

To view help information for the tool and its commands, run:

```
uv run main.py --help
```

## Notes

Always rebuild Docker images before running the tool to ensure that migrations are executed using the most recent version of each service.

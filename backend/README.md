# OPD-Vertex — Development Setup Guide

## Prerequisites

Make sure you have the following installed before starting:

- [Docker](https://www.docker.com/get-started) & Docker Compose
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Git](https://git-scm.com/)
- Python 3.13

---

## 1. Clone the Repository

```bash
git clone https://github.com/coxMita/OPD-Vertex-Group7.git
cd OPD-Vertex-Group7
```

---

## 2. Install uv

```bash
pip install uv
```

Then verify it works:

```bash
uv --version
```

If you get `command not found`, add it to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
# Add the above line to ~/.bashrc or ~/.zshrc to make it permanent
```

Install Python 3.13 via uv:

```bash
uv python install 3.13
```

---

## 3. Set Up Environment Variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

The `.env` file contains credentials for all databases, RabbitMQ, and JWT. The defaults from `.env.example` work out of the box for local development — you do not need to change anything to get started.

---

## 4. Install Dependencies for Each Service

Run this from the repo root to generate `uv.lock` files for all services (linux):

```bash
for svc in ai-service email-service gateway transcription-service appointment-service consultation-service prescription-service user-service; do
    echo "Syncing $svc..."
    (cd backend/$svc && uv sync)
done
```
For windows
```bash
$services = @("ai-service","email-service","gateway","transcription-service","appointment-service","consultation-service","prescription-service","user-service")
foreach ($svc in $services) {
    Write-Host "Syncing $svc..."
    Set-Location backend/$svc; uv sync; Set-Location ../..
}
```
---

## 5. Start All Containers

```bash
docker compose up -d --build
```

This will start all 14 containers:

| Container | Description | Port |
|---|---|---|
| `gateway` | API Gateway | 8080 |
| `ai-service` | AI transcription & note generation | 8081 |
| `appointment-service` | Appointment booking | 8082 |
| `consultation-service` | Consultation management | 8083 |
| `email-service` | Email notifications | 8084 |
| `prescription-service` | Prescription management | 8085 |
| `transcription-service` | Real-time transcription | 8086 |
| `user-service` | User management & auth | 8087 |
| `rabbitmq` | Message broker | 5672 (AMQP) / 9000 (UI) |
| `appointment-db` | PostgreSQL | 5432 |
| `consultation-db` | PostgreSQL | 5433 |
| `prescription-db` | PostgreSQL | 5434 |
| `user-db` | PostgreSQL | 5435 |
| `pgadmin` | Database UI | 5050 |

---

## 6. Verify Everything is Running

```bash
docker compose ps
```

All containers should show `healthy` or `running`. You can also check individual service health:

```bash
curl http://localhost:8080/health   # gateway
curl http://localhost:8082/health   # appointment-service
```

---

## 7. pgAdmin — Database UI

Open [http://localhost:5050](http://localhost:5050) in your browser.

**Login credentials:**
- Email: `admin@admin.com`
- Password: `admin123`

### Adding Database Servers

Right-click **Servers → Register → Server** for each database below.  
Fill in the **General** tab (Name) and **Connection** tab (everything else).

> ⚠️ Use the container name as the host (not `localhost`) — pgAdmin connects over Docker's internal network.

---

**appointment-db**

| Field | Value |
|---|---|
| Name | `appointment-db` |
| Host | `appointment-db` |
| Port | `5432` |
| Database | `appointment_db` |
| Username | `appointment_user` |
| Password | `appointment_pass` |

---

**consultation-db**

| Field | Value |
|---|---|
| Name | `consultation-db` |
| Host | `consultation-db` |
| Port | `5432` |
| Database | `consultation_db` |
| Username | `consultation_user` |
| Password | `consultation_pass` |

---

**prescription-db**

| Field | Value |
|---|---|
| Name | `prescription-db` |
| Host | `prescription-db` |
| Port | `5432` |
| Database | `prescription_db` |
| Username | `prescription_user` |
| Password | `prescription_pass` |

---

**user-db**

| Field | Value |
|---|---|
| Name | `user-db` |
| Host | `user-db` |
| Port | `5432` |
| Database | `user_db` |
| Username | `user_user` |
| Password | `user_pass` |

---

## 8. RabbitMQ Management UI

Open [http://localhost:9000](http://localhost:9000) in your browser.

- Username: `guest`
- Password: `guest`

---

## Daily Development Commands

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# Rebuild and restart a single service after code changes
docker compose up -d --build appointment-service

# View logs for a service
docker compose logs -f appointment-service

# View logs for all services
docker compose logs -f

# Restart a single service
docker compose restart appointment-service

# Stop everything and wipe all database data (careful!)
docker compose down -v
```

---

## Running a Service Locally (without Docker)

Useful when actively developing a service and want faster feedback.

```bash
# Start only the dependencies the service needs
docker compose up -d rabbitmq appointment-db

# Then run the service locally
cd backend/appointment-service
uv run fastapi dev
```

The service will be available at [http://localhost:8000](http://localhost:8000).

---

## Code Quality

Each service uses [Ruff](https://docs.astral.sh/ruff/) for formatting and linting.

```bash
cd backend/appointment-service

# Format code
uv run ruff format

# Lint and auto-fix
uv run ruff check --fix
```

### Install Pre-commit Hooks

Run this once per service to automatically format/lint on every commit:

```bash
cd backend/appointment-service
uv run pre-commit install
```

---

## Database Migrations (Alembic)

For services that have a database (`appointment`, `consultation`, `prescription`, `user`).

### Initialize Alembic (first time only)

```bash
cd backend/appointment-service
uv run alembic init migrations
```

### Create a New Migration

```bash
# Start the service container first
docker compose up -d appointment-service appointment-db rabbitmq

# Connect to the running container
docker exec -it appointment-service bash

# Inside the container:
uv run alembic revision --autogenerate -m "your migration message"
uv run alembic upgrade head
exit

# Copy the generated migration file back to your local machine
docker cp appointment-service:/app/migrations ./
```

### Apply Migrations

```bash
# Inside the container
uv run alembic upgrade head

# Check current revision
uv run alembic current

# Rollback one step
uv run alembic downgrade -1
```

---

## Project Structure

```
OPD-Vertex-Group7/
├── backend/
│   ├── ai-service/
│   ├── appointment-service/
│   ├── consultation-service/
│   ├── email-service/
│   ├── gateway/
│   ├── prescription-service/
│   ├── transcription-service/
│   └── user-service/
├── docker-compose.yml
├── .env.example          ← copy this to .env
└── README.md
```

Each service follows the same structure:

```
<service>/
├── src/                  ← all source code goes here
├── tests/                ← pytest tests
├── main.py               ← FastAPI entry point
├── pyproject.toml        ← dependencies & tooling config
├── uv.lock               ← pinned dependency versions
├── Dockerfile
├── .env.example
├── .python-version
└── .pre-commit-config.yaml
```

---

## Troubleshooting

**Docker permission denied:**
```bash
sudo usermod -aG docker $USER
# Then log out and log back in
```

**uv command not found:**
```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Python 3.13 not found:**
```bash
uv python install 3.13
```

**Container fails to start — check logs:**
```bash
docker compose logs appointment-service
```

**Database connection refused:**  
Make sure the DB container is healthy before the service starts. The `docker-compose.yml` handles this with `depends_on` health checks automatically.
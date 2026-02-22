#!/usr/bin/env bash
# =============================================================================
#  OPD-Vertex Microservices – uv Project Setup Script
#
#  Run from the ROOT of your OPD-VERTEX-GROUP7 repository:
#    chmod +x setup_opd_vertex.sh
#    ./setup_opd_vertex.sh
#
#  What it does (per service):
#    • Creates pyproject.toml with correct deps + ruff + pytest config
#    • Runs `uv sync` to generate uv.lock
#    • Creates .python-version, .gitignore, .pre-commit-config.yaml
#    • Scaffolds src/, tests/, main.py
#
#  Root level:
#    • .env.example
#    • .gitignore
#    • .github/workflows/ci-<service>.yml for each service
# =============================================================================

set -e

PYTHON_VERSION="3.13"
BACKEND_DIR="backend"

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[ OK ]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERR ]${NC}  $*"; exit 1; }

# ── Checks ───────────────────────────────────────────────────────────────────
command -v uv >/dev/null 2>&1 || error "uv not found. Install: https://docs.astral.sh/uv/"
info "uv $(uv --version 2>&1)"
echo ""

# =============================================================================
# write_pyproject  <dir>  <name>  <deps…>
#   Writes a complete pyproject.toml (deps + ruff + pytest sections)
# =============================================================================
write_pyproject() {
    local dir="$1"; local name="$2"; shift 2
    local deps_block=""
    for dep in "$@"; do
        deps_block+="    \"${dep}\",\n"
    done

    cat > "$dir/pyproject.toml" << PYPROJECT
[project]
name = "$name"
version = "0.1.0"
description = "OPD-Vertex – $name"
readme = "README.md"
requires-python = ">=$PYTHON_VERSION"
dependencies = [
$(printf "$deps_block")]

[dependency-groups]
dev = [
    "pre-commit>=4.3",
    "pytest>=8.4",
    "pytest-asyncio>=1.2",
    "pytest-cov>=7.0",
    "ruff>=0.14",
]

# ── Ruff ──────────────────────────────────────────────────────────────────────
[tool.ruff]
line-length   = 88
indent-width  = 4
target-version = "py313"
exclude = [
    ".venv", "__pycache__", "migrations",
    "build", "dist", ".git", ".pytest_cache",
]

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "F",     # pyflakes
    "W",     # pycodestyle warnings
    "I",     # isort
    "N",     # naming
    "D",     # pydocstyle
    "B",     # bugbear
    "S",     # bandit security
    "ANN",   # annotations
    "ASYNC", # async issues
    "SIM",   # simplify
    "PL",    # pylint
    "C4",    # comprehensions
    "COM",   # commas
]
ignore = [
    "D100", "D104", "D107",   # missing module/package/__init__ docstrings
    "D203", "D213",           # conflicting docstring styles
    "COM812",                 # trailing comma (conflicts with formatter)
    "B008",                   # function calls in defaults (FastAPI Depends)
    "S101",                   # assert in tests
    "ANN101", "ANN102",       # self/cls annotations
]
fixable = ["ALL"]

[tool.ruff.format]
quote-style    = "double"
indent-style   = "space"
line-ending    = "auto"
skip-magic-trailing-comma = false

# ── Pytest ────────────────────────────────────────────────────────────────────
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths    = ["tests"]
PYPROJECT
}

# =============================================================================
# init_service  <subdir>  <name>  <deps…>
# =============================================================================
init_service() {
    local subdir="$1"; local name="$2"; shift 2
    local path="$BACKEND_DIR/$subdir"

    info "── $name  ($path)"
    mkdir -p "$path"

    # ── pyproject.toml ────────────────────────────────────────────────────────
    if [ -f "$path/pyproject.toml" ]; then
        warn "  pyproject.toml already exists – skipping"
    else
        write_pyproject "$path" "$name" "$@"
        success "  pyproject.toml written"
    fi

    # ── uv.lock (uv sync) ─────────────────────────────────────────────────────
    if [ -f "$path/uv.lock" ]; then
        warn "  uv.lock already exists – skipping sync"
    else
        info "  Running uv sync (this fetches packages)…"
        (cd "$path" && uv sync --quiet 2>&1) && success "  uv.lock generated" \
            || warn "  uv sync failed (network issue?) – uv.lock not created"
    fi

    # ── .python-version ───────────────────────────────────────────────────────
    echo "$PYTHON_VERSION" > "$path/.python-version"

    # ── .gitignore ────────────────────────────────────────────────────────────
    cat > "$path/.gitignore" << 'GITIGNORE'
# Python
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
.venv

# IDE
.idea
.vscode

# Env
.env
GITIGNORE

    # ── .pre-commit-config.yaml ───────────────────────────────────────────────
    cat > "$path/.pre-commit-config.yaml" << 'PRECOMMIT'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.1
    hooks:
      - id: ruff-format
      - id: ruff-check
        args: [--fix]
PRECOMMIT

    # ── src/ scaffold ─────────────────────────────────────────────────────────
    mkdir -p "$path/src"
    [ -f "$path/src/__init__.py" ] || touch "$path/src/__init__.py"

    # ── tests/ scaffold ───────────────────────────────────────────────────────
    mkdir -p "$path/tests"
    [ -f "$path/tests/__init__.py" ] || touch "$path/tests/__init__.py"
    if [ ! -f "$path/tests/conftest.py" ]; then
        cat > "$path/tests/conftest.py" << 'CONFTEST'
"""Pytest configuration and shared fixtures."""
import pytest
CONFTEST
    fi

    # ── .env.example (per service) ────────────────────────────────────────────
    [ -f "$path/.env.example" ] || touch "$path/.env.example"

    # ── main.py scaffold ──────────────────────────────────────────────────────
    if [ ! -f "$path/main.py" ]; then
        cat > "$path/main.py" << MAINPY
"""Entry point for $name."""

from fastapi import FastAPI

app = FastAPI(title="$name")


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"service": "$name"}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
MAINPY
    fi

    success "  $name scaffold complete"
    echo ""
}

# =============================================================================
#  Services  –  name & dependency lists
#  (faster-whisper is CPU-friendly; add [cuda12] / [cuda11] suffix for GPU)
# =============================================================================

init_service "ai-service" "ai-service" \
    "fastapi[standard]>=0.120" \
    "faster-whisper>=1.0" \
    "aio-pika>=9.5" \
    "python-dotenv>=1.1" \
    "pydantic>=2.0" \
    "httpx>=0.28"

init_service "appointment-service" "appointment-service" \
    "fastapi[standard]>=0.120" \
    "sqlmodel>=0.0.27" \
    "psycopg2-binary>=2.9" \
    "alembic>=1.17" \
    "aio-pika>=9.5" \
    "python-dotenv>=1.1"

init_service "consultation-service" "consultation-service" \
    "fastapi[standard]>=0.120" \
    "sqlmodel>=0.0.27" \
    "psycopg2-binary>=2.9" \
    "alembic>=1.17" \
    "aio-pika>=9.5" \
    "python-dotenv>=1.1"

init_service "email-service" "email-service" \
    "fastapi[standard]>=0.120" \
    "aio-pika>=9.5" \
    "aiosmtplib>=3.0" \
    "python-dotenv>=1.1" \
    "pydantic>=2.0"

init_service "gateway" "gateway" \
    "fastapi[standard]>=0.120" \
    "httpx>=0.28" \
    "python-dotenv>=1.1" \
    "python-jose[cryptography]>=3.5"

init_service "prescription-service" "prescription-service" \
    "fastapi[standard]>=0.120" \
    "sqlmodel>=0.0.27" \
    "psycopg2-binary>=2.9" \
    "alembic>=1.17" \
    "aio-pika>=9.5" \
    "python-dotenv>=1.1"

init_service "transcription-service" "transcription-service" \
    "fastapi[standard]>=0.120" \
    "faster-whisper>=1.0" \
    "aio-pika>=9.5" \
    "python-dotenv>=1.1" \
    "websockets>=13.0"

init_service "user-service" "user-service" \
    "fastapi[standard]>=0.120" \
    "sqlmodel>=0.0.27" \
    "psycopg2-binary>=2.9" \
    "alembic>=1.17" \
    "aio-pika>=9.5" \
    "python-dotenv>=1.1" \
    "passlib[bcrypt]>=1.7"

# =============================================================================
#  Root-level files
# =============================================================================
info "Creating root-level files…"

# .env.example
cat > .env.example << 'ENVEXAMPLE'
# ── Databases ─────────────────────────────────────────────────────────────────
APPOINTMENT_DB_USER=appointment_user
APPOINTMENT_DB_PASS=appointment_pass
APPOINTMENT_DB_NAME=appointment_db

CONSULTATION_DB_USER=consultation_user
CONSULTATION_DB_PASS=consultation_pass
CONSULTATION_DB_NAME=consultation_db

PRESCRIPTION_DB_USER=prescription_user
PRESCRIPTION_DB_PASS=prescription_pass
PRESCRIPTION_DB_NAME=prescription_db

USER_DB_USER=user_user
USER_DB_PASS=user_pass
USER_DB_NAME=user_db

PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin123

# ── RabbitMQ ──────────────────────────────────────────────────────────────────
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest

# ── JWT ───────────────────────────────────────────────────────────────────────
JWT_SECRET=change_me_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# ── AI / ML ───────────────────────────────────────────────────────────────────
# Whisper model size: tiny | base | small | medium | large-v3
WHISPER_MODEL_SIZE=base
# Path to local GGUF model file for LLM inference
LLM_MODEL_PATH=/models/llama
ENVEXAMPLE

# Root .gitignore
cat > .gitignore << 'ROOTGIT'
.env
*.pid
__pycache__/
*.py[oc]
.venv/
ROOTGIT

# codecov.yml
cat > codecov.yml << 'CODECOV'
codecov:
  branch: main
  max_report_age: off
CODECOV

success "Root files created"

# =============================================================================
#  GitHub Actions CI workflows
# =============================================================================
info "Creating GitHub Actions CI workflows…"
mkdir -p .github/workflows

make_ci() {
    local svc="$1"; local extra="${2:-}"
    cat > ".github/workflows/ci-${svc}.yml" << YAML
name: CI ${svc}

on:
  push:
    branches: [main]
    paths: ["backend/${svc}/**"]
  pull_request:
    branches: [main]
    paths: ["backend/${svc}/**"]
  workflow_dispatch:

jobs:
  ci:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend/${svc}
    env:
      DATABASE_URL: postgresql://dummy:dummy@localhost:5432/dummy_db
      AMQP_URL: amqp://dummy:dummy@localhost:5672/
${extra}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Ruff format check
        run: uv run ruff format --check

      - name: Ruff lint
        run: uv run ruff check

      - name: Run pytest
        run: uv run pytest --cov=src --cov-report=xml

      - name: Upload coverage
        if: hashFiles('coverage.xml') != ''
        uses: codecov/codecov-action@v5
        with:
          token: \${{ secrets.CODECOV_TOKEN }}
          flags: ${svc}
          fail_ci_if_error: false
YAML
}

make_ci "ai-service"             "      WHISPER_MODEL_SIZE: tiny"
make_ci "appointment-service"    ""
make_ci "consultation-service"   ""
make_ci "email-service"          ""
make_ci "gateway"                "      JWT_SECRET: ci_testing_secret"
make_ci "prescription-service"   ""
make_ci "transcription-service"  "      WHISPER_MODEL_SIZE: tiny"
make_ci "user-service"           ""

success "CI workflows created"

# =============================================================================
#  Summary
# =============================================================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          OPD-Vertex setup complete! 🏥                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Each service in backend/ now has:"
echo "    ✓  pyproject.toml   (uv, ruff, pytest all configured)"
echo "    ✓  uv.lock          (reproducible installs)"
echo "    ✓  .python-version  ($PYTHON_VERSION)"
echo "    ✓  .gitignore"
echo "    ✓  .pre-commit-config.yaml  (ruff)"
echo "    ✓  src/__init__.py  +  tests/  scaffold"
echo "    ✓  main.py          (FastAPI skeleton)"
echo "    ✓  .env.example"
echo ""
echo "  Root:"
echo "    ✓  .env.example"
echo "    ✓  .gitignore"
echo "    ✓  codecov.yml"
echo "    ✓  .github/workflows/ci-<service>.yml  (×8)"
echo ""
echo -e "  ${CYAN}Next steps:${NC}"
echo -e "    1.  cp .env.example .env   # fill in real values"
echo -e "    2.  For each DB-backed service:"
echo -e "        cd backend/<service>"
echo -e "        uv run alembic init migrations"
echo -e "    3.  cd backend/<service> && uv run pre-commit install"
echo -e "    4.  Build docker-compose.yml and start:"
echo -e "        docker compose up -d"
echo ""

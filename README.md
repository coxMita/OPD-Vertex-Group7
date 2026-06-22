# OPD-Vertex-Group7
OPD Vertex project repository of Group 7

---

## CI Pipeline

This project uses GitHub Actions for continuous integration (CI). The CI pipelines are defined in the `.github/workflows/ci-*.yml` files.
It includes steps for building the application, running tests, and checking code quality.

| Service | CI |
|---|---|
| Gateway | [![CI Gateway](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-gateway.yml/badge.svg)](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-gateway.yml) |
| AI Service | [![CI AI Service](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-ai-service.yml/badge.svg)](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-ai-service.yml) |
| Appointment Service | [![CI Appointment Service](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-appointment-service.yml/badge.svg)](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-appointment-service.yml) |
| Consultation Service | [![CI Consultation Service](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-consultation-service.yml/badge.svg)](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-consultation-service.yml) |
| Email Service | [![CI Email Service](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-email-service.yml/badge.svg)](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-email-service.yml) |
| Prescription Service | [![CI Prescription Service](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-prescription-service.yml/badge.svg)](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-prescription-service.yml) |
| Transcription Service | [![CI Transcription Service](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-transcription-service.yml/badge.svg)](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-transcription-service.yml) |
| User Service | [![CI User Service](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-user-service.yml/badge.svg)](https://github.com/coxMita/OPD-Vertex-Group7/actions/workflows/ci-user-service.yml) |

## Code Coverage

This project uses Codecov to track code coverage. After running tests, coverage reports are generated and
uploaded to Codecov for analysis. The code coverage only includes all microservices and not the frontend. The overall code coverage can be seen below:

[![codecov](https://codecov.io/github/coxMita/OPD-Vertex-Group7/graph/badge.svg)](https://codecov.io/github/coxMita/OPD-Vertex-Group7)

## Monitoring

The Docker Compose stack includes Prometheus and Grafana for observability dashboards.

Start the stack:

```bash
docker compose up --build
```

Open the monitoring tools:

| Tool | URL | Credentials |
|---|---|---|
| Grafana | http://localhost:3000 | `admin` / `admin` |
| Prometheus | http://localhost:9090 | n/a |

Grafana is provisioned automatically with the `OPD Vertex Observability Overview` dashboard. It uses Prometheus metrics from:

- FastAPI services via `/metrics`
- RabbitMQ via its built-in Prometheus plugin
- Postgres databases via dedicated `postgres-exporter` containers
- Prometheus target health via `up`

Useful dashboard panels for the report include service availability, API request rate, p95 API latency, 5xx errors, database connections, and RabbitMQ queue depth.


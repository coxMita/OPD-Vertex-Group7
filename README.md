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

  ## Running it locally

  ### 1. Configure environment

  ```bash
  # Root env: then fill in LLM_API_KEY and WHISPER_API_KEY (UCloud tokens)
  cp .env.example .env

  # Per-service envs (the defaults work as-is for Docker)
  for d in backend/*/; do [ -f "$d.env.example" ] && cp "$d.env.example" "$d.env"; done
  ```

  ### 2. Start the backend

  ```bash
  docker compose up -d --build
  ```

  Migrations run and the doctors are seeded automatically when the services start.

  ### 3. Start the frontend

  ```bash
  cd frontend/OPD-Vertex
  npm install
  npm run dev
  ```

  ## Pages

  | Page | URL | Login |
  |---|---|---|
  | Patient booking | http://localhost:5173/patient | – |
  | Doctor calendar & consultations | http://localhost:5173/doctor | Doctor account |
  | Demo control panel (book, start AM/PM sessions, wipe data) | http://localhost:5173/admin | Doctor account |

  ## Doctor accounts (Keycloak)

  You can log in with either the username or the email.

  | Username | Email | Doctor | Department | Password |
  |---|---|---|---|---|
  | `a.hansen` | a.hansen@opd-vertex.dk | Anders Hansen | General Practice | `admin123` |
  | `m.nielsen` | m.nielsen@opd-vertex.dk | Maria Nielsen | Cardiology | `admin123` |
  | `l.christensen` | l.christensen@opd-vertex.dk | Lars Christensen | Neurology | `admin123` |
  | `s.pedersen` | s.pedersen@opd-vertex.dk | Sofie Pedersen | Orthopedics | `admin123` |
  | `m.andersen` | m.andersen@opd-vertex.dk | Mikkel Andersen | Dermatology | `admin123` |






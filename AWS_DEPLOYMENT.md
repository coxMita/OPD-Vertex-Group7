# AWS Deployment Plan

How to get OPD-Vertex running on AWS at minimum cost, with the LLM on a GPU
instance that is normally stopped and only starts when a request needs it.

Written against the state of the repo on branch `aws-deployment`.

## Recommended setup (lowest cost)

```
Users ─► CloudFront + S3 ............ Vue app (static files)
      └► EC2 "core" (t3.large, always on)
           Caddy (HTTPS) → gateway, keycloak
           7 FastAPI services, RabbitMQ, 1 Postgres with pgvector (several DBs in it)
           Ollama on CPU, only for nomic-embed-text
                │  wakes it through the AWS API
                ▼
         EC2 "gpu" (g4dn.xlarge, normally STOPPED)
           Ollama + llama3.2:3b, stored on its disk so it survives stops
           Shuts itself down after about 10 minutes idle
```

Rough monthly cost in us-east-1:

| Item | Cost |
| --- | --- |
| Core `t3.large` (always on) | ~$60/mo (`t3.medium` with swap ~$30, but tight because of Keycloak) |
| GPU `g4dn.xlarge` disk while stopped | ~$3–4/mo for 40 GB |
| GPU compute | ~$0.53 per hour actually running |
| S3, CloudFront, Route 53, public IP | ~$5/mo |

## Changes needed

### 1. Frontend (`frontend/OPD-Vertex`)

1. **`src/services/keycloak.ts`**: the URL `http://localhost:8089` is hard-coded.
   Read it from env vars instead: `VITE_KEYCLOAK_URL`, `VITE_KEYCLOAK_REALM`,
   `VITE_KEYCLOAK_CLIENT_ID`.
2. **Two names for one URL**: `apiClient.ts` and `emailApi.ts` use
   `VITE_API_BASE_URL`, but `transcriptionApi.ts` uses `VITE_GATEWAY_URL`. Pick
   one, and remove the `localhost` fallbacks from production builds.
3. Add a `.env.production` with values like `https://api.<domain>` and
   `https://auth.<domain>`.
4. **`vite.config.ts`**: load `vueDevTools()` only in dev mode.
5. Replace the "is Docker running?" error text in `transcriptionApi.ts` with a
   message that makes sense in production.
6. Deploy with `npm run build`, upload to S3 (kept private, served through
   CloudFront), and make CloudFront return `index.html` on 403/404 so Vue router
   history mode works.

### 2. Keycloak

1. `command: start-dev` → `start --import-realm`, with
   `KC_HOSTNAME=auth.<domain>`, `KC_PROXY_HEADERS=xforwarded` and
   `KC_HTTP_ENABLED=true` (HTTPS ends at Caddy).
2. **`keycloak/realm-export.json`**: add the production frontend URL to the
   `vue-app` client's `redirectUris` and `webOrigins`.
3. Move `admin/admin123` and `keycloak_user/keycloak_pass` out of
   `docker-compose.yml` into secrets.
4. Set `KEYCLOAK_EXTERNAL_URL` to `https://auth.<domain>` in the gateway and
   user-service.

### 3. All backend Dockerfiles

1. `CMD ["uv","run","fastapi","dev",...]` → `fastapi run`. Dev mode auto-reloads
   and is slower.
2. `uv sync` → `uv sync --frozen --no-dev`.
3. **The gateway Dockerfile runs `COPY ... .env`**, and `setup.sh` notes other
   services do too. That bakes secrets into images, and they're pushed publicly
   to `mita28/opdvertex`. Remove it and pass config through environment
   variables only.
4. Make the gateway's CORS allowed origins configurable, set to the CloudFront or
   frontend domain.

### 4. New `docker-compose.prod.yml` for the core instance

1. Remove `pgadmin` and `mailpit`. Use an SSH tunnel for database admin.
2. Merge the 6 Postgres containers into **one** `pgvector/pgvector:pg17`
   container with an init script that creates each database and user. This saves
   about 1 GB of RAM.
3. Remove all published host ports except Caddy's 80/443. The databases
   (5432–5437), RabbitMQ (5672/9000) and the services (8081–8087) must not be
   reachable from the internet.
4. Add Caddy (or nginx with certbot) to route `api.<domain>` → `gateway:8000` and
   `auth.<domain>` → `keycloak:8080` with automatic TLS.
5. Add a CPU-only `ollama` container that pulls only `nomic-embed-text` (see 5.2).
6. Set memory limits, and make production images pinned tags rather than `build:`.
7. Replace `setup.sh`'s `docker exec ... alembic upgrade head` and `seed.py` with
   a one-time `migrate` service, or an entrypoint that runs migrations before
   start.

### 5. ai-service: GPU on demand (the main code change)

1. **New module, `gpu_manager.py`**: before `generate()`, call
   `ec2.describe_instances`. If the instance is stopped, call `start_instances`,
   wait for `instance_running`, then poll
   `http://<gpu-private-ip>:11434/api/tags` until it responds. Use the instance's
   private IP rather than a fixed URL, since it can change on start unless you
   attach a fixed network interface. Use a lock so simultaneous requests don't all
   start it. Add `boto3`, plus env vars `GPU_INSTANCE_ID` and `AWS_REGION`.
2. **Split the embedding URL from the LLM URL** in `ollama_client.py`: add an
   `OLLAMA_EMBED_BASE_URL` that points at the CPU Ollama. RAG embeddings run on
   every query, so leaving them on the GPU would wake it for every lookup.
3. **`main.py` lines 32–54** pull the embedding model from `OLLAMA_BASE_URL` at
   startup. With the GPU stopped, this would fail or hang, so point it at the
   embedding URL.
4. **A cold start takes about 1–3 minutes.** Two options:
   - Simple: raise the timeouts in `OLLAMA_TIMEOUT` and the gateway's
     `ai_proxy.py` client, and show a "warming up the AI model…" spinner in the
     frontend.
   - Better: have ai-service return `202` with a job ID and let the frontend poll
     a status endpoint. RabbitMQ is already set up for this.
5. Add a status endpoint such as `GET /ai/status` returning `stopped`, `starting`
   or `ready`, so the UI can show the state.
6. Grant IAM permissions through an **instance role** on the core EC2, allowing
   only `ec2:StartInstances` and `ec2:DescribeInstances` on that one instance.
   Don't use access keys.

### 6. GPU instance (one-time setup, no app code)

1. Use the Deep Learning Base AMI (NVIDIA drivers included) on `g4dn.xlarge` with
   a 40 GB gp3 disk. Set shutdown behavior to **stop**, not terminate.
2. Run Ollama as a systemd service with `OLLAMA_HOST=0.0.0.0` and
   `OLLAMA_KEEP_ALIVE=10m`, and pull `llama3.2:3b` once. It stays on the disk
   after that.
3. **Idle shutdown**: a cron job every 5 minutes. If `ollama ps` shows no loaded
   model on two checks in a row, run `shutdown -h now`.
4. Security group: allow port 11434 **only from the core instance's security
   group**. Give it no public IP if possible.
5. ⚠️ **New AWS accounts have a GPU quota of 0.** Request an increase for
   "Running On-Demand G and VT instances" to at least 4 vCPUs in Service Quotas
   before you start. Approval can take a day or more.

### 7. Transcription service

1. `whisper.py:19` hard-codes `device="cpu"`. Make it configurable with
   `WHISPER_DEVICE` and `WHISPER_COMPUTE_TYPE`. Keep `base` on CPU on the core
   box, which is cheapest. Moving it to the GPU would need the same wake-up logic.

### 8. Email

1. Replace Mailpit with **Amazon SES** SMTP settings in `email-service`. You'll
   need to verify your domain and request removal of the SES sandbox.

### 9. Secrets and security

1. Change every default in `.env.example`: `guest/guest`,
   `JWT_SECRET=change_me_in_production`, `admin123`, and the database passwords.
2. Store secrets in **SSM Parameter Store** (the standard tier is free) and write
   the `.env` on the instance at deploy time.
3. This handles medical data, so turn on EBS encryption and use HTTPS everywhere.
   Check GDPR requirements too, for example which AWS region you choose.

### 10. CI/CD (`.github/workflows`)

1. Extend the `ci-*.yml` workflows: on merge to `main`, build and push images to
   ECR (or keep Docker Hub), then SSH or SSM Run Command on the core instance to
   run `docker compose pull && up -d`.
2. Add `deploy-frontend.yml`: build, `aws s3 sync`, then a CloudFront cache
   invalidation.
3. Log in to AWS from GitHub through **OIDC**, not stored access keys.

### 11. Infrastructure and operations

1. Optional but recommended: Terraform in an `infra/` folder covering the VPC, two
   EC2 instances, security groups, IAM role, S3, CloudFront, Route 53, ACM
   certificate and an Elastic IP.
2. Daily EBS snapshots of the core instance's disk through Data Lifecycle
   Manager, as the database backup.
3. An AWS Budgets alert, for example at $80/month, in case the GPU fails to shut
   down.

## Cheaper alternative to consider

For low traffic, calling a hosted model through **Amazon Bedrock** (pay per token)
removes the GPU instance, the wake-up logic and the cold starts. That would
replace only `generate()` in `ollama_client.py`.

## Suggested order of work

1. Sections 2 and 1 — Keycloak and frontend configuration.
2. Sections 3 and 4 — Dockerfiles and the production compose file.
3. Sections 5 and 6 — the on-demand GPU.
4. The rest.

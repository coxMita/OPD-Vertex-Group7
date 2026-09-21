# GCP Deployment Plan

How to get OPD-Vertex running on Google Cloud at minimum cost, with the LLM on a
GPU VM that is normally stopped and only starts when a request needs it.

Written against the state of the repo on branch `aws-deployment`. It is the
Google Cloud version of the AWS plan: the architecture is the same, only the
cloud services and the wake-up code change.

## Recommended setup (lowest cost)

```
Users ─► Firebase Hosting / Cloudflare Pages ... Vue app (static files)
      └► VM "opd-core" (e2-standard-2, always on)
           Caddy (HTTPS) → gateway, keycloak
           7 FastAPI services, RabbitMQ, 1 Postgres with pgvector (several DBs in it)
           Ollama on CPU, only for nomic-embed-text
                │  wakes it through the Compute Engine API
                ▼
         VM "opd-gpu" (n1-standard-4 + 1× NVIDIA T4, normally STOPPED)
           Ollama + llama3.2:3b, stored on its disk so it survives stops
           Fixed internal IP, no public IP
           Shuts itself down after about 10 minutes idle
```

Monthly cost in us-central1 (on-demand list prices, excluding the $300 new-account credit):

| Item | Cost |
| --- | --- |
| Core `e2-standard-2` (2 vCPU, 8 GB, always on) | ~$48.92/mo (`e2-medium` 4 GB is ~$24.46, but tight because of Keycloak) |
| Core disk, 30 GB balanced SSD | ~$3.00/mo |
| Core static external IP | ~$3.65/mo |
| GPU VM disk while stopped, 40 GB standard | ~$1.60/mo (~$4 as balanced SSD) |
| GPU compute (`n1-standard-4` $0.19 + T4 $0.35) | ~$0.54 per hour actually running |
| Frontend + DNS (Firebase Hosting / Cloudflare) | $0 |
| **Base** | **~$57/mo** |

With 10 GPU hours a month: **~$63/mo** (AWS equivalent: ~$74/mo).
Outbound internet traffic is extra (~$0.12/GB), which is pennies for a demo.

## AWS → Google Cloud mapping

| AWS | Google Cloud | Note |
| --- | --- | --- |
| CloudFront + S3 (Vue) | Firebase Hosting (free tier) or Cloudflare Pages (free) | Cloud Storage + Cloud CDN needs a load balancer (~$18/mo), so avoid it |
| EC2 core `t3.large` | `e2-standard-2` | ~$49/mo vs ~$61/mo |
| EC2 gpu `g4dn.xlarge` | `n1-standard-4` + 1× T4 | ~$0.54/hr |
| Deep Learning Base AMI | Deep Learning VM image (`common-cu*` family) | NVIDIA drivers included |
| Shutdown behavior = stop | Default on GCP | `shutdown -h now` leaves the VM stopped (`TERMINATED`) with its disk kept |
| Private IP changes on start | Reserved static internal IP | The IP stays fixed |
| Security group | VPC firewall rule with network tags | |
| IAM instance role | Service account attached to the core VM | |
| `boto3` | `google-cloud-compute` | |
| G-instance vCPU quota | `NVIDIA_T4_GPUS` (region) + `GPUS_ALL_REGIONS` | |
| Elastic IP | Static external IP | |
| Route 53 | Cloudflare DNS (free) or Cloud DNS ($0.20/zone) | |
| ACM certificate | Caddy automatic TLS | Unchanged |
| Amazon SES | Brevo, Mailgun or SendGrid (free tiers) | GCP blocks outbound port 25 |
| SSM Parameter Store | Secret Manager | |
| ECR | Artifact Registry (0.5 GB free) or Docker Hub | |
| GitHub OIDC | Workload Identity Federation | |
| SSM Run Command | `gcloud compute ssh --tunnel-through-iap` | |
| Data Lifecycle Manager | Snapshot schedule (resource policy) | |
| EBS encryption | Always on by default | Nothing to do |
| AWS Budgets | Cloud Billing budgets | |
| Bedrock | Vertex AI | |

## Changes needed

Sections 1–4, 7 and 9.1 are cloud-agnostic and match the AWS plan. Sections 5,
6, 8, 10 and 11 are adapted for Google Cloud.

### 0. Google Cloud project (one-time)

1. Create a project and link a billing account. **Upgrade the free trial to a
   paid account**, because free-trial accounts can't use GPUs. The $300 credit
   still applies.
2. Enable the APIs:
   ```bash
   gcloud services enable compute.googleapis.com secretmanager.googleapis.com \
     iamcredentials.googleapis.com artifactregistry.googleapis.com
   ```
3. ⚠️ **Request a GPU quota.** Go to IAM & Admin → Quotas and set
   `NVIDIA_T4_GPUS` in `us-central1` to 1 and `GPUS_ALL_REGIONS` to 1. Small
   requests are usually approved within minutes to hours.

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
6. Deploy with `npm run build` to one of these, with a rewrite to `index.html`
   so Vue router history mode works:
   - **Firebase Hosting**, using `firebase.json`:
     ```json
     {
       "hosting": {
         "public": "dist",
         "ignore": ["firebase.json", "**/.*"],
         "rewrites": [{ "source": "**", "destination": "/index.html" }]
       }
     }
     ```
     Then run `firebase deploy --only hosting`.
   - **Cloudflare Pages**: add `public/_redirects` containing
     `/* /index.html 200`.

### 2. Keycloak

1. `command: start-dev` → `start --import-realm`, with
   `KC_HOSTNAME=auth.<domain>`, `KC_PROXY_HEADERS=xforwarded` and
   `KC_HTTP_ENABLED=true` (HTTPS ends at Caddy).
2. **`keycloak/realm-export.json`**: add the production frontend URL to the
   `vue-app` client's `redirectUris` and `webOrigins`.
3. Move `admin/admin123` and `keycloak_user/keycloak_pass` out of
   `docker-compose.yml` into secrets (see section 9).
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
4. Make the gateway's CORS allowed origins configurable, set to the frontend
   domain.

### 4. New `docker-compose.prod.yml` for the core VM

1. Remove `pgadmin` and `mailpit`. Use an SSH tunnel for database admin.
2. Merge the 6 Postgres containers into **one** `pgvector/pgvector:pg17`
   container with an init script that creates each database and user. This saves
   about 1 GB of RAM.
3. Remove all published host ports except Caddy's 80/443. The databases
   (5432–5437), RabbitMQ (5672/9000) and the services (8081–8087) must not be
   reachable from the internet.
4. Add Caddy to route `api.<domain>` → `gateway:8000` and
   `auth.<domain>` → `keycloak:8080` with automatic TLS.
5. Add a CPU-only `ollama` container that pulls only `nomic-embed-text` (see 5.2).
6. Set memory limits, and make production images pinned tags rather than `build:`.
7. Replace `setup.sh`'s `docker exec ... alembic upgrade head` and `seed.py` with
   a one-time `migrate` service, or an entrypoint that runs migrations before
   start.

### 5. ai-service: GPU on demand (the main code change)

1. **New module, `gpu_manager.py`**: before `generate()`, check the GPU VM. If it
   is stopped, start it, then poll `http://<gpu-internal-ip>:11434/api/tags`
   until Ollama responds. The GPU VM has a reserved internal IP, so the URL never
   changes. A lock stops simultaneous requests from all starting it.

   ```python
   # gpu_manager.py
   import asyncio
   import os

   import httpx
   from google.cloud import compute_v1

   PROJECT = os.environ["GCP_PROJECT"]
   ZONE = os.environ["GCP_ZONE"]            # e.g. us-central1-a
   INSTANCE = os.environ["GPU_INSTANCE"]    # e.g. opd-gpu
   GPU_IP = os.environ["GPU_INTERNAL_IP"]   # reserved static internal IP
   OLLAMA_URL = f"http://{GPU_IP}:11434"

   _client = compute_v1.InstancesClient()   # uses the VM's service account, no keys
   _lock = asyncio.Lock()


   def vm_status() -> str:
       """RUNNING, TERMINATED (= stopped), STAGING, PROVISIONING, STOPPING, ..."""
       return _client.get(project=PROJECT, zone=ZONE, instance=INSTANCE).status


   async def ollama_ready() -> bool:
       try:
           async with httpx.AsyncClient() as c:
               r = await c.get(f"{OLLAMA_URL}/api/tags", timeout=3)
               return r.status_code == 200
       except httpx.HTTPError:
           return False


   async def ai_status() -> str:
       """Value for GET /ai/status: stopped | starting | ready."""
       status = await asyncio.to_thread(vm_status)
       if status in ("TERMINATED", "STOPPING", "SUSPENDED"):
           return "stopped"
       if status == "RUNNING" and await ollama_ready():
           return "ready"
       return "starting"


   async def ensure_gpu_ready(timeout: int = 300) -> None:
       async with _lock:
           if await ollama_ready():
               return
           if await asyncio.to_thread(vm_status) == "TERMINATED":
               # Fire the start request; readiness is checked by polling below,
               # so no permission on zone operations is needed.
               await asyncio.to_thread(
                   _client.start, project=PROJECT, zone=ZONE, instance=INSTANCE
               )
           for _ in range(timeout // 5):
               if await ollama_ready():
                   return
               await asyncio.sleep(5)
       raise TimeoutError("GPU VM did not become ready in time")
   ```

   Add `google-cloud-compute` to the dependencies, plus the env vars
   `GCP_PROJECT`, `GCP_ZONE`, `GPU_INSTANCE` and `GPU_INTERNAL_IP`.
2. **Split the embedding URL from the LLM URL** in `ollama_client.py`: add an
   `OLLAMA_EMBED_BASE_URL` that points at the CPU Ollama on the core VM. RAG
   embeddings run on every query, so leaving them on the GPU would wake it for
   every lookup.
3. **`main.py` lines 32–54** pull the embedding model from `OLLAMA_BASE_URL` at
   startup. With the GPU stopped, this would fail or hang, so point it at the
   embedding URL.
4. **A cold start takes about 1–3 minutes** (VM boot plus loading the model).
   Two options:
   - Simple: raise the timeouts in `OLLAMA_TIMEOUT` and the gateway's
     `ai_proxy.py` client, and show a "warming up the AI model…" spinner in the
     frontend.
   - Better: have ai-service return `202` with a job ID and let the frontend poll
     a status endpoint. RabbitMQ is already set up for this.
5. Add `GET /ai/status` returning `stopped`, `starting` or `ready` (from
   `ai_status()` above), so the UI can show the state. If a start fails with
   `ZONE_RESOURCE_POOL_EXHAUSTED` (no T4 free in the zone), return a clear error
   such as "GPU capacity unavailable, try again later".
6. **Permissions through a service account**, not keys. The core VM runs as
   `opd-core@<project>.iam.gserviceaccount.com`, and that account gets a custom
   role with only `compute.instances.get` and `compute.instances.start`,
   granted on the GPU VM alone (see 6.5).

### 6. GPU VM and core VM (one-time setup, no app code)

Replace `<project>` with your project ID. The commands assume the `default`
network in `us-central1-a`.

1. **Reserve a fixed internal IP for the GPU VM:**
   ```bash
   gcloud compute addresses create opd-gpu-ip \
     --region=us-central1 --subnet=default --addresses=10.128.0.50
   ```
2. **Create the GPU VM.** Use the Deep Learning VM image (NVIDIA drivers
   included) and a 40 GB disk. GPU VMs must use
   `--maintenance-policy=TERMINATE`. Stopping on shutdown is already the default.
   ```bash
   gcloud compute instances create opd-gpu \
     --zone=us-central1-a --machine-type=n1-standard-4 \
     --accelerator=type=nvidia-tesla-t4,count=1 \
     --maintenance-policy=TERMINATE \
     --image-family=common-cu124-debian-11 --image-project=deeplearning-platform-release \
     --boot-disk-size=40GB --boot-disk-type=pd-standard \
     --private-network-ip=10.128.0.50 --tags=gpu \
     --metadata=install-nvidia-driver=True
   ```
   If the image family has been renamed, list the current ones with
   `gcloud compute images list --project deeplearning-platform-release | grep common-cu`.
3. **Install Ollama and pull the model once.** It stays on the disk after that.
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   sudo systemctl edit ollama
   #   [Service]
   #   Environment="OLLAMA_HOST=0.0.0.0"
   #   Environment="OLLAMA_KEEP_ALIVE=10m"
   sudo systemctl restart ollama
   ollama pull llama3.2:3b
   ```
4. **Idle shutdown**: a cron job every 5 minutes. If `ollama ps` shows no loaded
   model on two checks in a row, the VM shuts itself down.
   ```bash
   # /usr/local/bin/idle-shutdown.sh  (chmod +x)
   #!/bin/bash
   STATE=/var/tmp/ollama_idle_count
   if [ -z "$(ollama ps | tail -n +2)" ]; then
     n=$(( $(cat "$STATE" 2>/dev/null || echo 0) + 1 ))
     echo "$n" > "$STATE"
     [ "$n" -ge 2 ] && echo 0 > "$STATE" && shutdown -h now
   else
     echo 0 > "$STATE"
   fi
   ```
   Add it to root's crontab with `sudo crontab -e`:
   `*/5 * * * * /usr/local/bin/idle-shutdown.sh`
5. **Service account for the core VM, allowed to start only the GPU VM:**
   ```bash
   gcloud iam service-accounts create opd-core
   gcloud iam roles create gpuStarter --project=<project> \
     --title="GPU starter" \
     --permissions=compute.instances.get,compute.instances.start
   gcloud compute instances add-iam-policy-binding opd-gpu --zone=us-central1-a \
     --member=serviceAccount:opd-core@<project>.iam.gserviceaccount.com \
     --role=projects/<project>/roles/gpuStarter
   ```
6. **Create the core VM** with that service account, a static external IP for
   Caddy, and a 30 GB balanced disk:
   ```bash
   gcloud compute addresses create opd-core-ip --region=us-central1
   gcloud compute instances create opd-core \
     --zone=us-central1-a --machine-type=e2-standard-2 \
     --image-family=debian-12 --image-project=debian-cloud \
     --boot-disk-size=30GB --boot-disk-type=pd-balanced \
     --address=opd-core-ip --tags=core \
     --service-account=opd-core@<project>.iam.gserviceaccount.com \
     --scopes=cloud-platform
   ```
   Point the DNS A records for `api.<domain>` and `auth.<domain>` at
   `opd-core-ip`.
7. **Firewall rules**: open port 11434 on the GPU VM **only to the core VM**,
   open 80/443 on the core VM, and allow SSH only through IAP.
   ```bash
   gcloud compute firewall-rules create allow-ollama-from-core \
     --network=default --allow=tcp:11434 --source-tags=core --target-tags=gpu
   gcloud compute firewall-rules create allow-web-core \
     --network=default --allow=tcp:80,tcp:443 --target-tags=core
   gcloud compute firewall-rules create allow-iap-ssh \
     --network=default --allow=tcp:22 --source-ranges=35.235.240.0/20
   ```
   If the `default` network still has its `default-allow-ssh` rule
   (0.0.0.0/0), delete it.
8. **Remove the GPU VM's public IP** once Docker, Ollama and the model are
   installed. It only needs internet for that first setup.
   ```bash
   gcloud compute instances delete-access-config opd-gpu \
     --zone=us-central1-a --access-config-name="external-nat"
   ```
   To pull a new model later, add the IP back with `add-access-config`, or set
   up Cloud NAT (costs extra).

### 7. Transcription service

1. `whisper.py:19` hard-codes `device="cpu"`. Make it configurable with
   `WHISPER_DEVICE` and `WHISPER_COMPUTE_TYPE`. Keep `base` on CPU on the core
   VM, which is cheapest. Moving it to the GPU would need the same wake-up logic.

### 8. Email

1. Google Cloud has no email-sending service like SES. Replace Mailpit with the
   SMTP settings of **Brevo**, **Mailgun** or **SendGrid** (all have free tiers)
   in `email-service`.
2. **GCP blocks outbound port 25**, so use port 587 (STARTTLS) or 2525.
3. Verify your sending domain with the provider (SPF and DKIM records).

### 9. Secrets and security

1. Change every default in `.env.example`: `guest/guest`,
   `JWT_SECRET=change_me_in_production`, `admin123`, and the database passwords.
2. Store secrets in **Secret Manager**, which is effectively free at this size.
   Grant `opd-core` the `roles/secretmanager.secretAccessor` role and write the
   `.env` on the VM at deploy time:
   ```bash
   printf '%s' 'super-secret' | gcloud secrets create JWT_SECRET --data-file=-
   gcloud secrets versions access latest --secret=JWT_SECRET
   ```
3. Disks are encrypted at rest by default on Google Cloud. Use HTTPS everywhere.
   This handles medical data, so check GDPR requirements. An EU region such as
   `europe-west1` or `europe-west4` (both have T4s) is safer than
   `us-central1`, at a slightly higher price.

### 10. CI/CD (`.github/workflows`)

1. Log in to Google Cloud from GitHub through **Workload Identity Federation**
   (`google-github-actions/auth`), not a stored service-account key.
2. Extend the `ci-*.yml` workflows: on merge to `main`, build and push images to
   **Artifact Registry** (or keep Docker Hub), then update the core VM over IAP:
   ```bash
   gcloud compute ssh opd-core --zone=us-central1-a --tunnel-through-iap \
     --command="cd /opt/opd-vertex && docker compose pull && docker compose up -d"
   ```
3. Add `deploy-frontend.yml`: build, then `firebase deploy --only hosting` (or
   `wrangler pages deploy dist` for Cloudflare Pages). No cache invalidation step
   is needed; both invalidate on deploy.

### 11. Infrastructure and operations

1. Optional but recommended: Terraform (`google` provider) in an `infra/` folder
   covering the two VMs, the reserved IPs, firewall rules, service account,
   custom role and Secret Manager secrets.
2. **Daily snapshots** of the core VM's disk, as the database backup:
   ```bash
   gcloud compute resource-policies create snapshot-schedule opd-daily \
     --region=us-central1 --daily-schedule --start-time=18:00 --max-retention-days=7
   gcloud compute disks add-resource-policies opd-core \
     --zone=us-central1-a --resource-policies=opd-daily
   ```
3. A **Cloud Billing budget**, for example $80/month, with email alerts at 50%
   and 90%, in case the GPU VM fails to shut down:
   ```bash
   gcloud billing budgets create --billing-account=<billing-account-id> \
     --display-name="OPD-Vertex" --budget-amount=80USD \
     --threshold-rule=percent=0.5 --threshold-rule=percent=0.9
   ```

## GCP-specific gotchas

- **The free trial can't use GPUs.** Upgrade to a paid account first; the credit
  stays.
- **GPU VMs must use `--maintenance-policy=TERMINATE`**, because they can't
  live-migrate.
- **T4 capacity can be tight** in a zone. A start can fail with
  `ZONE_RESOURCE_POOL_EXHAUSTED`, so handle it in `/ai/status` (5.5).
- **A stopped VM still bills its disk** (~$1.60/mo for 40 GB standard) and any
  reserved external IP that isn't attached to a running VM.
- **Port 25 is blocked**, so use port 587 or 2525 for SMTP.

## Cheaper alternative to consider

For low traffic, calling a hosted model through **Vertex AI** (Gemini, or Llama
through Model Garden, pay per token) removes the GPU VM, the wake-up logic and
the cold starts. That would replace only `generate()` in `ollama_client.py`.

## Suggested order of work

1. Section 0 — Google Cloud project and GPU quota. Start this first, since the
   quota request can take a while.
2. Sections 2 and 1 — Keycloak and frontend configuration.
3. Sections 3 and 4 — Dockerfiles and the production compose file.
4. Sections 5 and 6 — the on-demand GPU.
5. The rest.

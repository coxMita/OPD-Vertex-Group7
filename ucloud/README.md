# Running the AI models on UCloud (SDU)

Only the **GPU-heavy models** run on UCloud. Everything else (gateway, ai-service,
transcription-service, databases, RabbitMQ, frontend, Keycloak) still runs locally
with `docker compose`.

```
 your laptop (docker compose)                         UCloud (cloud.sdu.dk)
┌────────────────────────────┐   HTTPS + Bearer token   ┌──────────────────────────────────────┐
│ ai-service ────────────────┼─────────────────────────▶│ Job 1 "opd-llm"  (Nginx app, GPU)    │
│                            │                          │  nginx :8080 ─┬─▶ vLLM chat  :8000   │
│                            │                          │               └─▶ vLLM embed :8001   │
│ transcription-service ─────┼─────────────────────────▶│ Job 2 "opd-whisper" (Nginx app, GPU) │
│   (still publishes to      │                          │  nginx :8080 ───▶ faster-whisper :9000│
│    RabbitMQ locally)       │                          └──────────────────────────────────────┘
└────────────────────────────┘
```

Why the **Nginx Web Server** app? UCloud does not let us run our own containers,
but the Nginx app gives a Linux machine with `sudo`, an optional GPU, an
**init script** that runs on start-up, and — the important part — a **public link**
(`https://app-<name>.cloud.sdu.dk`). The model servers listen on `127.0.0.1` only;
nginx is the single door in, and it rejects every request without the right
`Authorization: Bearer <token>` header.

The token is **not** a Hugging Face token. It is a random secret that `init.sh`
generates on the first run (`secrets/api_token`) and that you copy into the
local `.env`. Never commit it.

---

## 1. Upload the files to UCloud (once)

In UCloud → **Files**, inside your project drive, create two folders and upload:

| UCloud folder | Upload these files from this repo |
|---|---|
| `opd-llm` | `ucloud/llm/init.sh`, `ucloud/llm/default.conf.template` |
| `opd-whisper` | `ucloud/whisper/init.sh`, `ucloud/whisper/default.conf.template`, `ucloud/whisper/server.py` |

The folder names matter: they are mounted at `/work/opd-llm` and `/work/opd-whisper`,
which is what the scripts expect (`BASE_DIR`). If you use other names, change
`BASE_DIR` at the top of `init.sh`.

## 2. Start job 1 — the LLM

Apps → **Nginx Web Server** → fill in:

| Field | Value |
|---|---|
| Job name | `opd-llm` |
| Hours | as needed (+8 / +24); the job stops after that |
| Machine type | a GPU type with **≥ 24 GB GPU memory** (e.g. `gpu-nvidia-b200-4-mig.1g` or bigger) |
| Folder #1 | `opd-llm` |
| Public link #1 | create one, e.g. `opd-llm` → `https://app-opd-llm.cloud.sdu.dk` |
| Initialization | `opd-llm/init.sh` |
| NGINX configuration | leave empty (init.sh installs its own) |

Submit. Open the job page and watch the log:

* **First start**: installs vLLM into `/work/opd-llm/.venv` and downloads the
  models into `/work/opd-llm/hf-cache` → 10–20 min.
* **Later starts**: reuse both → a couple of minutes.
* Ready when the log shows `Application startup complete` / `Uvicorn running on http://127.0.0.1:8000`.

What runs:

* Chat: `Qwen/Qwen3-8B-FP8` (8B, FP8 → ~9 GB), served as **`opd-llm`**, 16k context.
* Embeddings: `nomic-ai/nomic-embed-text-v1.5` (768-dim, same as our pgvector
  table), served as **`opd-embed`**.

To change model/size, edit the variables at the top of `init.sh`
(`LLM_MODEL`, `LLM_MAX_LEN`, `LLM_GPU_UTIL`, …).

## 3. Start job 2 — faster-whisper

Same as above with:

| Field | Value |
|---|---|
| Job name | `opd-whisper` |
| Machine type | smallest GPU type is enough (e.g. `gpu-nvidia-b200-4-mig.1g`) |
| Folder #1 | `opd-whisper` |
| Public link #1 | e.g. `opd-whisper` → `https://app-opd-whisper.cloud.sdu.dk` |
| Initialization | `opd-whisper/init.sh` |

Default model is `large-v3` on GPU (float16). Ready when the log shows
`Uvicorn running on http://127.0.0.1:9000`.

## 4. Get the tokens

After the first start, each folder contains `secrets/api_token`
(UCloud → Files → `opd-llm/secrets/api_token`, open it). The token stays the
same for every later start. To rotate it: delete the file and restart the job.

## 5. Test from your laptop

```bash
LLM=https://app-opd-llm.cloud.sdu.dk;    LLM_TOKEN=...      # from opd-llm/secrets/api_token
WSP=https://app-opd-whisper.cloud.sdu.dk; WSP_TOKEN=...     # from opd-whisper/secrets/api_token

# should be 401 (no token)
curl -i $LLM/v1/models

curl -s $LLM/v1/models -H "Authorization: Bearer $LLM_TOKEN"

curl -s $LLM/v1/chat/completions -H "Authorization: Bearer $LLM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"opd-llm","messages":[{"role":"user","content":"Say hi"}],
       "chat_template_kwargs":{"enable_thinking":false}}'

curl -s $LLM/v1/embeddings -H "Authorization: Bearer $LLM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"opd-embed","input":["patient has fever"]}' | head -c 200

curl -s $WSP/v1/audio/transcriptions -H "Authorization: Bearer $WSP_TOKEN" \
  -F file=@some-recording.wav -F language=en -F response_format=verbose_json
```

## 6. Point the local stack at UCloud

In the repo root `.env` (copy from `.env.example`):

```env
LLM_BASE_URL=https://app-opd-llm.cloud.sdu.dk/v1
LLM_API_KEY=<opd-llm token>
LLM_MODEL=opd-llm
EMBED_MODEL=opd-embed

WHISPER_API_URL=https://app-opd-whisper.cloud.sdu.dk/v1
WHISPER_API_KEY=<opd-whisper token>
```

Then `docker compose up -d --build`. The local `ollama` container no longer
starts (it is behind the `local-llm` profile). On start-up ai-service logs
`LLM endpoint ... reachable, models: ['opd-llm']`.

### Offline / UCloud job not running

```env
LLM_BASE_URL=http://ollama:11434/v1
LLM_API_KEY=
LLM_MODEL=llama3.2:3b
EMBED_MODEL=nomic-embed-text
WHISPER_API_URL=
```

and `docker compose --profile local-llm up -d`. Whisper then runs on the local CPU again.

> ⚠️ Embeddings from Ollama's `nomic-embed-text` and vLLM's `nomic-embed-text-v1.5`
> are not interchangeable. After switching between them, old RAG chunks in
> `ai-db` give poor matches — re-process consultations or clear the table.

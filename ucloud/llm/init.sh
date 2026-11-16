#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# UCloud "Nginx Web Server" init script — OPD-Vertex LLM + embeddings
#
# Runs two vLLM servers on the job's GPU and puts nginx (with a Bearer token)
# in front of them, so the local ai-service can reach them via the public link:
#
#   https://<public-link>/v1/chat/completions  ->  vLLM chat   127.0.0.1:8000
#   https://<public-link>/v1/embeddings        ->  vLLM embed  127.0.0.1:8001
#
# Everything heavy (venv, model weights, token) lives in $BASE_DIR, which is
# the folder you mount from /work, so restarts are fast.
# Override any variable below by exporting it before the script runs or by
# editing the defaults here.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

BASE_DIR="${BASE_DIR:-/work/opd-llm}"

LLM_MODEL="${LLM_MODEL:-Qwen/Qwen3-8B-FP8}"            # chat model (HF id)
LLM_SERVED_NAME="${LLM_SERVED_NAME:-opd-llm}"          # name the client uses
LLM_MAX_LEN="${LLM_MAX_LEN:-16384}"                    # context window
LLM_GPU_UTIL="${LLM_GPU_UTIL:-0.75}"                   # share of GPU memory

EMBED_MODEL="${EMBED_MODEL:-nomic-ai/nomic-embed-text-v1.5}"  # 768-dim, = pgvector schema
EMBED_SERVED_NAME="${EMBED_SERVED_NAME:-opd-embed}"
EMBED_GPU_UTIL="${EMBED_GPU_UTIL:-0.12}"

VLLM_SPEC="${VLLM_SPEC:-vllm}"                         # e.g. "vllm==0.11.0" to pin
INSTALL_CUDA_TOOLKIT="${INSTALL_CUDA_TOOLKIT:-0}"     # 1 = apt install CUDA toolkit (only if vLLM complains about nvcc)

LOG_DIR="$BASE_DIR/logs"
SECRETS_DIR="$BASE_DIR/secrets"
VENV="$BASE_DIR/.venv"
mkdir -p "$LOG_DIR" "$SECRETS_DIR"

# If a server crashes: show why, then keep the job alive so you can open a
# terminal on the job page and debug (instead of the job silently ending).
fail_and_wait() {  # fail_and_wait <message> <logfile>
  set +e
  echo ""
  echo "############################################################"
  echo "### FAILED: $1"
  echo "### Last 80 lines of $2:"
  echo "############################################################"
  tail -n 80 "$2"
  echo "############################################################"
  nvidia-smi
  echo "### Job kept alive for debugging. Fix, then restart the job."
  sleep infinity
}

# ── [1/6] API token ──────────────────────────────────────────────────────────
echo "==> [1/6] Loading API token..."
if [ ! -s "$SECRETS_DIR/api_token" ]; then
  (umask 077; openssl rand -hex 32 > "$SECRETS_DIR/api_token")
  echo "    Generated a NEW token in $SECRETS_DIR/api_token"
  echo "    Copy it into LLM_API_KEY in your local .env"
fi
API_TOKEN="$(tr -d '[:space:]' < "$SECRETS_DIR/api_token")"
echo "==> [1/6] Done."

# ── [2/6] nginx reverse proxy ────────────────────────────────────────────────
echo "==> [2/6] Configuring nginx reverse proxy..."
sed "s/__API_TOKEN__/${API_TOKEN}/" "$BASE_DIR/default.conf.template" \
  | sudo tee /etc/nginx/conf.d/default.conf > /dev/null
if pgrep -x nginx > /dev/null 2>&1; then
  sudo nginx -s reload
  echo "==> [2/6] Done: nginx reloaded."
else
  (sudo systemctl start nginx 2>/dev/null || sudo nginx) &
  disown || true
  sleep 1
  echo "==> [2/6] Done: nginx started in background."
fi

# ── [3/6] (optional) CUDA toolkit ────────────────────────────────────────────
if [ "$INSTALL_CUDA_TOOLKIT" = "1" ] && [ ! -x /usr/local/cuda/bin/nvcc ]; then
  echo "==> [3/6] Installing CUDA toolkit (this takes a while)..."
  DISTRO=$(. /etc/os-release && echo "ubuntu${VERSION_ID//./}")
  wget -q "https://developer.download.nvidia.com/compute/cuda/repos/${DISTRO}/x86_64/cuda-keyring_1.1-1_all.deb" -O /tmp/cuda-keyring.deb
  sudo dpkg -i /tmp/cuda-keyring.deb
  sudo apt-get update
  sudo apt-get install -y cuda-toolkit
  export CUDA_HOME=/usr/local/cuda
  export PATH="${CUDA_HOME}/bin:$PATH"
  export LD_LIBRARY_PATH="${CUDA_HOME}/lib64:${LD_LIBRARY_PATH:-}"
  echo "==> [3/6] Done."
else
  echo "==> [3/6] Skipping CUDA toolkit (vLLM wheels ship their own CUDA runtime)."
fi
nvidia-smi || echo "    WARNING: nvidia-smi failed — did you pick a GPU machine type?"

# ── [4/6] Python venv + vLLM (only first time) ───────────────────────────────
echo "==> [4/6] Preparing Python venv with vLLM..."
if ! command -v uv > /dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
if [ ! -f "$VENV/.vllm-installed" ]; then
  uv venv --python 3.12 --clear "$VENV"
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  uv pip install --upgrade "$VLLM_SPEC"
  touch "$VENV/.vllm-installed"
  echo "==> [4/6] Done: vLLM installed."
else
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  echo "==> [4/6] Done: reusing existing venv."
fi

# ── [5/6] Hugging Face cache (+ optional token for gated models) ─────────────
export HF_HOME="$BASE_DIR/hf-cache"
if [ -s "$SECRETS_DIR/hf_token" ]; then
  HF_TOKEN="$(tr -d '[:space:]' < "$SECRETS_DIR/hf_token")"
  export HF_TOKEN
  echo "==> [5/6] Using Hugging Face token from $SECRETS_DIR/hf_token"
else
  echo "==> [5/6] No hf_token file — fine for public models (Qwen, nomic)."
fi

# ── [6/6] Start vLLM servers ─────────────────────────────────────────────────
wait_for() {  # wait_for <port> <name> <logfile>
  echo "    Waiting for $2 on port $1 (first run downloads the model)..."
  until curl -sf "http://127.0.0.1:$1/health" > /dev/null; do
    if ! kill -0 "$EMBED_PID" 2>/dev/null; then
      fail_and_wait "$2 exited during start-up" "$3"
    fi
    sleep 5
  done
  echo "    $2 is up."
}

echo "==> [6/6] Starting embedding server ($EMBED_MODEL)..."
vllm serve "$EMBED_MODEL" \
  --host 127.0.0.1 --port 8001 \
  --served-model-name "$EMBED_SERVED_NAME" \
  --trust-remote-code \
  --gpu-memory-utilization "$EMBED_GPU_UTIL" \
  ${EMBED_EXTRA_ARGS:-} \
  > "$LOG_DIR/embed.log" 2>&1 &
EMBED_PID=$!
wait_for 8001 "embedding server" "$LOG_DIR/embed.log"

echo "==> [6/6] Starting chat server ($LLM_MODEL) — logs follow below."
# Foreground: the job's log window shows vLLM output, and the job keeps running.
vllm serve "$LLM_MODEL" \
  --host 127.0.0.1 --port 8000 \
  --served-model-name "$LLM_SERVED_NAME" \
  --max-model-len "$LLM_MAX_LEN" \
  --gpu-memory-utilization "$LLM_GPU_UTIL" \
  ${LLM_EXTRA_ARGS:-} \
  > "$LOG_DIR/llm.log" 2>&1 &
LLM_PID=$!
tail -n +1 -f "$LOG_DIR/llm.log" &   # show vLLM output in the job log
wait "$LLM_PID" || true
fail_and_wait "vLLM chat server ($LLM_MODEL) exited" "$LOG_DIR/llm.log"

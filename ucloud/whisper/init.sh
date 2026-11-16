#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# UCloud "Nginx Web Server" init script — OPD-Vertex faster-whisper
#
#   https://<public-link>/v1/audio/transcriptions -> server.py on 127.0.0.1:9000
#
# venv, model weights and token live in $BASE_DIR (the folder mounted from
# /work), so only the first start is slow.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

BASE_DIR="${BASE_DIR:-/work/opd-whisper}"
export WHISPER_MODEL="${WHISPER_MODEL:-large-v3}"         # tiny|base|small|medium|large-v3|...
export WHISPER_DEVICE="${WHISPER_DEVICE:-cuda}"
export WHISPER_COMPUTE_TYPE="${WHISPER_COMPUTE_TYPE:-float16}"

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

# ── [1/4] API token ──────────────────────────────────────────────────────────
echo "==> [1/4] Loading API token..."
if [ ! -s "$SECRETS_DIR/api_token" ]; then
  (umask 077; openssl rand -hex 32 > "$SECRETS_DIR/api_token")
  echo "    Generated a NEW token in $SECRETS_DIR/api_token"
  echo "    Copy it into WHISPER_API_KEY in your local .env"
fi
API_TOKEN="$(tr -d '[:space:]' < "$SECRETS_DIR/api_token")"
echo "==> [1/4] Done."

# ── [2/4] nginx reverse proxy ────────────────────────────────────────────────
echo "==> [2/4] Configuring nginx reverse proxy..."
sed "s/__API_TOKEN__/${API_TOKEN}/" "$BASE_DIR/default.conf.template" \
  | sudo tee /etc/nginx/conf.d/default.conf > /dev/null
if pgrep -x nginx > /dev/null 2>&1; then
  sudo nginx -s reload
  echo "==> [2/4] Done: nginx reloaded."
else
  (sudo systemctl start nginx 2>/dev/null || sudo nginx) &
  disown || true
  sleep 1
  echo "==> [2/4] Done: nginx started in background."
fi
nvidia-smi || echo "    WARNING: nvidia-smi failed — did you pick a GPU machine type?"

# ── [3/4] Python venv (only first time) ──────────────────────────────────────
echo "==> [3/4] Preparing Python venv with faster-whisper..."
if ! command -v uv > /dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
if [ ! -f "$VENV/.whisper-installed" ]; then
  uv venv --python 3.12 --clear "$VENV"
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  # cuBLAS + cuDNN 9 as pip wheels -> no system CUDA install needed
  uv pip install faster-whisper "fastapi>=0.115" "uvicorn[standard]" python-multipart \
    nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
  touch "$VENV/.whisper-installed"
  echo "==> [3/4] Done: packages installed."
else
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  echo "==> [3/4] Done: reusing existing venv."
fi
LD_LIBRARY_PATH="$(python -c 'import os, nvidia.cublas.lib, nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'):${LD_LIBRARY_PATH:-}"
export LD_LIBRARY_PATH
export HF_HOME="$BASE_DIR/hf-cache"

# ── [4/4] Start the server (foreground) ──────────────────────────────────────
echo "==> [4/4] Starting faster-whisper server ($WHISPER_MODEL) — logs follow below."
cd "$BASE_DIR"
uvicorn server:app --host 127.0.0.1 --port 9000 > "$LOG_DIR/whisper.log" 2>&1 &
SRV_PID=$!
tail -n +1 -f "$LOG_DIR/whisper.log" &   # show server output in the job log
wait "$SRV_PID" || true
fail_and_wait "faster-whisper server exited" "$LOG_DIR/whisper.log"

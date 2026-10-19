#!/usr/bin/env bash
# =============================================================================
#  PUBLIC MODE — Ollama (local) + free public URL, BINA CARD, BINA ACCOUNT
#
#  Kya karta hai:
#   1. Check: Ollama chal raha hai? model hai?
#   2. SuperAgent server start (background)
#   3. Cloudflare Quick Tunnel -> https://xxx.trycloudflare.com
#
#  Chalane ka tarika:
#     bash deploy/start-public.sh
#     bash deploy/start-public.sh --mail tumhara@email.com   # sirf tum khol sako
#     bash deploy/start-public.sh --port 5000 --model qwen2.5-coder:7b
#
#  Rokna: Ctrl+C (server + tunnel dono band ho jayenge)
# =============================================================================
set -euo pipefail

PORT=5000
MODEL="${AGENT_MODEL:-qwen2.5-coder:7b}"
ALLOWED_MAIL=""
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

while [ $# -gt 0 ]; do
  case "$1" in
    --port)  PORT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --mail|--allowed-mail) ALLOWED_MAIL="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed -n '2,15p' | sed 's/^#  \{0,2\}//'; exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

say() { printf "\n\033[1;36m▸ %s\033[0m\n" "$*"; }
ok()  { printf "  \033[1;32m✓\033[0m %s\n" "$*"; }
bad() { printf "  \033[1;31m✗\033[0m %s\n" "$*"; }
warn(){ printf "  \033[1;33m!\033[0m %s\n" "$*"; }

cd "$APP_DIR"

# ── 1) Ollama check ─────────────────────────────────────────────────────────
say "Ollama check"
if ! command -v ollama >/dev/null 2>&1; then
  bad "Ollama install nahi hai"
  echo "     Windows: https://ollama.com/download"
  echo "     Mac    : brew install ollama"
  echo "     Linux  : curl -fsSL https://ollama.com/install.sh | sh"
  exit 1
fi

if ! curl -s -m 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
  warn "Ollama band hai — start kar raha hoon…"
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^ollama'; then
    sudo systemctl start ollama || true
  else
    (ollama serve >/dev/null 2>&1 &) || true
  fi
  sleep 3
fi

if curl -s -m 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
  ok "Ollama chal raha hai"
else
  bad "Ollama start nahi hua — alag terminal me 'ollama serve' chalao"
  exit 1
fi

# model present?
if ollama list 2>/dev/null | awk 'NR>1{print $1}' | grep -qx "$MODEL"; then
  ok "Model ready: $MODEL"
else
  warn "Model nahi mila: $MODEL — pull kar raha hoon (2-5 GB, thoda time)"
  ollama pull "$MODEL"
  ok "Model ready: $MODEL"
fi

# ── 2) Python deps ──────────────────────────────────────────────────────────
say "Python dependencies"
PY=python3; command -v $PY >/dev/null || PY=python
if [ -d .venv ]; then . .venv/bin/activate; PY=python; fi
$PY -c "import flask, openai, dotenv" 2>/dev/null || {
  warn "Dependencies missing — install kar raha hoon"
  $PY -m pip install -q -r requirements.txt
}
ok "Dependencies ready"

# ── 3) Server start ─────────────────────────────────────────────────────────
say "SuperAgent server"
if curl -s -m 3 "http://localhost:$PORT/healthz" >/dev/null 2>&1; then
  ok "Server pehle se chal raha hai (port $PORT)"
  SERVER_PID=""
else
  NO_AUTH=1 PORT="$PORT" DATA_DIR="$APP_DIR/data" AGENT_MODEL="$MODEL" \
    OLLAMA_BASE_URL="http://localhost:11434/v1" \
    nohup $PY server.py > "$APP_DIR/server.log" 2>&1 &
  SERVER_PID=$!
  for _ in $(seq 1 20); do
    sleep 0.5
    curl -s -m 2 "http://localhost:$PORT/healthz" >/dev/null 2>&1 && break
  done
  if curl -s -m 2 "http://localhost:$PORT/healthz" >/dev/null 2>&1; then
    ok "Server chalu: http://localhost:$PORT  (log: server.log)"
  else
    bad "Server start nahi hua — server.log dekho:"; tail -20 server.log; exit 1
  fi
fi

# ── 4) cloudflared ──────────────────────────────────────────────────────────
say "Cloudflare Tunnel (free, no account, no card)"
if ! command -v cloudflared >/dev/null 2>&1; then
  bad "cloudflared install nahi hai"
  echo "     Windows: winget install Cloudflare.cloudflared"
  echo "     Mac    : brew install cloudflared"
  echo "     Linux  : https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
  echo
  echo "  Abhi ke liye LAN pe try karo:"
  echo "     http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 127.0.0.1):$PORT"
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
  exit 0
fi

cleanup() {
  echo
  say "Band kar raha hoon…"
  [ -n "${TUNNEL_PID:-}" ] && kill "$TUNNEL_PID" 2>/dev/null || true
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

CF_ARGS=(tunnel --url "http://localhost:$PORT" --no-autoupdate)
# Oct 2026: email-locked quick tunnel — bina Cloudflare account
if [ -n "$ALLOWED_MAIL" ]; then
  CF_ARGS+=(--allowed-mail "$ALLOWED_MAIL")
  ok "Access lock: sirf $ALLOWED_MAIL (OTP se verify)"
fi

cloudflared "${CF_ARGS[@]}" > "$APP_DIR/tunnel.log" 2>&1 &
TUNNEL_PID=$!

echo
echo "════════════════════════════════════════════════════════════"
URL=""
for _ in $(seq 1 40); do
  sleep 1
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$APP_DIR/tunnel.log" 2>/dev/null | head -1 || true)
  [ -n "$URL" ] && break
done

if [ -n "$URL" ]; then
  echo "  ✅ PUBLIC URL (free):  $URL"
  echo
  echo "  Model     : $MODEL (Ollama — local, unlimited, no API key)"
  echo "  Login     : koi password nahi (NO_AUTH mode)"
  echo
  echo "  ⚠️  URL temporary hai — is process ke band hone pe khatam."
  echo "  ⚠️  Laptop on rehna chahiye. Band karo to site band."
  echo "════════════════════════════════════════════════════════════"
else
  echo "  ⚠️  URL nahi mila — tunnel.log dekho:"
  tail -15 "$APP_DIR/tunnel.log" 2>/dev/null || true
  echo "════════════════════════════════════════════════════════════"
fi

wait "$TUNNEL_PID" 2>/dev/null || true

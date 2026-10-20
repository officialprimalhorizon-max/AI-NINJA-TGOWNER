#!/usr/bin/env bash
# =============================================================================
#  run-forever.sh — AI Ninja ko ZINDA rakhta hai
#
#  Kar kya raha hai:
#    - Ollama serve (agar down ho to start)
#    - Model RAM me preload + pin (KEEP_ALIVE=-1)  -> cold start khatam
#    - Server (agar down ho to start)
#    - cloudflared quick tunnel (http2, auto restart)
#    - har 20s check: server down? tunnel down? -> restart + naya URL print
#    - URL /opt/ai-ninja/URL.txt me save
#
#  Chalane ka tarika:
#      cd /opt/ai-ninja && bash run-forever.sh
#  Background me chhodna ho:
#      setsid nohup bash run-forever.sh > /opt/ai-ninja/supervisor.log 2>&1 &
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")" || exit 1

PORT=$(grep '^PORT=' .env 2>/dev/null | cut -d= -f2); PORT=${PORT:-8000}
MODEL=$(grep '^AGENT_MODEL=' .env 2>/dev/null | cut -d= -f2); MODEL=${MODEL:-qwen2.5-coder:7b}
PASSW=$(grep '^APP_PASSWORD=' .env 2>/dev/null | cut -d= -f2)
APP_DIR="$(pwd)"

c_g() { printf '\033[32m%s\033[0m\n' "$*"; }
c_y() { printf '\033[33m%s\033[0m\n' "$*"; }
c_r() { printf '\033[31m%s\033[0m\n' "$*"; }
c_c() { printf '\033[36m%s\033[0m\n' "$*"; }
ts()  { date +%H:%M:%S; }

# ─────────────────────────────── ollama
ensure_ollama() {
  if ! curl -s -m 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
    c_y "$(ts) Ollama down -> start"
    OLLAMA_KEEP_ALIVE=-1 nohup ollama serve >/tmp/ollama.log 2>&1 &
    for i in $(seq 1 30); do
      curl -s -m 2 http://localhost:11434/api/tags >/dev/null 2>&1 && break
      sleep 1
    done
  fi
  # model preload + pin (cold start hatao)
  curl -s -m 300 http://localhost:11434/api/generate \
    -d "{\"model\":\"$MODEL\",\"prompt\":\"hi\",\"stream\":false,\"keep_alive\":-1,\"options\":{\"num_predict\":1}}" \
    >/dev/null 2>&1
}

# ─────────────────────────────── server
ensure_server() {
  if ! curl -s -m 4 "http://localhost:$PORT/healthz" 2>/dev/null | grep -q ok; then
    c_y "$(ts) Server down -> start"
    pkill -f "python server.py" 2>/dev/null
    sleep 1
    set -a; . "$APP_DIR/.env" 2>/dev/null; set +a
    export OLLAMA_KEEP_ALIVE=-1 PORT="$PORT"
    nohup .venv/bin/python server.py >> server.log 2>&1 &
    for i in $(seq 1 40); do
      curl -s -m 2 "http://localhost:$PORT/healthz" 2>/dev/null | grep -q ok && break
      sleep 1
    done
  fi
}

# ─────────────────────────────── tunnel
ensure_tunnel() {
  pkill -f "cloudflared tunnel" 2>/dev/null
  sleep 1
  nohup cloudflared tunnel --url "http://localhost:$PORT" \
        --no-autoupdate --protocol http2 \
        > /tmp/cf.log 2>&1 &
  local u=""
  for i in $(seq 1 40); do
    u=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cf.log 2>/dev/null | tail -1)
    [ -n "$u" ] && break
    sleep 2
  done
  echo "$u"
}

# ─────────────────────────────── banner
banner() {
  echo
  echo "══════════════════════════════════════════════════════════"
  c_g  "  🥷 AI NINJA LIVE"
  echo "══════════════════════════════════════════════════════════"
  echo "  LOCAL  : http://localhost:$PORT"
  echo "  PUBLIC : $1"
  echo "  PASS   : $PASSW"
  echo "  MODEL  : $MODEL (Ollama local)"
  echo "  DATA   : $APP_DIR/data"
  echo "══════════════════════════════════════════════════════════"
  echo
}

echo "$(ts) Ollama ensure..."
ensure_ollama && c_g "$(ts) Ollama live + model pinned"

echo "$(ts) Server ensure..."
ensure_server && c_g "$(ts) Server live :$PORT"

echo "$(ts) Tunnel start..."
URL=$(ensure_tunnel)
[ -n "$URL" ] && { echo "$URL" > URL.txt; banner "$URL"; } || c_r "$(ts) Tunnel fail -> /tmp/cf.log dekho"

# ─────────────────────────────── watch loop
while true; do
  sleep 20

  ensure_ollama >/dev/null 2>&1

  if ! curl -s -m 4 "http://localhost:$PORT/healthz" 2>/dev/null | grep -q ok; then
    c_r "$(ts) server down -> restart"
    ensure_server >/dev/null 2>&1
  fi

  U=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cf.log 2>/dev/null | tail -1)
  if [ -z "$U" ] || ! curl -s -m 8 -o /dev/null "$U/healthz" 2>/dev/null; then
    c_r "$(ts) tunnel down -> restart"
    NU=$(ensure_tunnel)
    if [ -n "$NU" ]; then
      URL="$NU"; echo "$NU" > URL.txt
      c_g "$(ts) NAYA URL: $NU"
    fi
  elif [ "$U" != "$URL" ]; then
    URL="$U"; echo "$U" > URL.txt
    c_c "$(ts) URL: $U"
  fi
done

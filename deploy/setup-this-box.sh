#!/usr/bin/env bash
# =============================================================================
#  ONE-SHOT SETUP — kisi bhi bare-metal / VPS / container ke liye
#  (Kali, Ubuntu, Debian, whatever — root ke roop me chalao)
#
#  Ye script:
#    1. Python + venv + node + git install karta hai
#    2. Ollama install karta hai (local model = unlimited, free, no key)
#    3. Model pull karta hai (RAM dekh ke)
#    4. App ka venv + deps
#    5. Server start (nohup) + Cloudflare quick tunnel = public URL
#
#  Usage:
#    bash deploy/setup-this-box.sh                    # default model
#    bash deploy/setup-this-box.sh --model qwen2.5-coder:14b
#    bash deploy/start-public.sh --model qwen2.5-coder:7b   # (purana, sirf tunnel+server)
# =============================================================================
set -uo pipefail

MODEL="qwen2.5-coder:7b"
PORT="${PORT:-8000}"
APP_DIR="${APP_DIR:-/opt/ai-ninja}"
REPO_URL="${REPO_URL:-https://github.com/officialprimalhorizon-max/AI-NINJA-TGOWNER.git}"
PASSWORD="${APP_PASSWORD:-}"
NO_TUNNEL=0
GROQ_KEY="${GROQ_API_KEY:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)  MODEL="$2"; shift 2 ;;
    --port)   PORT="$2"; shift 2 ;;
    --dir)    APP_DIR="$2"; shift 2 ;;
    --no-tunnel) NO_TUNNEL=1; shift ;;
    --help|-h) tail -n +2 "$0" | head -24 | grep '^#' | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

c_g() { printf '\033[32m%s\033[0m\n' "$*"; }
c_y() { printf '\033[33m%s\033[0m\n' "$*"; }
c_r() { printf '\033[31m%s\033[0m\n' "$*"; }
step() { printf '\n\033[36m==> %s\033[0m\n' "$*"; }

# ─────────────────────────────────────────── 0. root check
if [[ $EUID -ne 0 ]]; then
  c_y "root nahi ho — sudo chahiye ho sakta hai. Jaari rakh raha hoon..."
fi

# ─────────────────────────────────────────── 1. system deps
step "1/6  System packages"
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq 2>/dev/null || true
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
      python3 python3-venv python3-pip curl ca-certificates git \
      nodejs npm unzip tzdata procps zstd unzip xz-utils 2>&1 | tail -3
elif command -v apk >/dev/null 2>&1; then
  apk add --no-cache python3 py3-pip curl ca-certificates git nodejs npm unzip bash zstd
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y -q python3 python3-pip curl ca-certificates git nodejs npm unzip zstd
else
  c_y "Unknown package manager — jo hai wahi use karunga"
fi
c_g "  ✅ python: $(python3 --version 2>&1)"
c_g "  ✅ node  : $(node --version 2>/dev/null || echo 'missing — JS nahi chalega')"

# ─────────────────────────────────────────── 2. Ollama
step "2/6  Ollama (local model — unlimited, no key)"
if command -v ollama >/dev/null 2>&1; then
  c_g "  ✅ Ollama pehle se installed ($(ollama --version 2>/dev/null | head -1))"
else
  # zstd ensure (Ollama installer isi se extract karta hai)
  if ! command -v zstd >/dev/null 2>&1; then
    c_y "  zstd missing -> install kar raha hoon"
    if command -v apt-get >/dev/null 2>&1; then
      DEBIAN_FRONTEND=noninteractive apt-get install -y -qq zstd 2>&1 | tail -2
    elif command -v dnf >/dev/null 2>&1; then dnf install -y -q zstd
    elif command -v apk >/dev/null 2>&1; then apk add --no-cache zstd
    fi
  fi
  c_y "  Ollama install ho raha hai..."
  curl -fsSL https://ollama.com/install.sh | sh 2>&1 | tail -6
  if ! command -v ollama >/dev/null 2>&1; then
    c_y "  installer fail -> direct binary download try kar raha hoon"
    ARCH=$(uname -m); case "$ARCH" in x86_64) OARCH=amd64 ;; aarch64) OARCH=arm64 ;; *) OARCH=amd64 ;; esac
    curl -fsSL -o /tmp/ollama.tgz "https://ollama.com/download/ollama-linux-$OARCH.tgz" \
      && tar -C /usr/local -xzf /tmp/ollama.tgz 2>/dev/null \
      && ln -sf /usr/local/bin/ollama /usr/bin/ollama 2>/dev/null || true
  fi
  command -v ollama >/dev/null 2>&1 && c_g "  ✅ Ollama installed ($(ollama --version 2>/dev/null | head -1))" \
    || c_r "  ❌ Ollama install fail — Pollinations keyless fallback chalega"
fi

# serve (systemd ho to wahi, warna nohup)
if ! curl -s -m 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
  c_y "  Ollama serve start kar raha hoon..."
  if command -v systemctl >/dev/null 2>&1 && systemctl is-system-running >/dev/null 2>&1; then
    systemctl enable --now ollama 2>/dev/null || true
  fi
  if ! curl -s -m 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
    OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 nohup ollama serve >/tmp/ollama.log 2>&1 &
    for i in $(seq 1 30); do
      curl -s -m 2 http://localhost:11434/api/tags >/dev/null 2>&1 && break
      sleep 1
    done
  fi
fi
curl -s -m 3 http://localhost:11434/api/tags >/dev/null 2>&1 \
  && c_g "  ✅ Ollama live -> http://localhost:11434" \
  || c_r "  ⚠️  Ollama respond nahi kar raha — Pollinations keyless fallback chalega"

# ─────────────────────────────────────────── 3. model
step "3/6  Model pull: $MODEL"
RAM_GB=$(( $(awk '/MemTotal/{print $2}' /proc/meminfo) / 1024 / 1024 ))
c_y "  RAM: ${RAM_GB} GB"
if curl -s -m 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
  if ollama list 2>/dev/null | grep -q "${MODEL%%:*}"; then
    c_g "  ✅ Model pehle se hai"
  else
    c_y "  Download ho raha hai (2-5 min, ${MODEL})..."
    ollama pull "$MODEL" 2>&1 | tail -3
  fi
fi

# ─────────────────────────────────────────── 4. app
step "4/6  App setup -> $APP_DIR"
if [[ -f "./server.py" ]]; then
  SRC="$(pwd)"
else
  SRC=""
fi

mkdir -p "$APP_DIR"
if [[ -n "$SRC" && "$SRC" != "$APP_DIR" ]]; then
  cp -r "$SRC"/. "$APP_DIR"/ 2>/dev/null || true
fi

cd "$APP_DIR" || exit 1
if [[ ! -f server.py ]]; then
  c_y "  server.py nahi mila -> GitHub se clone kar raha hoon..."
  REPO_URL="${REPO_URL:-https://github.com/officialprimalhorizon-max/AI-NINJA-TGOWNER.git}"
  if command -v git >/dev/null 2>&1; then
    git clone --depth 1 "$REPO_URL" "$APP_DIR" 2>&1 | tail -3
    cd "$APP_DIR" || exit 1
  fi
fi
if [[ ! -f server.py ]]; then
  c_r "  ❌ server.py nahi mila $APP_DIR me."
  c_y "  Manually: git clone ${REPO_URL:-<repo-url>} $APP_DIR"
  exit 1
fi

python3 -m venv .venv 2>/dev/null || python3 -m venv --without-pip .venv
.venv/bin/pip install -q --upgrade pip 2>&1 | tail -1
.venv/bin/pip install -q -r requirements.txt 2>&1 | tail -3
c_g "  ✅ Python deps installed"

# password
if [[ -z "$PASSWORD" ]]; then
  PASSWORD=$(python3 -c "import secrets,string;print(''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(10)))")
fi

cat > .env <<EOF
APP_PASSWORD=$PASSWORD
SECRET_KEY=$(python3 -c "import secrets;print(secrets.token_hex(32))")
DATA_DIR=$APP_DIR/data
PORT=$PORT
OLLAMA_BASE_URL=http://localhost:11434/v1
AGENT_MODEL=$MODEL
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_THREAD=24
OLLAMA_NUM_PREDICT=1400
EOF
[[ -n "$GROQ_KEY" ]] && echo "GROQ_API_KEY=$GROQ_KEY" >> .env
chmod 600 .env
c_g "  ✅ .env banaya"

# ─────────────────────────────────────────── 5. server
step "5/6  Server start"
pkill -f "server.py" 2>/dev/null || true
pkill -f "gunicorn.*server:app" 2>/dev/null || true
sleep 1

# .env ko shell me load karo (reliable tarika)
set -a
# shellcheck disable=SC1091
. "$APP_DIR/.env" 2>/dev/null || true
set +a
export OLLAMA_KEEP_ALIVE=-1

START_LOG="$APP_DIR/server.log"
: > "$START_LOG"

# gunicorn hai ya nahi — teen tarah ke fallback
if [[ -x .venv/bin/gunicorn ]]; then
  c_y "  gunicorn: .venv/bin/gunicorn"
  RUN=(.venv/bin/gunicorn --bind "0.0.0.0:$PORT" -w 1 --threads 16 -k gthread
       --timeout 900 --access-logfile "$START_LOG" --error-logfile "$START_LOG" server:app)
elif command -v gunicorn >/dev/null 2>&1; then
  c_y "  gunicorn: system"
  RUN=(gunicorn --bind "0.0.0.0:$PORT" -w 1 --threads 16 -k gthread
       --timeout 900 --access-logfile "$START_LOG" --error-logfile "$START_LOG" server:app)
else
  c_y "  gunicorn nahi mila -> python server.py (Flask threaded fallback)"
  RUN=(.venv/bin/python server.py)
fi

nohup "${RUN[@]}" >> "$START_LOG" 2>&1 &
SERVER_PID=$!
echo "  PID: $SERVER_PID"

for i in $(seq 1 45); do
  curl -s -m 2 "http://localhost:$PORT/healthz" >/dev/null 2>&1 && break
  kill -0 "$SERVER_PID" 2>/dev/null || break
  sleep 1
done

if curl -s -m 3 "http://localhost:$PORT/healthz" | grep -q ok; then
  c_g "  ✅ Server live -> http://localhost:$PORT"
else
  c_r "  ❌ Server start nahi hua. Last 25 lines ($START_LOG):"
  tail -25 "$START_LOG" 2>/dev/null || c_r "  (log file hi nahi bani — $RUN[0] missing?)"
  exit 1
fi

# ─────────────────────────────────────────── 6. public URL
step "6/6  Public URL"
PUBLIC_URL=""
if [[ "$NO_TUNNEL" -eq 1 ]]; then
  c_y "  --no-tunnel: localhost only"
else
  if ! command -v cloudflared >/dev/null 2>&1; then
    ARCH=$(uname -m); case "$ARCH" in x86_64) CF=amd64 ;; aarch64) CF=arm64 ;; *) CF=amd64 ;; esac
    curl -fsSL -o /usr/local/bin/cloudflared \
      "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$CF" \
      && chmod +x /usr/local/bin/cloudflared
  fi
  if command -v cloudflared >/dev/null 2>&1; then
    nohup cloudflared tunnel --url "http://localhost:$PORT" --no-autoupdate \
      > /tmp/cf.log 2>&1 &
    for i in $(seq 1 45); do
      PUBLIC_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cf.log 2>/dev/null | head -1)
      [[ -n "$PUBLIC_URL" ]] && break
      sleep 2
    done
  fi
fi

echo
echo "╔══════════════════════════════════════════════════════════════════╗"
printf "║  %-62s ║\n" "🥷 AI NINJA — LIVE"
echo "╠══════════════════════════════════════════════════════════════════╣"
printf "║  %-62s ║\n" "Local   : http://localhost:$PORT"
[[ -n "$PUBLIC_URL" ]] && printf "║  %-62s ║\n" "Public  : $PUBLIC_URL"
printf "║  %-62s ║\n" "Password: $PASSWORD"
printf "║  %-62s ║\n" "Model   : $MODEL (Ollama local)"
printf "║  %-62s ║\n" "Data    : $APP_DIR/data"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo
c_y "Logs  : tail -f $APP_DIR/server.log"
c_y "Stop  : pkill -f 'gunicorn.*server:app'"
c_y "Tunnel: tail -f /tmp/cf.log"
[[ -z "$PUBLIC_URL" ]] && c_y "Tunnel URL na mila -> cloudflared manually: cloudflared tunnel --url http://localhost:$PORT"

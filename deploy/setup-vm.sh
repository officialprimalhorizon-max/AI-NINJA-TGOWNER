#!/usr/bin/env bash
# =============================================================================
#  SuperAgent + Ollama — one-command VM setup
#  Ubuntu 22.04 / 24.04 (ARM Ampere ya x86 dono chalega)
#
#  Chalane ka tarika (VM ke andar):
#     curl -fsSL https://raw.githubusercontent.com/<you>/<repo>/main/deploy/setup-vm.sh | bash
#  ya:
#     scp -r private-agent ubuntu@VM_IP:~ && ssh ubuntu@VM_IP 'bash ~/private-agent/deploy/setup-vm.sh'
#
#  Kya karta hai:
#   1. Ollama install + model pull (RAM dekh ke model chunta hai)
#   2. Python venv + dependencies
#   3. systemd service (auto-start, auto-restart, boot pe chalu)
#   4. Firewall port + optional Cloudflare tunnel
#   5. Password generate karke print karta hai
# =============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/private-agent}"
PORT="${PORT:-5000}"
MODEL="${MODEL:-}"
PASSWORD="${APP_PASSWORD:-}"

say() { printf "\n\033[1;36m▸ %s\033[0m\n" "$*"; }
ok()  { printf "  \033[1;32m✓\033[0m %s\n" "$*"; }
warn(){ printf "  \033[1;33m!\033[0m %s\n" "$*"; }

# ── root / sudo check ───────────────────────────────────────────────────────
if [ "$(id -u)" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi

say "System info"
. /etc/os-release 2>/dev/null || true
echo "  OS   : ${PRETTY_NAME:-unknown}"
echo "  Arch : $(uname -m)"
RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
echo "  RAM  : ${RAM_GB} GB"
echo "  Disk : $(df -h / | awk 'NR==2{print $4}') free"

# ── RAM ke hisaab se model ──────────────────────────────────────────────────
if [ -z "$MODEL" ]; then
  if   [ "$RAM_GB" -le 5 ];  then MODEL="qwen2.5-coder:3b"
  elif [ "$RAM_GB" -le 9 ];  then MODEL="qwen2.5-coder:7b"
  elif [ "$RAM_GB" -le 16 ]; then MODEL="qwen2.5-coder:7b"
  else                            MODEL="qwen2.5-coder:14b"
  fi
fi
say "Model: $MODEL"

# ── 1) Ollama ───────────────────────────────────────────────────────────────
if command -v ollama >/dev/null 2>&1; then
  ok "Ollama already installed ($(ollama --version 2>/dev/null | head -1))"
else
  say "Ollama install ho raha hai…"
  curl -fsSL https://ollama.com/install.sh | sh
  ok "Ollama installed"
fi

# model RAM me hi rakho -> Oracle idle reclaim se bacho + pehla jawab fast
say "Ollama config (model RAM me hold)"
$SUDO mkdir -p /etc/systemd/system/ollama.service.d
$SUDO tee /etc/systemd/system/ollama.service.d/override.conf >/dev/null <<'EOF'
[Service]
Environment="OLLAMA_KEEP_ALIVE=-1"
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
EOF
$SUDO systemctl daemon-reload
$SUDO systemctl enable --now ollama
sleep 3

say "Model pull: $MODEL (thoda time lagega, 2-5 GB)"
ollama pull "$MODEL" && ok "Model ready"

# ── 2) Python app ───────────────────────────────────────────────────────────
if [ ! -d "$APP_DIR" ]; then
  warn "$APP_DIR nahi mila."
  echo "  Pehle app upload karo:  scp -r private-agent ubuntu@VM:~"
  echo "  Phir dobara chalao:     bash ~/private-agent/deploy/setup-vm.sh"
  exit 1
fi

say "Python environment"
command -v python3 >/dev/null || { $SUDO apt-get update -qq && $SUDO apt-get install -y python3 python3-venv python3-pip; }
cd "$APP_DIR"
python3 -m venv .venv
. .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
ok "Dependencies installed"

# ── 3) Password + env ───────────────────────────────────────────────────────
if [ -z "$PASSWORD" ]; then
  if [ -f "$APP_DIR/.env" ] && grep -q '^APP_PASSWORD=' "$APP_DIR/.env" 2>/dev/null; then
    PASSWORD=$(grep '^APP_PASSWORD=' "$APP_DIR/.env" | cut -d= -f2-)
  else
    PASSWORD=$(tr -dc 'a-zA-Z0-9' </dev/urandom | head -c 14)
  fi
fi

cat > "$APP_DIR/.env" <<EOF
APP_PASSWORD=$PASSWORD
SECRET_KEY=$(tr -dc 'a-f0-9' </dev/urandom | head -c 40)
DATA_DIR=$APP_DIR/data
OLLAMA_BASE_URL=http://localhost:11434/v1
AGENT_MODEL=$MODEL
PORT=$PORT
EOF
chmod 600 "$APP_DIR/.env"
ok ".env likhi gayi (chmod 600)"

# ── 4) systemd service ──────────────────────────────────────────────────────
say "systemd service"
$SUDO tee /etc/systemd/system/superagent.service >/dev/null <<EOF
[Unit]
Description=SuperAgent (private AI agent + Ollama)
After=network-online.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/gunicorn --bind 0.0.0.0:$PORT \\
  --workers 1 --threads 16 --worker-class gthread \\
  --timeout 900 --graceful-timeout 30 \\
  --access-logfile - --error-logfile - server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

$SUDO systemctl daemon-reload
$SUDO systemctl enable --now superagent
sleep 3
systemctl is-active --quiet superagent && ok "SuperAgent chalu hai" || warn "Service fail — dekho: journalctl -u superagent -n 50"

# ── 5) firewall ─────────────────────────────────────────────────────────────
if command -v ufw >/dev/null 2>&1; then
  $SUDO ufw allow "$PORT"/tcp >/dev/null 2>&1 || true
  ok "ufw: port $PORT khula"
fi
# Oracle ke iptables rules (Ubuntu images pe by default band hote hain)
if command -v iptables >/dev/null 2>&1; then
  $SUDO iptables -I INPUT 6 -m state --state NEW -p tcp --dport "$PORT" -j ACCEPT 2>/dev/null || true
  $SUDO netfilter-persistent save >/dev/null 2>&1 || true
fi

# ── 6) status ───────────────────────────────────────────────────────────────
IP=$(curl -s -m 5 ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo
echo "════════════════════════════════════════════════════════════"
echo "  ✅ READY"
echo "════════════════════════════════════════════════════════════"
echo "  App      : http://$IP:$PORT"
echo "  Password : $PASSWORD"
echo "  Model    : $MODEL (Ollama, local)"
echo
echo "  Logs     : journalctl -u superagent -f"
echo "  Ollama   : journalctl -u ollama -f"
echo "  Restart  : sudo systemctl restart superagent"
echo
echo "  ⚠️  Oracle Security List me bhi port $PORT kholna padega:"
echo "      Console → Networking → VCN → Security Lists → Default → Add Ingress Rule"
echo "      Source 0.0.0.0/0, TCP, Destination Port $PORT"
echo "════════════════════════════════════════════════════════════"
echo

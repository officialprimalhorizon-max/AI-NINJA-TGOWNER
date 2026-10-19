#!/usr/bin/env bash
# Private Agent — one-command setup (Linux/Mac/Git Bash)
set -e

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   MERA AGENT — setup                 ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# python check
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else echo "❌ Python install nahi hai. https://python.org se install karo."; exit 1; fi
echo "✓ Python: $($PY --version)"

# deps
echo "→ Dependencies install ho rahi hain…"
$PY -m pip install -q --upgrade pip
$PY -m pip install -q -r requirements.txt
echo "✓ Dependencies ready"

# env file
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✓ .env ban gayi"
else
  echo "✓ .env pehle se hai"
fi

echo ""
echo "────────────────────────────────────────────"
echo " Ab ye chuno:"
echo ""
echo "  A) UNLIMITED + 100% FREE (local model, koi key nahi)"
echo "     1. https://ollama.com/download  se Ollama install karo"
echo "     2. ollama pull qwen3:8b"
echo "     3. python agent.py --provider ollama"
echo ""
echo "  B) FREE CLOUD KEY (fast, par daily limit)"
echo "     Groq   -> https://console.groq.com/keys"
echo "     Gemini -> https://aistudio.google.com/apikey"
echo "     .env me GROQ_API_KEY=... daalo"
echo "     python agent.py"
echo ""
echo "  C) WEB UI (ChatGPT jaisa)"
echo "     python webapp.py   ->  http://localhost:5000"
echo "────────────────────────────────────────────"
echo ""

# 🥷 AI NINJA — apna private AI agent (Railway, bina API key)

**Sabse pehle ye padho.** Ye repo ek **complete AI agent** hai jo:

- 🆓 **Bina API key** chalta hai (keyless free mode — Pollinations, GPT-OSS 20B)
- 📁 Files banata hai, padhta hai (workspace)
- 🐍 **Python, JavaScript, Java, C, C++, Rust, Go, PHP, Ruby, Lua, Bash, C#** chalata hai
- 💻 **Apna terminal** (npm install, pip install, git, ffmpeg...)
- 🌐 Web page fetch karta hai
- ⚡ **Streaming** (token-by-token jawab)
- 💬 **Multi-chat** + history + login
- 🌍 24/7 deploy-ready (Railway / Render / Oracle / laptop)

---

## 🚂 Railway pe deploy (5 minute, 30 din free)

### 1. Variables (sirf 2)
```
APP_PASSWORD = meraagent123        ← apna strong password
DATA_DIR     = /data
```
> **GROQ_API_KEY / koi API key NAHI chahiye.**

### 2. Volume (optional)
Settings → Volumes → Mount: `/data`
(bina volume bhi chalega — fallback `/tmp/data` hai)

### 3. Domain
Settings → Networking → **Generate Domain**

### 4. Kholo
`https://your-app.up.railway.app` → password → chat 🎉

---

## 💻 Local pe chalana

```bash
pip install -r requirements.txt
APP_PASSWORD=admin python server.py     # http://localhost:5001
```

Ya bina login (sirf apne laptop pe):
```bash
NO_AUTH=1 python server.py
```

---

## 🖥️ Ollama (local model, unlimited, no key)

```bash
ollama pull qwen2.5-coder:3b
APP_PASSWORD=admin AGENT_MODEL=qwen2.5-coder:3b \
OLLAMA_BASE_URL=http://localhost:11434/v1 python server.py
```
Ollama chal raha ho to agent **pehle wahi** use karega (free + unlimited + fast).

---

## 📚 Baaki files

| File | Kya |
|---|---|
| `RAILWAY-QUICKSTART.md` | Railway step-by-step (screen pe khula hai) |
| `README-RAILWAY.md` | Railway ki poori guide + kharcha + troubleshooting |
| `README.md` | Poora feature list + commands |
| `deploy/README-OLLAMA-HOSTING.md` | Ollama + free hosting (card/no-card dono) |
| `deploy/start-public.sh` | Laptop + Ollama + free public URL (no card) |
| `deploy/setup-vm.sh` | Oracle VM one-command setup |
| `render.yaml` | Render free deploy (no card, hamesha free) |

---

## ⚠️ Speed

Bina key = **25-30 sec per step** (Pollinations free limit).
Fast chahiye to baad me **ek** variable add karo — turant 1-2 sec:
```
GROQ_API_KEY = gsk_...        (console.groq.com/keys — free, 2 min)
```

---

## 🩺 Deploy fail ho to

| Error | Fix |
|---|---|
| Build fail | `railway.json` me `Dockerfile.slim` hona chahiye |
| Application failed to respond | 120s wait karo (first boot slow), ya logs dekho |
| Login pe kuch na ho | Cookie block — URL me `?t=` token mode automatic hai |
| Chats gayab | Volume `/data` mount karo |
| Java/C++ error | Slim image me sirf Python + JS (RAM bachane ke liye) — full chahiye to `railway.json` me `Dockerfile` kar do |

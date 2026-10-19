# 🚂 RAILWAY — 30 DIN, BINA API KEY (sirf ye follow karo)

## Step 1 — GitHub
```bash
cd private-agent
git init && git add . && git commit -m "SuperAgent"
git remote add origin https://github.com/TUMHARA_NAAM/superagent.git
git push -u origin main
```

## Step 2 — Railway
1. [railway.app](https://railway.app) → **New Project**
2. **Deploy from GitHub repo** → apna repo
3. Build automatic start ho jayega (`railway.json` → `Dockerfile.slim`)

## Step 3 — Sirf 2 variables
Railway → service → **Variables** → **Raw Editor**:

```env
APP_PASSWORD=meraagent123
DATA_DIR=/data
```

> `GROQ_API_KEY` **nahi chahiye**. App keyless mode chalayega (Pollinations, GPT-OSS 20B).

## Step 4 — Volume (optional, chats save rakhne ke liye)
**Settings → Volumes → Add Volume → Mount path: `/data`**

> Bina volume: chats restart pe ud jayengi (app phir bhi chalega — fallback `/tmp/data` hai)
> Volume ke saath bhi agar permission issue aaye, app khud `/tmp/data` pe gir jayega — crash nahi hoga.

## Step 5 — Domain
**Settings → Networking → Generate Domain**
→ `https://superagent-xxxx.up.railway.app`

## Step 6 — Kholo
Password: `meraagent123` (jo Step 3 me daala)

Badge me dikhega: **`🆓 free · pollinations · openai-fast`** = chal raha hai, koi key nahi.

---

## ⏱️ Speed ka sach
Har step pe **25–30 sec** wait dikhega (`⏳`). Ye Pollinations ka free limit hai (30s/IP).
Slow lage to baad me **ek** variable add kar dena — turant fast ho jayega:

```env
GROQ_API_KEY=gsk_...      # console.groq.com/keys — free, 2 min
```

---

## 📅 30 din baad
$5 credit khatam → service band. Us waqt:
- **Render free** (no card, hamesha free) → `render.yaml` repo me ready hai
- **Oracle** (card, 12 GB, Ollama bhi) → `deploy/setup-vm.sh`
- **Laptop + tunnel** (no card, Ollama) → `deploy/start-public.sh`

---

## 🩺 Agar deploy fail ho

| Error | Fix |
|---|---|
| Build fail | Logs dekho; `railway.json` me `Dockerfile.slim` hona chahiye |
| `Application failed to respond` | Healthcheck `/healthz` — 120s tak wait karo, first boot slow |
| Login pe kuch na ho | Sandbox iframe cookies block karti hai — URL me `?t=` token mode hai |
| `No provider` | Koi baat nahi, reload karo — keyless auto-on hai |
| Chats gayab | Volume `/data` mount karo |
| Java/C++ nahi chalta | Slim image me sirf Python+JS hai (RAM bachane ke liye) |

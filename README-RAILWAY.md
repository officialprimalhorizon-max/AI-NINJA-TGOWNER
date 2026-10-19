# 🥷 SuperAgent — Railway pe deploy (Ninja AI jaisa)

Yahi wo app hai: **multi-chat, apna workspace, terminal + 10 languages, streaming, artifact preview, ZIP download, login**.
Railway pe 5 minute me live ho jayega.

---

## 📦 Railway pe deploy — step by step

### 1) GitHub pe daalo
```bash
cd private-agent
git init
git add .
git commit -m "SuperAgent"
# GitHub pe naya repo banao, phir:
git remote add origin https://github.com/TUMHARA_NAAM/superagent.git
git push -u origin main
```
> `.env`, `data/` push nahi honge (`.gitignore`/`.dockerignore` me hain) — sahi hai.

### 2) Railway project
1. [railway.app](https://railway.app) → **New Project**
2. **Deploy from GitHub repo** → apna repo chuno
3. Railway khud **Dockerfile** detect kar lega (`railway.json` me set hai)

### 3) Variables — sirf 3 cheezein

Railway → service → **Variables** → **Raw Editor** me paste karo:

```env
APP_PASSWORD=change-this-to-strong-password
SECRET_KEY=change-this-to-40-random-hex-characters
DATA_DIR=/data
```

**AI ke liye 2 options:**

| Option | Kya karo | Speed | Limit |
|---|---|---|---|
| **A. Groq (recommended)** | `GROQ_API_KEY=gsk_...` add karo — free, 2 min | ⚡ **1-2 sec** | 30 req/min, 1000/day |
| **B. Keyless** | kuch mat daalo | 🐢 30s/step | kuch nahi (free forever) |

Groq key: `console.groq.com/keys` → Google login → Create API Key.
Poora template: **`railway.env.example`** file me hai.

> 💡 Key daalne se agent **pehle Groq** try karega, limit khatam → **Gemini** → phir **Pollinations**. Kabhi nahi rukta.

### 4) Volume (chats save rakhne ke liye)
Service → **Settings → Volumes → Add Volume** → mount path: **`/data`**

> Bina volume ke, har redeploy pe chats/files **delete** ho jayenge (container ephemeral hota hai).

### 5) Domain banao
Service → **Settings → Networking → Generate Domain** → `https://superagent-xxxx.up.railway.app`

### 6) Kholo
Browser me domain → **login page** → `APP_PASSWORD` daalo → chat shuru 🎉

Healthcheck: `https://your-app.up.railway.app/healthz` → `ok`

---

## 💰 Railway ka sach (important)

| Plan | Price | RAM | Kaam karega? |
|---|---|---|---|
| **Free Trial** | $5 credit, 30 din | 1 GB | ✅ aaram se |
| **Free** | $0 + $1 credit/month | **0.5 GB** | ⚠️ chalega, par code compile (Java/C++) me tight |
| **Hobby** | $5/month | 48 GB tak | ✅ best |

**Note:** Railway pe **local AI model nahi chalega** (0.5–1 GB RAM). Wahan **keyless Pollinations mode** chalta hai — zero cost.
Bilkul local + unlimited chahiye to apne laptop pe `python agent.py --provider ollama` chalao.

**Bilkul ₹0 chahiye to:** Railway ki jagah **Oracle Cloud Always Free VM** (1–4 CPU, **24 GB RAM**, hamesha free) le lo — wahan local model bhi chal jayega.

---

## 🐛 Login issue (sandboxed preview / iframe)

Agar login button dabane pe kuch na ho, to reason hamesha ek hi hota hai: **cookies block hain**
(sandboxed iframe me cookies set nahi hoti) → server login ke baad wapas `/login` bhej deta hai → loop.

Do fixes already code me hain:

| Mode | Kaise | Kab use karo |
|---|---|---|
| **`NO_AUTH=1`** | login poora skip | Preview/sandbox, local testing |
| **Token login** | `POST /login` JSON → `{token}` → `/?t=TOKEN` (cookie ki zaroorat nahi) | Railway + iframe dono |

```bash
# preview / bina login
NO_AUTH=1 PORT=5000 python server.py

# normal (password + token fallback)
APP_PASSWORD=meraagent python server.py
```

Deploy pe **`NO_AUTH` mat lagao** — wahan `APP_PASSWORD` hi sahi hai.


---

## 💰 Railway ka asli kharcha (honest)

| Plan | Price | RAM | Hamara app fit? |
|---|---|---|---|
| **Trial** | $5 credit, 30 din, card nahi | 1 GB | ✅ aaram se |
| **Free** | $0 + **$1 credit/month** | 0.5 GB | ⚠️ **bas fit** — idle ~100 MB |
| **Hobby** | **$5/month** (usme $5 usage included) | 48 GB tak | ✅ comfortable |

**Math (measured):** hamara app idle pe **~77-110 MB RAM** leta hai.
Railway ka rate $10/GB/month → 0.1 GB ≈ **$1/month** = free credit ke barabar.
Thoda traffic + build time judne pe $1 se upar ja sakta hai → tab **Hobby $5** lagega.

**Sach:** Railway "hamesha free" nahi hai — Free plan me bas ek chhota service chalta hai.
24/7 bina paisa chahiye to **Oracle (card)** ya **laptop + tunnel (no card)** hi option hai.

---

## 🚫 Railway pe Ollama nahi chalega

| | Railway | Laptop / Oracle VM |
|---|---|---|
| Ollama (local model) | ❌ 0.5 GB RAM | ✅ 8-12 GB |
| API key chahiye | ✅ haan (ya keyless slow) | ❌ nahi |
| Speed | ⚡ Groq se | ⚡ model pe depend |
| 24/7 | ✅ | laptop: ❌ · Oracle: ✅ |
| Cost | $1-5/month | ₹0 |

**Matlab:** Railway = **app** ke liye best, **model** ke liye nahi.
Fast chahiye Railway pe → **Groq free key** daalo (1-2 sec). Wo Ninja AI jaisa hi fast lagega.

---

## 🔐 Security (zaroori padho)

Agent ke paas **terminal** hai. Public internet pe mat chhodo bina password ke:
- ✅ `APP_PASSWORD` strong rakho (8+ chars, random)
- ✅ HTTPS Railway se automatic milta hai
- ✅ Container `agent` (non-root) user pe chalta hai
- ⚠️ Ye **ek user ka tool** hai — public signup/multi-user nahi hai
- ⚠️ Bahut zyada sensitive data mat daalo — free AI APIs prompts log kar sakti hain

---

## 🧪 Deploy se pehle local test

```bash
pip install -r requirements.txt
APP_PASSWORD=admin python server.py
# -> http://localhost:5001  (login: admin)
```

Docker se (Railway jaisa hi):
```bash
docker build -t superagent .
docker run -p 8080:8080 -e APP_PASSWORD=admin -e GROQ_API_KEY=gsk_xxx -v $(pwd)/data:/data superagent
```

---

## 🩺 Troubleshooting

| Problem | Fix |
|---|---|
| Deploy fail — image big | Dockerfile se `default-jdk-headless` hata do (~300 MB bachega) |
| Badge pe "free · pollinations" | Ye sahi hai — bina key chal raha hai. Tez chahiye to `GROQ_API_KEY` daalo |
| Jawab 30-60s late | Free tier ka 30s/IP limit hai. Agent khud wait karta hai. Groq key se instant |
| Chat bhejte hi 500 | Logs dekho (Railway → Deployments → View Logs) |
| Chats gayab ho gayi redeploy pe | Volume `/data` mount nahi hai |
| Java/C++ compile OOM | Free plan 0.5 GB — Hobby lo ya woh languages hata do |
| Login loop | Cookies block hain / password galat |

---

## 📁 File tree (deploy)

```
private-agent/
├── server.py          # ← Railway isko chalata hai (gunicorn server:app)
├── agent.py           # agent core: tools + provider pool
├── Dockerfile         # python + node + java + gcc + lua + php + ruby
├── railway.json       # builder + healthcheck
├── requirements.txt   # flask, gunicorn, openai...
└── .dockerignore
```

| File | Kya |
|---|---|
| `Dockerfile.slim` | **Railway isko use karta hai** — Python + Node only, ~280 MB, idle ~100 MB RAM |
| `Dockerfile` | Full multi-language (Java, C/C++, Rust, Go, PHP, Ruby) — VPS/local ke liye |
| `railway.env.example` | Variables ka ready template |

**Slim image me sirf Python + JavaScript code chalega.** Java/C++ chahiye to `railway.json` me
`"dockerfilePath": "Dockerfile"` kar do — par build 4x slow aur image ~1.2 GB ho jayegi (free plan pe tight).

Purane files (`webapp.py`, `auto.py`, `doctor.py`, `host.py`, `deploy/`) local use ke liye hain — deploy me include ho sakte hain.

---

## ⚡ Deploy ke baad try karo

```
ek portfolio website banao — 3 pages, dark theme, mobile friendly
```
```
C++ me prime numbers nikaalo 1-100 tak, chala ke dikhao
```
```
sales.csv banao dummy data se aur usme se monthly chart nikaalo
```
Agent khud files banayega → right panel **📁 Files** → HTML pe click → **live preview**.
Sab kuch **⬇ ZIP** se download ho sakta hai.

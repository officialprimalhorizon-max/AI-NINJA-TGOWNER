# 🤖 Mera Agent — apna AI, zero restriction

Tumhara apna agent. **Tumhare computer pe** chalta hai, tumhari keys use karta hai, koi company beech me nahi.

- 💬 Chat (Hinglish/English)
- 📁 **Workspace** me files banana, padhna, list karna
- 🐍 **Python code khud likhna aur chalana**
- 🌐 Web page fetch karna
- 🔁 **Multi-step kaam** — ek instruction do, poora ho jayega
- 🖥️ **Web UI** (ChatGPT jaisa) + CLI dono
- ⏰ **AUTO MODE** — schedule pe khud chalta hai, folder me file aayi to khud process karta hai

---

## 🎯 YE KYA KYA KAR SAKTA HAI (jo tum "bas bolo" kar sakte ho)

### 📂 Files ka kaam — sabse zyada useful
- "**Downloads folder saaf karo** — images, PDFs, videos alag-alag folders me daalo"
- "**Saari photos date ke hisaab se rename karo** (IMG_1234.jpg → 2026-10-19-001.jpg)"
- "**10 PDFs ko ek PDF me merge karo**"
- "**Is image ka size 200KB se kam karo**"
- "**Word file ko PDF me convert karo**"
- "inbox me jo files hain, sabka summary banao"

### 📊 Data aur Excel
- "**sales.csv analyze karo** — top products, monthly trend, chart banao"
- "**3 Excel files ko ek me merge karo**, duplicate hatao"
- "**monthly report banao Excel me** — formulas ke saath"
- "**CSV ko clean karo** — missing values, galat dates fix karo"

### 📝 Document aur content
- "**Mera resume banao** — [details] ke saath, PDF me"
- "**Leave application likho** — manager ko, formal tone"
- "**10 page ka project report banao** — headings, tables ke saath"
- "**Presentation banado** — 8 slides, topic: [X]"
- "Hindi ↔ English translate karo, poora document"

### 🌐 Website / code
- "**Portfolio website banao** — 3 pages, mobile-friendly"
- "**Ek calculator/todo app banao** HTML me"
- "**Ye error fix karo** — mera code chal nahi raha"
- "**Python script likho** jo folder ki saari images resize kare"
- "**Landing page banao** ek product ke liye"

### 🔎 Research aur internet
- "**Is topic pe research karo** — 5 sources se, report banao"
- "**Is URL ka summary do**"
- "**Competitor ke prices compare karo** — table banao"
- "**YouTube/article ka notes banao**"

### ⏰ AUTOMATIC (tum kuch na karo)
- "**Roz subah 8 baje** AI news summary banao" → schedule
- "**Inbox me file daali to** auto summary bana do" → watch folder
- "**Har roz** ek diary note likho"
- "**Har hafte** backup report banao"

> Dhyan rakho: local 8B model **simple-medium kaam** acche karta hai. Bahut complex
> multi-step kaam me galti kar sakta hai — tab Groq/Gemini key use karo ya bada model
> (`qwen3:14b`, 16 GB RAM chahiye).


---

## 💻 MULTI-LANGUAGE + APNA TERMINAL

Agent sirf Python nahi — **13 languages** me code likh sakta hai, compile kar sakta hai, chala sakta hai, aur error aaye to khud fix karke dobara chala sakta hai.

| Language | Kaise chalti hai | Install (Windows) |
|---|---|---|
| Python | built-in | `winget install Python.Python.3.12` |
| JavaScript | Node.js | `winget install OpenJS.NodeJS.LTS` |
| Java | javac + java | `winget install EclipseAdoptium.Temurin.21.JDK` |
| C | gcc | `winget install BrechtSanders.WinLibs.POSIX.UCRT` |
| C++ | g++ (C++17) | same as C |
| C# | dotnet | `winget install Microsoft.DotNet.SDK.8` |
| Lua | lua | `winget install DEVCOM.Lua` |
| Go | go | `winget install GoLang.Go` |
| Rust | rustc | `winget install Rustlang.Rustup` |
| PHP | php | `winget install PHP.PHP` |
| Ruby | ruby | `winget install RubyInstallerTeam.Ruby` |
| Bash | bash | Git Bash ke saath |
| PowerShell | powershell | Windows me built-in |

**Kya-kya ready hai — check karo:**
```bash
python doctor.py
python doctor.py --install-hint lua     # kisi bhi language ka install command
```

**Terminal (`run_shell`)** — agent ke paas apna shell hai:
```bash
npm install express        # packages install
pip install pandas
git init && git add . && git commit -m "first"
ffmpeg -i in.mp4 out.mp3   # video/audio convert
zip -r backup.zip folder/
python script.py
```
Workspace folder me chalta hai, 120s tak chal sakta hai, aur **khatarnak commands blocked** hain (`rm -rf /`, `mkfs`, `shutdown` etc.).

---

## 🌍 HOSTING — FREE ME HO SAKTI HAI

```bash
python host.py --guide        # poori list
python host.py                # local server  -> http://localhost:8080
python host.py --tunnel       # FREE public URL (cloudflared), no account
```

| Kya host karna hai | Free option | Limit |
|---|---|---|
| **Static site** (HTML/CSS/JS) | GitHub Pages, Cloudflare Pages, Netlify Drop, Vercel | ♾️ hamesha free |
| **Python/Node app** (PC on rehna chahiye) | `python host.py --tunnel` (Cloudflare Tunnel) | ♾️ free, random URL |
| **24/7 server** (PC band ho to bhi) | **Oracle Cloud "Always Free" VM** — 1-4 CPU, 24 GB RAM | ♾️ hamesha free |
| ML demo | HuggingFace Spaces (CPU) | free tier |

> 💡 **₹0 me 24/7 agent:** Oracle free VM pe `private-agent` chalao + Cloudflare Tunnel.
> VM pe 24 GB RAM hai, to `qwen2.5-coder:14b` bhi chal jayega — laptop ka load zero.

---

## 🧠 8 GB RAM KE LIYE MODEL (tumhara case)

```bash
ollama pull qwen2.5-coder:3b     # ~2 GB — CODING ke liye best
ollama pull qwen3:4b             # ~2.5 GB — general kaam
python agent.py --provider ollama
```

| Model | Size | Kaisa hai |
|---|---|---|
| `qwen2.5-coder:3b` | ~2 GB | ⭐ Coding (Python/C++/JS) ke liye best, 8GB pe smooth |
| `qwen3:4b` | ~2.5 GB | General baat-cheet + simple kaam |
| `qwen2.5-coder:7b` | ~4.7 GB | Better code, par 8GB pe tight — browser band rakho |
| ~~14B+~~ | 9 GB+ | ❌ 8GB pe mat chalao, swap hoke dead slow |

**Speed tip:** 8 GB pe `OLLAMA_NUM_PARALLEL=1` aur `OLLAMA_MAX_LOADED_MODELS=1` set karo.

**Honest baat:** 3B model **simple-medium code** acche se likhta hai (calculator, script, CRUD, file tools).
Bahut bada project (multi-file app, complex bug) me galti karega. Uske liye:
- free Groq/Gemini key (fast + smart), **ya**
- Oracle free VM pe 14B model.


---

## ⚡ SPEED — Ninja AI jaisi fast (important)

**Sach ye hai:** slow hone ki wajah hosting nahi, **model** hai.
Keyless Pollinations = 30 sec/IP throttle (free by design). Isko hosting badal ke fix nahi kar sakte.

| Setup | Speed | Limit | Cost |
|---|---|---|---|
| Pollinations (keyless) | 🐢 30s/step | 30s me 1 req/IP | ₹0 |
| **Groq free key** | ⚡⚡⚡ instant (~1-2s) | 30 req/min, 1000/day | ₹0 |
| Gemini free key | ⚡⚡ fast | generous daily | ₹0 |
| Ollama local (7B) | ⚡ fast | ♾️ unlimited | ₹0 |

### Fastest free setup (2 minute, recommended)

1. **console.groq.com/keys** → Google login → **Create API Key** → copy (`gsk_...`)
2. SuperAgent UI me **⚙ Key** dabao → provider `groq` → key paste → Save
3. Badge me `groq` dikhega → ab **1-2 second me jawab**, koi wait nahi

> Agent ka pehle Groq try karta hai. Groq ki limit khatam → khud Gemini → phir
> Pollinations pe fallback. Isliye **kabhi rukta nahi**.

### Streaming (naya)
Jawab ab **token-by-token** aata hai — pehla shabd turant dikhta hai,
poora jawab aane ka intezaar nahi. Perceived speed bahut zyada.

### Multi-key (zero downtime)
```env
GROQ_API_KEY=gsk_key1,gsk_key2,gsk_key3
```
Limit aate hi agent khud agla key use karta hai.


---

## 💸 "FREE" ka sach — trial vs asli free (Oct 2026)

**Railway free NAHI hai** — $5 credit sirf **30 din** ka trial hai, uske baad $1/month credit
me kuch nahi chalta. Practically Railway = **$5/month**. Tumne sahi pakda.

| Platform | Asli free? | Card | RAM | Ollama | Catch |
|---|---|---|---|---|---|
| **Laptop + Cloudflare Tunnel** | ✅ **hamesha** | ❌ **nahi** | tumhara 8 GB | ✅ **haan** | laptop on rakhna |
| **Render (free web service)** | ✅ **hamesha** | ❌ **nahi** | 512 MB | ❌ | 15 min idle pe sota, ~1 min cold start |
| **GitHub Codespaces** | ✅ 60 hrs/month | ❌ nahi | 4-8 GB | ✅ haan | 60 ghante/month limit |
| **Oracle Always Free** | ✅ hamesha | ✅ **card verify** | 2 OCPU / 12 GB | ✅ haan | card chahiye, capacity milna mushkil |
| Railway | ❌ **trial ($5, 30 din)** | ❌ | 0.5 GB | ❌ | baad me $5/month |
| HuggingFace Spaces | ⚠️ static only | ❌ | 16 GB | ❌ | Jul 2026 se compute Space **paid** |
| Koyeb / Fly.io | ❌ band | — | — | — | free plan khatam |

### 🥇 Render — bina card, hamesha free (app ke liye)

`render.yaml` repo me ready hai — **Blueprint deploy**:

1. GitHub pe repo push karo
2. [render.com](https://render.com) → New → **Blueprint** → repo chuno (`render.yaml` auto-detect)
3. Variables: `APP_PASSWORD` (Render khud bana dega) + `GROQ_API_KEY` (free, 1-2 sec speed)
4. Deploy → `https://superagent-xxx.onrender.com`

- ✅ Card nahi, trial khatam nahi hota
- ✅ 750 instance-hours/month ≈ poora mahina
- ⚠️ 15 min bina traffic → sota hai, pehla request ~1 min
- ⚠️ Free plan me **persistent disk nahi** → redeploy pe chats/files reset
- ⚠️ 512 MB RAM → Ollama nahi, par keyless/Groq dono chalte hain

### 🥈 Laptop + Tunnel — Ollama ke saath, 100% free

```bash
ollama pull qwen2.5-coder:3b
bash deploy/start-public.sh --model qwen2.5-coder:3b
# -> ✅ https://xxx.trycloudflare.com
```

- ✅ Na card, na account, na trial
- ✅ **Ollama** chalta hai (unlimited, no API key, tumhara CPU)
- ⚠️ Laptop on rakhna padega

---

## 🌍 FREE HOSTING — kahan karu? (Oct 2026)

| Platform | Free tier | Ollama chalega? |
|---|---|---|
| **Oracle Cloud Always Free** | **2 ARM OCPU + 12 GB RAM**, 200 GB disk, hamesha | ✅ **haan** — 🥇 best |
| Render free | 512 MB RAM, 15 min pe so jata | ❌ |
| Railway free | 0.5 GB RAM | ❌ (sirf cloud key mode) |
| Koyeb | Feb 2026 se free plan band | ❌ |
| Fly.io | free tier Oct 2024 me band | ❌ |
| Tumhara laptop + Cloudflare Tunnel | unlimited | ✅ (laptop on rehna chahiye) |

> Oracle ne Jun 2026 me free ARM tier **aadha** kar diya (4/24 → **2 OCPU / 12 GB**).
> Isse zyada banao to instance terminate ho jayega.

**Poori step-by-step guide:** [`deploy/README-OLLAMA-HOSTING.md`](deploy/README-OLLAMA-HOSTING.md)
**One-command VM setup:** `bash deploy/setup-vm.sh` (Ollama + model + systemd + firewall + password)

```bash
# VM pe (Ubuntu 24.04, Ampere A1 2 OCPU/12GB)
scp -r private-agent ubuntu@VM_IP:~
ssh ubuntu@VM_IP
cd private-agent && bash deploy/setup-vm.sh
# -> http://VM_IP:5000  (password script print karega)
```

---

## 🩺 DOCTOR

```bash
python doctor.py
```
Batata hai: RAM, disk, kaunsi languages installed hain, kaunse tools missing hain (git, ffmpeg, pandoc), Python packages, Ollama models, aur tumhare RAM ke hisaab se model suggestion.

---

## ⏰ AUTO MODE — always-on agent

Ye tumhare agent ko "employee" bana deta hai. Tum so bhi sakte ho, ye kaam karta rahega.

```bash
python auto.py            # daemon chalu (Ctrl+C se band)
python auto.py --list     # kaunse kaam set hain
python auto.py --run morning-news   # ek job abhi chalao
python auto.py --test     # sab theek hai?
```

Pehli baar chalane pe `tasks.json` ban jayegi. Usme `"enabled": true` kar do:

```json
{
  "watch_seconds": 5,
  "schedules": [
    {
      "name": "morning-news",
      "at": "08:00",
      "prompt": "Aaj ki top 5 AI news dhoondo aur reports/news-{date}.md me save karo.",
      "enabled": true
    },
    {
      "name": "daily-diary",
      "every_minutes": 1440,
      "prompt": "workspace/diary-{date}.md me 5 line ka note likho.",
      "enabled": true
    }
  ],
  "watch": [
    {
      "name": "inbox-process",
      "folder": "inbox",
      "prompt": "Is file ko padho: {file}\nSummary banao aur outbox/{stem}.md me save karo.",
      "enabled": true
    }
  ]
}
```

**Kaise chalta hai:**
- `at: "08:00"` → roz us time
- `every_minutes: 60` → har ghante
- `watch` → `workspace/inbox/` me file daalo, result `workspace/outbox/` me aa jayega
- Log: `logs/auto.log`

**Always-on rakhne ke liye (laptop band hone pe bhi chale):**
```bash
# Linux/Mac (cron)
crontab -e
# add:  @reboot cd /path/to/private-agent && python3 auto.py >> logs/boot.log 2>&1
```
Windows: Task Scheduler → "At startup" → `python auto.py`

---


## 🚀 3 tarike — jo pasand aaye

### ✅ Tarika 1 — UNLIMITED + 100% FREE (local, koi limit nahi)

Ye **asli "no restriction"** hai. Model tumhare computer pe chalta hai. Na key, na daily limit, na bill, na data leak.

```bash
# 1) Ollama install: https://ollama.com/download
# 2) Model download (ek hi baar, ~5 GB)
ollama pull qwen3:8b

# 3) Chalao
python agent.py --provider ollama
```

**Kitna RAM chahiye:** 8B model → 8–10 GB RAM. Kam hai to `qwen3:4b` (4 GB) ya `llama3.2:3b` (3 GB).
**Speed:** chhote model dheere chalte hain par **kabhi limit nahi aati**.

---

### 🆓 Tarika 0 — BINA API KEY (bilkul free, keyless)

Koi key nahi, koi signup nahi. Bas chalao:

```bash
python agent.py
```

Andar **Pollinations** (GPT-OSS 20B, tool calling ✅) chalta hai — anonymous tier.
Limit: 30 sec me 1 request per IP — agent khud `⏳ wait` karke retry karta hai.

- ✅ Key/signup: zero
- ⚠️ Speed: 30-60s per step (free tier)
- 🔐 Data: Pollinations ke server se hoke jaata hai

Tez chahiye to Tarika 2 (free keys) ya Tarika 1 (local) use karo — agent **automatically** key wale provider ko pehle try karta hai aur fail hone pe Pollinations pe gir jaata hai.

---

### ⚡ Tarika 2 — FREE cloud keys + auto-rotation

Fast models (Groq/Gemini) free tier pe. Daily limit hoti hai — **isliye agent me multi-key rotation hai**:

```env
# .env me 3-4 keys comma se daal do (har account se ek)
GROQ_API_KEY=key1,key2,key3,key4
GEMINI_API_KEY=gemini_key1,gemini_key2
```

Ek key ki limit khatam → agent **khud agla key** use karega → wo bhi khatam → **agla provider**.
Practically: jab tak pool me keys hain, kaam rukega nahi.

```bash
python agent.py                # sab configured keys rotate karega
python agent.py --provider groq
```

**Free keys:**

| Provider | Limit | Card | Link |
|---|---|---|---|
| **Groq** | 30 req/min, ~1,000 req/day | ❌ | https://console.groq.com/keys |
| **Gemini** | generous daily quota | ❌ | https://aistudio.google.com/apikey |
| **OpenRouter** | 20 req/min, 50 req/day | ❌ | https://openrouter.ai/keys |
| **Mistral** | free Experiment tier | ❌ | https://console.mistral.ai/api-keys |

---

### 🖥️ Tarika 3 — Web UI (ChatGPT jaisa)

```bash
python webapp.py          # ya: python app.py
# browser me kholo: http://localhost:5000
```

UI me:
- Chat window + live tool activity (`🔧 write_file · hello.html`)
- **Right side me workspace files** — click karke preview
- **⚙ Settings** — provider chuno, key paste karo (UI se hi save ho jati hai)
- Ollama mode bhi UI se select ho jata hai

> 🔒 Key `.env` me **tumhare computer pe** save hoti hai, kahin upload nahi hoti.
> Key leak ho jaye to us provider ke console se delete kar do — 10 second ka kaam.

---

## ⚡ Setup (3 minute)

```bash
cd private-agent
pip install -r requirements.txt     # ya: bash setup.sh
cp .env.example .env
```

`.env` me apna provider + key:

```env
PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxx
```

Chalao:

```bash
python agent.py
```

---

## 🎯 Use kaise karo

```bash
python agent.py " ek calculator banao HTML me, calculator.html me save karo "
python agent.py "dummy sales data banao aur chart nikaalo"
python agent.py "mere liye 3-page portfolio website banao"
python agent.py "is folder ki files ki summary do"
```

Files yahan banti hain: `private-agent/workspace/`

**Kahan se key milegi — reminder:**
```bash
python agent.py --setup
```

---

## 🔐 Privacy — kya kahan jaata hai

| Mode | Data kahan jaata hai |
|---|---|
| **Ollama (local)** | ❌ Kahin nahi. Sab tumhare computer pe. |
| Groq/Gemini/OpenRouter free | Provider ke server pe (wo training pe use kar sakte hain) |
| DeepSeek | Provider ke server pe + paid |

Sabse zyada privacy chahiye → **Ollama**.

---

## 🛠️ Naya tool add karna (30 second)

`agent.py` me `TOOLS` list me ek entry add karo, aur `REGISTRY` me function:

```python
def tool_send_whatsapp(number: str, msg: str) -> str:
    ...
    return "sent"

REGISTRY["send_whatsapp"] = tool_send_whatsapp
```

Bas — agent us tool ko khud use karna seekh jayega.

---

## 🐛 Common errors

| Error | Matlab | Fix |
|---|---|---|
| `Koi provider configured nahi` | Na key, na Ollama | Key daalo ya `--provider ollama` |
| `401 / invalid_api_key` | Key galat | `.env` check karo, space/quotes hatao |
| `402 / Insufficient Balance` | Key valid, paisa nahi | Top-up, ya Groq/Gemini use karo |
| `429` | Limit | Auto-rotate chalega; pool khali to key aur daalo |
| `404 model not found` | Model ID badal gaya | `--model naya-id` |
| Ollama se `connection refused` | Ollama band hai | `ollama serve` chalao |
| Auto mode kuch nahi kar raha | Jobs `"enabled": false` hain | `tasks.json` me `true` karo, `python auto.py --list` se check |

---

## 📂 Structure

```
private-agent/
├── agent.py          # core agent (tools + provider pool + CLI)
├── webapp.py         # web UI (Flask, single file)
├── auto.py           # ALWAYS-ON mode: schedule + watch folder
├── doctor.py         # system check + install hints
├── host.py           # free hosting (local server + cloudflared tunnel)
├── tasks.json        # auto mode ki settings (pehli baar auto-bane)
├── setup.sh          # one-command setup
├── .env.example      # keys daalne ki jagah
├── requirements.txt
├── README.md
└── workspace/
    ├── inbox/        # yahan file daalo → auto process
    └── outbox/       # results yahan aayenge
```

---

## ⚠️ Safety

- `.env` GitHub pe **kabhi** push mat karo (`.gitignore` me hai)
- Internet pe mili "free API key" **kabhi** use mat karo — wo kisi aur ki key hoti hai, tumhare prompts uske account me jaate hain
- `run_python` tumhare user permissions pe chalta hai — untrusted code mat chalwao

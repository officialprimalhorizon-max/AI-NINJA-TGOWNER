# ⚡ SPEED — Ollama ko fast karna (96-core box)

Tumhare box pe **CPU inference** hota hai (GPU nahi). CPU pe speed 4 cheezon pe depend karti hai:

| Setting | Default | Fast value | Kya karta hai |
|---|---|---|---|
| `OLLAMA_NUM_CTX` | 4096 | **2048–4096** | Chhota context = tez prompt processing |
| `OLLAMA_NUM_THREAD` | auto | **16–24** | 96 core pe sab dene se thrashing — memory bandwidth bottleneck |
| `OLLAMA_NUM_PREDICT` | 1400 | **1200–1600** | Model rambling nahi karega |
| `OLLAMA_KEEP_ALIVE` | 5m | **-1** | Model RAM me pinned — cold start khatam |

---

## 1️⃣ Ollama server flags (systemd / manual)

```bash
# manual serve
OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 \
  nohup ollama serve > /tmp/ollama.log 2>&1 &
```

> `OLLAMA_NUM_PARALLEL=1` — ek waqt me ek hi request = poori CPU ek kaam pe.
> Multi-user nahi ho to ye best hai.

### systemd (permanent)
```bash
systemctl edit ollama
```
```ini
[Service]
Environment="OLLAMA_KEEP_ALIVE=-1"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
```
```bash
systemctl daemon-reload && systemctl restart ollama
```

---

## 2️⃣ App-side tuning (`.env`)

```env
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_THREAD=24
OLLAMA_NUM_PREDICT=1400
```

`agent.py` ye `extra_body.options` ke through Ollama ko bhejta hai.

**`num_thread` kaise chuno:**
```bash
# cores / 4 ka approx — 96 core pe 24
OLLAMA_NUM_THREAD=24
```
Agar response slow lage aur CPU 100% pe ho, thread **kam** karo (16, 12, 8) — zyada nahi.
Memory bandwidth bottleneck hai, cores nahi.

---

## 3️⃣ Model choice (sabse bada asar)

| Model | Size | Speed (CPU, ~96 core) | Quality |
|---|---|---|---|
| `qwen2.5-coder:1.5b` | 1.0 GB | **60–90 tok/s** ⚡⚡ | basic |
| `qwen2.5-coder:3b` | 1.9 GB | **30–50 tok/s** ⚡ | decent |
| **`qwen2.5-coder:7b`** | 4.7 GB | **12–22 tok/s** ✅ | **best balance** |
| `qwen2.5-coder:14b` | 9.0 GB | 6–10 tok/s | best code |
| `qwen2.5-coder:32b` | 19 GB | 2–4 tok/s 🐢 | overkill |

Tumhare 322 GB RAM pe 32b bhi fit hai, par **7b hi rakho** — interactive use ke liye 12-22 tok/s theek hai.

**Agar 7b slow lage:** 3b try karo (2.5x fast, quality 80%).

```bash
ollama pull qwen2.5-coder:3b
# .env me:
AGENT_MODEL=qwen2.5-coder:3b
```

---

## 4️⃣ Quantization (advanced)

Default `Q4_K_M` hai — best balance. Faster chahiye:

```bash
# Q4_0 = thoda fast, thoda kam accurate
ollama pull qwen2.5-coder:7b-instruct-q4_0

# ya custom Modelfile se num_ctx fix karo
```

---

## 5️⃣ Real speed test

```bash
# Ollama direct — tok/s dekho
ollama run qwen2.5-coder:7b --verbose "write a python hello world"
# output me: eval rate: XX.XX tokens/s
```

```bash
# App ke through
time curl -s localhost:8000/api/chat -H 'Content-Type: application/json' \
  -d '{"chat_id":"test","task":"say hi"}'
```

**Target:** 7b pe **15+ tok/s** = 100 words ~7 second. Theek hai.

---

## 📊 Kyun slow ho sakta hai

| Symptom | Reason | Fix |
|---|---|---|
| 2 tok/s | `num_thread` bahut zyada | 24 → 16 → 12 try karo |
| 5 tok/s | model RAM me nahi (cold) | `KEEP_ALIVE=-1` |
| 8 tok/s | context 4096+ bada | `NUM_CTX=2048` |
| First response bahut slow | model load ho raha | preload: `curl` `api/generate` `num_predict:1` |
| Har step 30s+ | Pollinations use ho raha | `.env` me Ollama URL check karo |

---

## 🎯 Recommended full config

**Ollama:**
```bash
OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 ollama serve
```

**`.env`:**
```env
AGENT_MODEL=qwen2.5-coder:7b
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_KEEP_ALIVE=-1
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_THREAD=24
OLLAMA_NUM_PREDICT=1400
```

**Preload (ek baar):**
```bash
curl -s localhost:11434/api/generate -d '{"model":"qwen2.5-coder:7b","prompt":"hi","stream":false,"keep_alive":-1,"options":{"num_predict":1}}'
```

Isse: **first token ~0.4s, phir 15-20 tok/s steady.**

---

## 🔥 Bonus — Groq fallback (cloud, 100x fast)

Ollama se bhi fast chahiye to `GROQ_API_KEY` daalo:
```env
GROQ_API_KEY=gsk_...
```
Pool order: **Ollama → Groq → Pollinations**
Ollama down ho to Groq (0.3s) le lega — koi downtime nahi.

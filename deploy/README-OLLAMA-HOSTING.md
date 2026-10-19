# 🖥️ Ollama Local + FREE Hosting — poori guide

Tumne bola: **"Ollama local use karna hai"** + **"hosting kis pe karu free"**.
Dono cheezein alag hain, isliye pehle clear:

| Cheez | Kahan chalti hai | Paisa |
|---|---|---|
| **Ollama** (AI model) | Tumhare laptop pe **ya** VM pe | ₹0 |
| **SuperAgent** (app/UI) | Tumhare laptop pe **ya** VM pe | ₹0 |
| **Public URL** (doston ko bhejna) | Cloudflare Tunnel (free) ya VM ka IP | ₹0 |

**Rule:** Jahan Ollama chalega, **app bhi wahin** chalna chahiye — warna har request internet se aayegi aur slow lagegi.

---

## 🚫 CARD NAHI HAI? — ye 3 options (verified Oct 2026)

| Option | Free me | Ollama? | Card/Account | Catch |
|---|---|---|---|---|
| 🥇 **Laptop + Cloudflare Tunnel** | unlimited | ✅ **haan** | ❌ **na card, na account** | Laptop on rehna chahiye |
| Render free | 750 hrs/month, 512 MB | ❌ | ❌ no card | 15 min idle pe so jata; sirf cloud-key mode |
| GitHub Codespaces | 60 hrs/month, 2-core/4-8 GB | ✅ haan | ❌ no card | 60 ghante/month, band karne pe ruk jata |
| HuggingFace Spaces | CPU 16 GB | ⚠️ | ❌ no card | **Jul 2026 se** new Docker/Gradio Space banana **paid** plan chahiye — Static free hai |
| Koyeb / Fly.io | — | — | card / band | free plan khatam |

### ✅ CARD KE BINA 24/7 free + Ollama = sirf ek hi raasta

**Apna laptop hi server banao + Cloudflare Quick Tunnel.**

- **Card:** nahi
- **Account:** nahi (Cloudflare account bhi nahi chahiye)
- **Ollama:** ✅ unlimited, tumhara 8 GB laptop chalayega 3B/7B
- **Public URL:** ✅ `https://xxx.trycloudflare.com`
- **Catch:** laptop on rehna chahiye + URL temporary (process band = URL band)

```bash
# 1) Ollama install (ek baar)
#    Windows: https://ollama.com/download   Mac: brew install ollama
ollama pull qwen2.5-coder:3b      # 8 GB RAM ke liye ye best

# 2) cloudflared install (ek baar)
#    Windows: winget install Cloudflare.cloudflared
#    Mac    : brew install cloudflared

# 3) Ek command — server + tunnel dono
bash deploy/start-public.sh --model qwen2.5-coder:3b
```

Output:
```
✅ PUBLIC URL (free):  https://quiet-marble-otter.trycloudflare.com
Model : qwen2.5-coder:3b (Ollama — local, unlimited, no API key)
```

**Sirf tum khol sako (bina account):** Cloudflare ne Oct 2026 me email-lock add kiya —
```bash
bash deploy/start-public.sh --mail tumhara@email.com
# -> sirf tumhare email ka OTP daal ke hi khulega (koi account nahi banta)
```

---

## 🏆 FREE HOSTING — kaun sahi hai (Oct 2026 ke verified numbers)

| Platform | Free me milta hai | Ollama chalega? | Verdict |
|---|---|---|---|
| **Oracle Cloud Always Free** | **2 ARM OCPU + 12 GB RAM**, 200 GB disk, 10 TB bandwidth, **hamesha** | ✅ **haan** (7B aaram se, 14B tight) | 🥇 **BEST** |
| Render free | 512 MB RAM, 15 min idle pe so jata hai | ❌ nahi | Chat UI ke liye bhi tight |
| Railway free | 0.5 GB RAM, $1/month credit | ❌ nahi | Sirf cloud key wala mode |
| Koyeb | Feb 2026 se naye users ke liye free plan **band** | ❌ | — |
| Fly.io | Free tier **Oct 2024 me band** | ❌ | — |
| HuggingFace Spaces | 2 vCPU / 16 GB (CPU basic) | ⚠️ chal sakta hai par disk ephemeral | Demo ke liye ok |
| **Tumhara laptop + Cloudflare Tunnel** | unlimited | ✅ | Free, par laptop on rehna chahiye |

> ⚠️ **Oracle ne June 2026 me free tier aadha kar diya** — pehle 4 OCPU / 24 GB tha, ab **2 OCPU / 12 GB**.
> 18 Aug 2026 se isse zyada wale instances **terminate** ho rahe hain. To 2/12 hi banao.

**Bottom line:** 24/7 free hosting ke liye **Oracle Cloud Always Free hi ek hi asli option hai.**

---

## 🅰️ Plan A — Oracle VM pe Ollama + agent (24/7, recommended)

Laptop band ho jaye to bhi chalta rahega. 12 GB RAM me `qwen2.5-coder:7b` aaram se.

### Step 1 — Account
1. [oracle.com/cloud/free](https://oracle.com/cloud/free) → sign up
2. Card verification lagega (₹0 charge, sirf verify) — **prepaid card mat use karna**
3. Region: **Mumbai / Hyderabad** (India se latency kam)

### Step 2 — VM banao
Console → **Compute → Instances → Create Instance**

| Setting | Value |
|---|---|
| Image | **Ubuntu 24.04** (ya 22.04) |
| Shape | **Ampere / VM.Standard.A1.Flex** |
| OCPU | **2** |
| RAM | **12 GB** |
| Boot volume | 50–100 GB |
| SSH key | apni public key upload karo (ya generate) |

> ⚠️ **"Out of capacity"** error common hai. Try karo: doosra region, doosra availability domain, ya 10-15 min baad retry. Free tier users ke liye capacity limited hai — ye Oracle ka sabse bada catch hai.

### Step 3 — App upload karo
```bash
# apne laptop se:
scp -r private-agent ubuntu@VM_IP:~
ssh ubuntu@VM_IP
```

### Step 4 — One command setup
```bash
cd ~/private-agent
bash deploy/setup-vm.sh
```

Ye script khud kar degi:
- ✅ Ollama install + `qwen2.5-coder:7b` pull
- ✅ `OLLAMA_KEEP_ALIVE=-1` (model RAM me hold — **idle reclaim se bacha** + fast)
- ✅ Python venv + dependencies
- ✅ systemd service (boot pe auto-start, crash pe auto-restart)
- ✅ Firewall + random password + `.env`

### Step 5 — Port kholo (Oracle me 2 jagah)
1. **VM ke andar** — script khud kar deti hai (iptables/ufw)
2. **Oracle Console** → Networking → VCN → **Security Lists → Default** → **Add Ingress Rule**:
   - Source: `0.0.0.0/0`
   - Protocol: `TCP`
   - Destination Port: `5000`

### Step 6 — Kholo
```
http://VM_IP:5000
```
Password script ne print kiya hoga. (Dobara dekhna ho: `cat ~/private-agent/.env`)

---

## 🅱️ Plan B — Apne laptop pe Ollama (sabse simple, 0 setup cost)

Free hai, unlimited hai, par **laptop on rehna chahiye**.

```bash
# 1) Ollama install
#    Windows: https://ollama.com/download  (installer)
#    Mac    : brew install ollama
#    Linux  : curl -fsSL https://ollama.com/install.sh | sh

# 2) Model
ollama pull qwen2.5-coder:7b      # 8 GB RAM -> ye best balance
# (ya halka: ollama pull qwen2.5-coder:3b  ~2 GB)

# 3) App
cd private-agent
pip install -r requirements.txt
NO_AUTH=1 python server.py        # http://localhost:5000
```

### Public URL free me (doston ko bhejna ho)
```bash
# Cloudflare Tunnel — free, no account
# Windows: winget install Cloudflare.cloudflared
# Mac    : brew install cloudflared
cloudflared tunnel --url http://localhost:5000
# -> https://random-name.trycloudflare.com
```

Ya app ke andar se:
```bash
python host.py --tunnel
```

---

## 📊 Kaunsa model, kitni RAM

| RAM | Model | Size | Kaisa |
|---|---|---|---|
| **8 GB** (tumhara laptop) | **qwen2.5-coder:3b** | ~2 GB | ✅ smooth, coding decent |
| 8 GB (browser band) | qwen2.5-coder:7b | ~4.7 GB | ⚠️ tight par chalega |
| **12 GB** (Oracle VM) | **qwen2.5-coder:7b** | ~4.7 GB | ✅ best balance |
| 12 GB | qwen2.5-coder:14b | ~9 GB | ⚠️ tight — sirf jab aur kuch na chale |
| 16 GB+ | qwen2.5-coder:14b | ~9 GB | ✅ strong coding |

**Coding ke liye `qwen2.5-coder` family sabse best hai** — chhote size me bhi code acche likhte hain.

---

## ⚠️ Oracle ke 3 catches (honest)

1. **Capacity** — A1 instances aksar "out of capacity" dikhate hain. Retry karte raho / region badlo.
2. **Idle reclaim** — agar 7 din tak CPU, network **aur** memory teeno 20% se neeche rahe to instance reclaim ho sakta hai.
   - **Fix:** `OLLAMA_KEEP_ALIVE=-1` (script me already hai) → model RAM me rehta hai → memory usage ~5 GB = 40% of 12 GB → safe.
   - Extra safety: `*/10 * * * * curl -s localhost:5000/healthz >/dev/null` cron.
3. **Free limits aadhe ho gaye** (Jun 2026) — 4/24 ka plan mat banao, **2 OCPU / 12 GB** hi.

---

## 🆚 Laptop vs Oracle VM

| | Laptop | Oracle VM |
|---|---|---|
| Cost | ₹0 | ₹0 |
| 24/7 | ❌ (band karoge to gaya) | ✅ |
| Speed | ⚡ zyada (tera CPU/GPU) | 🐢 ARM CPU, par theek |
| RAM for model | 8 GB | 12 GB |
| Setup | 5 min | 30-45 min |
| Internet pe URL | tunnel (temporary) | ✅ permanent IP |

**Mera suggestion:** pehle laptop pe chala ke maza dekh lo, phir Oracle VM pe utha do jab 24/7 chahiye ho.

---

## 🧪 Deploy ke baad check

```bash
# VM pe
systemctl status superagent
journalctl -u superagent -n 30
curl -s localhost:5000/healthz     # -> ok
curl -s localhost:11434/api/tags   # -> model list

# model test
ollama run qwen2.5-coder:7b "print hello in python"
```

App khulne pe badge me **`ollama · qwen2.5-coder:7b`** dikhna chahiye — matlab local model chal raha hai, koi API key nahi.

---

## 🩺 Troubleshooting

| Problem | Fix |
|---|---|
| `Out of capacity` (VM create) | Region/AD badlo, retry, ya 2×1 OCPU (6 GB) try karo |
| App khulta nahi | Oracle Security List me port 5000 ingress rule add karo |
| Badge `pollinations` dikha raha | Ollama band hai → `sudo systemctl start ollama`, phir app restart |
| Jawab bahut slow | Chhota model: `AGENT_MODEL=qwen2.5-coder:3b` `.env` me |
| `model not found` | `ollama pull qwen2.5-coder:7b` dobara |
| VM 7 din baad gayab | Idle reclaim — keep_alive + healthz cron laga do |
| Service crash | `journalctl -u superagent -n 100` dekho |

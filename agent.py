#!/usr/bin/env python3
"""
PRIVATE AGENT 2.0 — apna AI agent, zero restriction mode ke saath.

Kya naya hai:
  - MULTI-KEY POOL: ek hi provider ki 3-4 free keys daal do, limit aate hi
    agla key khud use ho jayega.
  - AUTO-FALLBACK: Groq ki limit khatam -> Gemini -> OpenRouter -> DeepSeek...
    sab configured providers apne aap try hote hain.
  - OLLAMA SUPPORT: 100% unlimited, 100% local, koi key nahi.
  - Same tools: files, python, web fetch.

Chalao:
  python agent.py
  python agent.py "task do"
  python agent.py --provider ollama
"""

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

try:
    from dotenv import load_dotenv
    from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError
except ImportError:
    print("\n[!] Pehle ye chalao:  pip install -r requirements.txt\n")
    sys.exit(1)

HERE = pathlib.Path(__file__).parent.resolve()
WORKSPACE = HERE / "workspace"
WORKSPACE.mkdir(exist_ok=True)

MAX_STEPS = 20
MAX_TOOL_OUTPUT = 6000

# ---------------------------------------------------------------- providers
PRESETS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model": "openai/gpt-oss-120b",
        "signup": "https://console.groq.com/keys",
        "note": "Free, no card. 30 req/min, ~1000 req/day. Sabse fast.",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "model": "gemini-3.8-flash",
        "signup": "https://aistudio.google.com/apikey",
        "note": "Free tier, no card, key permanent.",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "model": "openrouter/free",
        "signup": "https://openrouter.ai/keys",
        "note": "Free ':free' models. 20 req/min, 50 req/day.",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "key_env": "MISTRAL_API_KEY",
        "model": "mistral-large-latest",
        "signup": "https://console.mistral.ai/api-keys",
        "note": "Free 'Experiment' tier, phone verify.",
    },
    "pollinations": {
        "base_url": "https://text.pollinations.ai/openai",
        "key_env": "POLLINATIONS_API_KEY",
        "model": "openai-fast",
        "signup": "KOI KEY NAHI CHAHIYE — free & keyless",
        "note": "Bina key! GPT-OSS 20B, tool calling support. Anonymous tier, 1 request/IP.",
        "keyless": True,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-flash",
        "signup": "https://platform.deepseek.com/api_keys",
        "note": "PAID (5M free token naye account pe). Sasta hai par free nahi.",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "key_env": "OLLAMA_API_KEY",
        "model": "qwen2.5-coder:7b",
        "signup": "https://ollama.com/download",
        "note": "100% local, unlimited, koi key nahi, koi limit nahi.",
    },
    "custom": {
        "base_url": "http://localhost:8000/v1",
        "key_env": "CUSTOM_API_KEY",
        "model": "local-model",
        "signup": "CUSTOM_BASE_URL env me endpoint daalo",
        "note": "LM Studio / vLLM / apna server.",
    },
}

# Free-first order. DeepSeek paid hai isliye last me.
AUTO_ORDER = ["groq", "gemini", "openrouter", "mistral", "deepseek", "pollinations"]
KEYLESS = {"pollinations", "ollama", "custom"}

SYSTEM_PROMPT = """Tum ek private AI agent ho jo user ke computer ke 'workspace' folder me kaam karta hai.

Tumhare paas apna TERMINAL hai (run_shell) aur MULTI-LANGUAGE RUNNER (run_code):
python, javascript, java, c, cpp, csharp, lua, go, rust, php, ruby, bash, powershell.

Rules:
- Kaam khud karo. "Aap ye kar lo" mat kaho — tum karo.
- Code likho -> CHALAO -> error aaye to padho -> FIX karo -> dobara chalao.
  Jab tak output sahi na aaye, rukna nahi.
- run_shell se packages bhi install kar sakte ho (pip install, npm install, apt).
- Har file workspace ke andar hi banao.
- Files banate waqt poora final content likho, placeholder nahi.
- Kaam khatam hone par 2-3 line me batao kya banaya aur kahan hai.
- Jawab Hinglish me do (simple, friendly), technical cheezein English me.
- Chhota aur clear rakho, faltu explanation mat do."""


# ---------------------------------------------------------------- tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Workspace ke files/folders ki list dekho.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative path, default '.'"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Workspace ki ek file padho.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Workspace me file banao ya overwrite karo. Parent folders khud ban jaate hain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "e.g. 'index.html' ya 'data/report.md'"},
                    "content": {"type": "string", "description": "Poora file content"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_code",
            "description": "Kisi bhi language ka code likho aur chalao. Compile errors khud milenge, phir fix karke dobara chalao.",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": [
                            "python", "javascript", "java", "c", "cpp", "csharp",
                            "lua", "go", "rust", "php", "ruby", "bash", "powershell",
                        ],
                        "description": "Kaunsi language",
                    },
                    "code": {"type": "string", "description": "Poora code"},
                },
                "required": ["language", "code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": (
                "Apna terminal — koi bhi shell command. npm install, pip install, git, "
                "mkdir, curl, gcc, ffmpeg, python script.py, ls, find, zip, etc. "
                "Workspace folder me chalta hai."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command"},
                    "timeout_s": {"type": "integer", "description": "Max seconds, default 120"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Kisi web page ka text laao (http/https).",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
]


def safe_path(rel: str) -> pathlib.Path:
    target = (WORKSPACE / rel).resolve()
    if WORKSPACE not in target.parents and target != WORKSPACE:
        raise ValueError("Workspace ke bahar access allowed nahi hai.")
    return target


def tool_list_files(path: str = ".") -> str:
    target = safe_path(path)
    if not target.exists():
        return f"'{path}' nahi mila."
    rows = []
    for p in sorted(target.iterdir()):
        size = p.stat().st_size if p.is_file() else "-"
        rows.append(f"{'DIR ' if p.is_dir() else 'FILE'} {p.name} ({size})")
    return "\n".join(rows) if rows else "(khali folder)"


def tool_read_file(path: str) -> str:
    target = safe_path(path)
    if not target.is_file():
        return f"File nahi mili: {path}"
    text = target.read_text(encoding="utf-8", errors="replace")
    if len(text) > MAX_TOOL_OUTPUT:
        return text[:MAX_TOOL_OUTPUT] + f"\n... (truncated, total {len(text)} chars)"
    return text


def tool_write_file(path: str, content: str) -> str:
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Saved: {target.relative_to(WORKSPACE)} ({len(content)} chars)"


LANG_SPECS = {
    "python": {"ext": ".py", "run": [sys.executable]},
    "javascript": {"ext": ".js", "run": ["node"]},
    "java": {"ext": ".java", "compile": ["javac"], "run": ["java", "Main"]},
    "c": {"ext": ".c", "compile": ["gcc", "-O2", "-o", "{out}"], "run": ["{out}"]},
    "cpp": {"ext": ".cpp", "compile": ["g++", "-std=c++17", "-O2", "-o", "{out}"], "run": ["{out}"]},
    "csharp": {"ext": ".cs", "run": ["dotnet", "script"]},
    "lua": {"ext": ".lua", "run": ["lua"]},
    "go": {"ext": ".go", "run": ["go", "run"]},
    "rust": {"ext": ".rs", "compile": ["rustc", "-O", "-o", "{out}"], "run": ["{out}"]},
    "php": {"ext": ".php", "run": ["php"]},
    "ruby": {"ext": ".rb", "run": ["ruby"]},
    "bash": {"ext": ".sh", "run": ["bash"]},
    "powershell": {"ext": ".ps1", "run": ["powershell", "-NoProfile", "-File"]},
}

def set_workspace(path) -> pathlib.Path:
    """Per-chat workspace (server mode). Thread-safe via server-side lock."""
    global WORKSPACE
    WORKSPACE = pathlib.Path(path)
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    return WORKSPACE


def _codegen_dir() -> pathlib.Path:
    d = WORKSPACE / ".codegen"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _which(name: str) -> bool:
    from shutil import which

    return which(name) is not None


def tool_run_code(language: str, code: str) -> str:
    """Kisi bhi language ka code likho, compile karo, chalao."""
    lang = (language or "").lower().strip()
    if lang in {"js", "node", "nodejs"}:
        lang = "javascript"
    if lang in {"c++", "cplusplus"}:
        lang = "cpp"
    if lang in {"c#", "cs", ".net"}:
        lang = "csharp"
    if lang in {"py"}:
        lang = "python"
    if lang in {"sh", "shell"}:
        lang = "bash"

    spec = LANG_SPECS.get(lang)
    if not spec:
        return f"Language '{language}' support nahi hai. Ye chalengi: {', '.join(LANG_SPECS)}"

    runner = (spec.get("compile") or spec["run"])[0]
    probe = "dotnet" if runner == "{out}" else runner
    if not _which(probe.replace("{out}", "gcc")):
        return (
            f"'{lang}' ka toolchain is container me installed nahi hai ({runner} nahi mila).\n"
            f"Railway pe slim image hai (sirf Python + JavaScript). Options:\n"
            f"  - Python ya JavaScript me karo (dono available hain)\n"
            f"  - Poora multi-language chahiye to Dockerfile use karo (railway.json me dockerfilePath badlo)\n"
            f"  - Local/VM pe: python doctor.py --install-hint {lang}"
        )

    cg = _codegen_dir()
    stem = f"prog_{int(time.time()*1000)}"
    src = cg / (stem + spec["ext"])
    if lang == "java":
        src = cg / "Main.java"
    out_bin = cg / (stem + (".exe" if os.name == "nt" else ""))
    src.write_text(code, encoding="utf-8")

    def run(cmd):
        return subprocess.run(
            [c if c != "{out}" else str(out_bin) for c in cmd],
            cwd=cg, capture_output=True, text=True, timeout=120,
        )

    try:
        if spec.get("compile"):
            cp = run(spec["compile"] + [str(src)])
            if cp.returncode != 0:
                return "❌ Compile error:\n" + ((cp.stderr or cp.stdout or "").strip()[:MAX_TOOL_OUTPUT])
        if lang == "java":
            run_cmd = spec["run"]              # java Main (class name)
        else:
            run_cmd = spec["run"] + [str(src)]  # interpreter/script + file
        rp = run(run_cmd)
        out = (rp.stdout or "") + (("\n[stderr]\n" + rp.stderr) if rp.stderr else "")
        out = out.strip() or "(koi output nahi aaya)"
        if rp.returncode != 0:
            out = f"(exit code {rp.returncode})\n" + out
        return out[:MAX_TOOL_OUTPUT]
    except subprocess.TimeoutExpired:
        return "Error: code 120 second me khatam nahi hua, kill kar diya."
    except Exception as e:  # noqa: BLE001
        return f"Run error: {e}"
    finally:
        for p in (src, out_bin, cg / "Main.class"):
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass


BLOCKED = [
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=/dev/zero of=/dev", ":(){", "shutdown", "reboot",
    "chmod -R 777 /", "> /dev/sda", "format c:", "del /f /s /q c:\\",
]


def tool_run_shell(command: str, timeout_s: int = 120) -> str:
    """Apna terminal — koi bhi command, workspace me."""
    cmd = (command or "").strip()
    if not cmd:
        return "Khali command."
    low = cmd.lower()
    for b in BLOCKED:
        if b in low:
            return f"⛔ Ye command block hai (system ko nuksan pahuncha sakti hai): {b}"

    timeout_s = max(5, min(int(timeout_s or 120), 600))
    try:
        p = subprocess.run(
            cmd, shell=True, cwd=WORKSPACE, capture_output=True, text=True, timeout=timeout_s
        )
        out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr else "")
        out = out.strip() or "(koi output nahi)"
        if p.returncode != 0:
            out = f"(exit code {p.returncode})\n" + out
        return out[:MAX_TOOL_OUTPUT]
    except subprocess.TimeoutExpired:
        return f"Error: command {timeout_s}s me khatam nahi hui."
    except Exception as e:  # noqa: BLE001
        return f"Shell error: {e}"


def tool_run_python(code: str) -> str:
    """Backward-compat alias."""
    return tool_run_code("python", code)


def tool_fetch_url(url: str) -> str:
    if not re.match(r"^https?://", url):
        return "Sirf http/https URL chalega."
    try:
        import requests

        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        html = r.text
        html = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", html)
        text = re.sub(r"(?s)<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return f"URL: {url}\n\n{text[:MAX_TOOL_OUTPUT]}"
    except Exception as e:
        return f"Fetch fail: {e}"


REGISTRY = {
    "list_files": tool_list_files,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "run_code": tool_run_code,
    "run_shell": tool_run_shell,
    "run_python": tool_run_python,  # backward compat
    "fetch_url": tool_fetch_url,
}


def call_tool(name: str, args: dict) -> str:
    fn = REGISTRY.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        return fn(**args)
    except TypeError as e:
        return f"Bad arguments: {e}"
    except Exception as e:
        return f"Tool error: {e}"


# ---------------------------------------------------------------- provider pool
class Provider:
    def __init__(self, name, base_url, model, key):
        self.name = name
        self.base_url = base_url
        self.model = model
        self.key = key
        self.dead = False

    def label(self):
        masked = (self.key[:6] + "..." + self.key[-4:]) if len(self.key) > 12 else "local"
        return f"{self.name}:{self.model} ({masked})"


def build_pool(preferred: str | None = None, model_override: str | None = None) -> list[Provider]:
    """Providers ko try-order me daalo.

    Order (jab sab available hain):
      1. OLLAMA (local)  — unlimited, free, sabse fast   <- pehle
      2. preferred provider (agar CLI se diya)
      3. keyed free providers (groq, gemini, openrouter, mistral, deepseek)
      4. pollinations (keyless fallback) — hamesha available
      5. custom endpoint (agar CUSTOM_BASE_URL set hai)
    """
    ollama_base = os.getenv("OLLAMA_BASE_URL", PRESETS["ollama"]["base_url"])

    order: list[str] = []

    # 1) local Ollama pehle — agar chal raha hai (ya explicitly maanga)
    if preferred == "ollama" or _ollama_alive(ollama_base):
        order.append("ollama")

    # 2) explicit choice
    if preferred and preferred not in order:
        order.append(preferred)

    # 3) cloud providers (free first)
    for name in AUTO_ORDER:
        if name not in order:
            order.append(name)

    # 4) custom endpoint
    if os.getenv("CUSTOM_BASE_URL") and "custom" not in order:
        order.append("custom")

    pool: list[Provider] = []
    for name in order:
        preset = PRESETS[name]
        model = model_override or os.getenv("AGENT_MODEL") or preset["model"]

        if name == "custom":
            base = os.getenv("CUSTOM_BASE_URL", preset["base_url"])
            key = os.getenv("CUSTOM_API_KEY", "no-key")
            pool.append(Provider(name, base, model, key))
            continue

        if name == "ollama":
            base = os.getenv("OLLAMA_BASE_URL", preset["base_url"])
            pool.append(Provider(name, base, model, "ollama"))
            continue

        raw = os.getenv(preset["key_env"], "")
        keys = [k.strip() for k in raw.replace("\n", ",").split(",") if k.strip()]

        if preset.get("keyless"):
            pool.append(Provider(name, preset["base_url"], model, keys[0] if keys else "none"))
            continue

        for k in keys:
            pool.append(Provider(name, preset["base_url"], model, k))
    return pool


def _ollama_alive(base_url: str) -> bool:
    try:
        import requests

        requests.get(base_url.rsplit("/v1", 1)[0] + "/api/tags", timeout=1.5)
        return True
    except Exception:
        return False


class AgentState:
    """Pool + messages + tools. CLI aur web dono isi ko use karte hain."""

    def __init__(self, pool: list[Provider] | None = None):
        self.pool = pool or []
        self.idx = 0
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.client = None

    # --- provider management -------------------------------------------
    @property
    def current(self) -> Provider | None:
        while self.idx < len(self.pool) and self.pool[self.idx].dead:
            self.idx += 1
        return self.pool[self.idx] if self.idx < len(self.pool) else None

    def _connect(self, p: Provider):
        self.client = OpenAI(base_url=p.base_url, api_key=p.key or "none", timeout=180)

    def next_provider(self, reason: str = "") -> bool:
        p = self.current
        if p:
            p.dead = True
        self.client = None
        self.idx += 1
        if self.current:
            print(f"  [switch] {reason} -> {self.current.label()}")
            return True
        return False

    # --- llm call ------------------------------------------------------
    def _stream_call(self, p, on_delta):
        """Streaming request: token-by-token callback + tool calls assemble."""
        from types import SimpleNamespace

        stream = self.client.chat.completions.create(
            model=p.model,
            messages=self.messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            stream=True,
        )
        parts, calls = [], {}
        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            txt = getattr(delta, "content", None)
            if txt:
                parts.append(txt)
                on_delta(txt)
            for tc in (getattr(delta, "tool_calls", None) or []):
                slot = calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                if tc.id:
                    slot["id"] = tc.id
                fn = getattr(tc, "function", None)
                if fn:
                    if fn.name:
                        slot["name"] = fn.name
                    if fn.arguments:
                        slot["arguments"] += fn.arguments
        tcs = [
            SimpleNamespace(
                id=v["id"] or f"call_{i}",
                type="function",
                function=SimpleNamespace(name=v["name"], arguments=v["arguments"]),
            )
            for i, v in sorted(calls.items())
        ] or None
        # run() ke normal path se compatible shape (choices[0].message)
        msg = SimpleNamespace(content="".join(parts) or None, tool_calls=tcs)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

    def ask(self, on_wait=None, on_delta=None):
        """Current provider se completion.

        - on_delta diya -> streaming (token turant UI me)
        - 402/429 (free tier throttle) -> agar doosra provider ready hai to switch,
          warna 'Retry after Ns' padh ke wait karke wahi provider dobara try
        """
        switched = 0
        total_wait = 0
        while True:
            p = self.current
            if not p:
                raise RuntimeError(
                    "Saare providers fail ho gaye. Free key daalo (python agent.py --setup) "
                    "ya Ollama chalao: python agent.py --provider ollama"
                )
            if self.client is None:
                self._connect(p)
            try:
                if on_delta:
                    try:
                        return self._stream_call(p, on_delta)
                    except (RateLimitError, APIStatusError, APIConnectionError):
                        raise
                    except Exception:
                        # kuch providers streaming support nahi karte -> normal call
                        pass
                return self.client.chat.completions.create(
                    model=p.model,
                    messages=self.messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=0.3,
                )
            except (RateLimitError, APIStatusError, APIConnectionError) as e:
                msg = str(e)
                code = getattr(e, "status_code", None)

                if code in (402, 429) or "FREE_LIMIT" in msg or "Free limit reached" in msg:
                    # pehle doosra provider try karo (fast key wala)
                    others = [x for x in self.pool[self.idx + 1:] if not x.dead]
                    if others:
                        self.next_provider(f"{p.name} throttle — switch")
                        switched += 1
                        continue

                    m = re.search(r"[Rr]etry after (\d+)\s*s", msg)
                    wait = (int(m.group(1)) + 2) if m else 32
                    if total_wait + wait <= 180:
                        total_wait += wait
                        note = f"{p.name}: free limit — {wait}s wait"
                        (on_wait or (lambda n: print(f"  [wait] {n}")))(note)
                        time.sleep(wait)
                        continue

                switched += 1
                if switched > len(self.pool) + 1:
                    raise RuntimeError(f"Sab providers fail. Last error: {msg[:200]}") from e
                if not self.next_provider(f"{p.name} fail ({code or 'network'})"):
                    raise RuntimeError(f"Sab providers fail. Last error: {msg[:200]}") from e

    # --- tool loop -----------------------------------------------------
    def run(self, task: str, on_event=None) -> str:
        def emit(kind, data):
            if on_event:
                on_event(kind, data)

        self.messages.append({"role": "user", "content": task})

        for step in range(1, MAX_STEPS + 1):
            try:
                resp = self.ask(
                    on_wait=lambda note: emit("tool", {"step": "⏳", "name": note, "target": ""}),
                    on_delta=lambda chunk: emit("delta", chunk),
                )
            except RuntimeError as e:
                msg = str(e)
                emit("error", msg)
                return msg

            m = resp.choices[0].message
            am = {"role": "assistant", "content": m.content or ""}
            if m.tool_calls:
                am["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in m.tool_calls
                ]
            self.messages.append(am)

            if not m.tool_calls:
                final = m.content or "(khali jawab)"
                emit("final", final)
                return final

            for tc in m.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                target = (
                    args.get("path") or args.get("url")
                    or args.get("command") or args.get("language") or ""
                )
                if len(str(target)) > 60:
                    target = str(target)[:60] + "…"
                emit("tool", {"step": step, "name": name, "target": target})
                result = call_tool(name, args)
                self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        msg = "Max steps ho gaye. Task chhote hisson me do."
        emit("error", msg)
        return msg


# ---------------------------------------------------------------- CLI
def print_events(kind, data):
    if kind == "tool":
        t = f" {data['target']}" if data.get("target") else ""
        print(f"  [{data['step']}] {data['name']}{t}")
    elif kind == "final":
        print(f"\n{data}\n")
    elif kind == "error":
        print(f"\n[!] {data}\n")


def main():
    load_dotenv(HERE / ".env")

    ap = argparse.ArgumentParser(description="Private AI agent — unlimited free mode")
    ap.add_argument("task", nargs="*")
    ap.add_argument("--provider", default=os.getenv("PROVIDER") or None, choices=list(PRESETS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--setup", action="store_true")
    args = ap.parse_args()

    if args.setup:
        print("\n=== FREE API KEYS ===\n")
        for n, p in PRESETS.items():
            print(f"{n:12} -> {p['signup']}")
            print(f"{'':12}    {p['note']}\n")
        print("TIP: ek hi line me 3-4 keys comma se daal do, agent khud rotate karega:")
        print("     GROQ_API_KEY=key1,key2,key3\n")
        return

    pool = build_pool(args.provider, args.model)
    if not pool:
        print("\n[!] Koi provider configured nahi hai.\n")
        print("  Option 1 (UNLIMITED, FREE): Ollama install karo")
        print("     https://ollama.com/download")
        print("     ollama pull qwen3:8b")
        print("     python agent.py --provider ollama\n")
        print("  Option 2 (free cloud keys):")
        print("     python agent.py --setup\n")
        sys.exit(1)

    state = AgentState(pool)
    print(f"\nPrivate Agent | {len(pool)} provider(s) ready")
    for p in pool:
        print(f"  - {p.label()}")
    print(f"Workspace: {WORKSPACE}\n")

    if args.task:
        state.run(" ".join(args.task), print_events)
        return

    print("Kuch bhi pucho ya kaam do. Exit: 'exit'\n")
    while True:
        try:
            task = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye!")
            break
        if not task:
            continue
        if task.lower() in {"exit", "quit", "q", "bye"}:
            print("bye!")
            break
        state.run(task, print_events)


if __name__ == "__main__":
    main()

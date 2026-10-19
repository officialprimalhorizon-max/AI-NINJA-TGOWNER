#!/usr/bin/env python3
"""
DOCTOR — tumhare computer pe kya-kya ready hai, check karo.

  python doctor.py                  # poori report
  python doctor.py --install-hint go   # ek language install karne ka command
"""

import importlib.util
import os
import platform
import shutil
import subprocess
import sys

OK = "✅"
NO = "❌"
WARN = "⚠️ "

# lang -> (binary list me se koi ek, winget, brew, apt)
LANGS = {
    "python":      (["python3", "python"],        "winget install Python.Python.3.12", "brew install python", "sudo apt install python3"),
    "javascript":  (["node"],                     "winget install OpenJS.NodeJS.LTS",  "brew install node",   "sudo apt install nodejs npm"),
    "java":        (["javac"],                    "winget install EclipseAdoptium.Temurin.21.JDK", "brew install openjdk", "sudo apt install default-jdk"),
    "c":           (["gcc", "cc"],                "winget install BrechtSanders.WinLibs.POSIX.UCRT", "xcode-select --install", "sudo apt install build-essential"),
    "cpp":         (["g++"],                      "winget install BrechtSanders.WinLibs.POSIX.UCRT", "xcode-select --install", "sudo apt install build-essential"),
    "csharp":      (["dotnet"],                   "winget install Microsoft.DotNet.SDK.8", "brew install dotnet", "sudo apt install dotnet-sdk-8.0"),
    "lua":         (["lua", "lua5.4"],            "winget install DEVCOM.Lua", "brew install lua", "sudo apt install lua5.4"),
    "go":          (["go"],                       "winget install GoLang.Go",  "brew install go",  "sudo apt install golang-go"),
    "rust":        (["rustc"],                    "winget install Rustlang.Rustup", "brew install rust", "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"),
    "php":         (["php"],                      "winget install PHP.PHP",    "brew install php", "sudo apt install php"),
    "ruby":        (["ruby"],                     "winget install RubyInstallerTeam.Ruby", "brew install ruby", "sudo apt install ruby"),
    "bash":        (["bash"],                     "(Git Bash ke saath aata hai)", "built-in", "built-in"),
}

DEPS = ["openai", "dotenv", "requests", "flask"]

MODEL_GUIDE = {
    "<=8":  ["qwen2.5-coder:3b  (~2 GB) — 8GB RAM ke liye best coding model",
             "qwen3:4b          (~2.5 GB) — general kaam, fast",
             "llama3.2:3b       (~2 GB) — sabse halka"],
    "<=16": ["qwen2.5-coder:7b  (~4.7 GB) — 8-16GB, accha coding balance",
             "qwen3:8b          (~5 GB) — acche reasoning"],
    "<=32": ["qwen2.5-coder:14b (~9 GB) — strong coding",
             "qwen3:14b         (~9 GB) — strong general"],
    ">32":  ["qwen3:32b / coder:32b — best local quality"],
}


def which_any(names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def version_cmd(path):
    try:
        out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=8)
        v = (out.stdout or out.stderr or "").strip().splitlines()
        return v[0][:60] if v else "?"
    except Exception:  # noqa: BLE001
        return "?"


def ram_gb():
    try:
        if hasattr(os, "sysconf"):
            return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1)
        if platform.system() == "Windows":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            m = MS()
            m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.ullTotalPhys / 1e9, 1)
        if platform.system() == "Darwin":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
            return round(int(out.stdout.strip()) / 1e9, 1)
    except Exception:  # noqa: BLE001
        pass
    return 0.0


def model_advice(ram):
    if ram <= 9:
        return MODEL_GUIDE["<=8"]
    if ram <= 17:
        return MODEL_GUIDE["<=16"]
    if ram <= 33:
        return MODEL_GUIDE["<=32"]
    return MODEL_GUIDE[">32"]


def ollama_models():
    try:
        out = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        lines = [ln.split()[0] for ln in out.stdout.strip().splitlines()[1:] if ln.strip()]
        return lines
    except Exception:  # noqa: BLE001
        return []


def main():
    args = sys.argv[1:]
    if "--install-hint" in args:
        lang = args[args.index("--install-hint") + 1].lower()
        row = LANGS.get(lang)
        if not row:
            print(f"'{lang}' unknown. Options: {', '.join(LANGS)}")
            return
        os_name = platform.system()
        cmd = row[1] if os_name == "Windows" else row[2] if os_name == "Darwin" else row[3]
        print(f"\n{lang} install karne ke liye:\n\n  {cmd}\n")
        return

    os_name = f"{platform.system()} {platform.release()}"
    ram = ram_gb()
    print("\n" + "=" * 56)
    print("  DOCTOR — tumhara setup")
    print("=" * 56)
    print(f"\n🖥  System : {os_name} | {platform.machine()}")
    print(f"🧠 RAM    : {ram} GB")
    try:
        d = shutil.disk_usage(".")
        print(f"💾 Disk   : {round(d.free/1e9,1)} GB free")
    except Exception:  # noqa: BLE001
        pass
    print(f"🐍 Python : {sys.version.split()[0]}")

    print("\n--- LANGUAGES (agent inme code likh ke chala sakta hai) ---")
    ready, missing = [], []
    for lang, (bins, *_rest) in LANGS.items():
        p = which_any(bins)
        if p:
            print(f"  {OK} {lang:12} {version_cmd(p)}")
            ready.append(lang)
        else:
            print(f"  {NO} {lang:12} — install: python doctor.py --install-hint {lang}")
            missing.append(lang)

    print("\n--- TERMINAL TOOLS ---")
    for tool, hint in [
        ("git", "winget install Git.Git / brew install git / apt install git"),
        ("curl", "built-in usually"),
        ("ffmpeg", "winget install Gyan.FFmpeg / brew install ffmpeg / apt install ffmpeg"),
        ("pandoc", "winget install JohnMacFarlane.Pandoc / apt install pandoc"),
        ("poppler-utils (pdftotext)", "apt install poppler-utils / brew install poppler"),
    ]:
        name = tool.split()[0]
        p = which_any([name])
        print(f"  {OK if p else NO} {tool:28}" + ("" if p else f" — {hint}"))

    print("\n--- PYTHON PACKAGES ---")
    for dep in DEPS:
        mod = "dotenv" if dep == "dotenv" else dep
        ok = importlib.util.find_spec(mod) is not None
        print(f"  {OK if ok else NO} {dep}" + ("" if ok else "  → pip install -r requirements.txt"))

    print("\n--- OLLAMA (local unlimited mode) ---")
    ol = shutil.which("ollama")
    if ol:
        models = ollama_models()
        print(f"  {OK} installed — models: {models or 'koi nahi (ollama pull karo)'}")
    else:
        print(f"  {NO} installed nahi — https://ollama.com/download")

    print(f"\n--- 8 GB RAM KE LIYE MODEL SUGGESTION ---")
    for line in model_advice(ram):
        print(f"  • {line}")
    print("\n  Bada model (14B+) 8GB pe mat chalao — swap hoke bahut slow ho jayega.")
    print("  Coding ke liye 'qwen2.5-coder' family sabse best hai.\n")

    print("=" * 56)
    print(f"  Ready languages: {len(ready)}/{len(LANGS)}  {ready}")
    if missing:
        print(f"  Missing        : {missing}")
    print("=" * 56 + "\n")


if __name__ == "__main__":
    main()

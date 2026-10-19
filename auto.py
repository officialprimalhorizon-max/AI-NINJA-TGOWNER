#!/usr/bin/env python3
"""
AUTO AGENT — always-on. Tum kuch na karo, ye khud kare.

Do tarah ka automation:

1) SCHEDULE — "roz subah 8 baje news summary banao"
   tasks.json me time likho. Ye daemon chalta rahega, time pe khud kaam karega.

2) WATCH FOLDER — workspace/inbox me file daalo
   Auto process hoke result workspace/outbox me aa jayega.

Chalao:
  python auto.py                 # daemon (always-on)
  python auto.py --list          # kaunse kaam set hain
  python auto.py --run <name>    # ek job abhi chalao
  python auto.py --test          # sab kuch theek hai? check karo
"""

import datetime as dt
import json
import pathlib
import shutil
import sys
import threading
import time
import traceback

from dotenv import load_dotenv

import agent as core

HERE = core.HERE
TASKS_FILE = HERE / "tasks.json"
STATE_FILE = HERE / ".auto_state.json"
LOG_FILE = HERE / "logs" / "auto.log"
INBOX = core.WORKSPACE / "inbox"
OUTBOX = core.WORKSPACE / "outbox"

INBOX.mkdir(parents=True, exist_ok=True)
OUTBOX.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

RUN_LOCK = threading.Lock()  # ek waqt me ek hi kaam

DEFAULT_TASKS = {
    "watch_seconds": 5,
    "watch": [
        {
            "name": "inbox-process",
            "folder": "inbox",
            "prompt": "Is file ko padho ya analyze karo: {file}\n"
                      "Ek saaf summary/report banao aur outbox/{stem}.md me save karo. "
                      "Hinglish me likho, headings ke saath.",
            "enabled": False,
        }
    ],
    "schedules": [
        {
            "name": "morning-news",
            "at": "08:00",
            "prompt": "Aaj ki top 5 AI/tech news dhoondo (web fetch use karo) aur "
                      "ek short Hinglish summary banao. reports/news-{date}.md me save karo.",
            "enabled": False,
        },
        {
            "name": "daily-diary",
            "every_minutes": 1440,
            "prompt": "Aaj ka din ka ek chhota note likho workspace/diary-{date}.md me. "
                      "5 line ka, Hinglish me, positive tone.",
            "enabled": False,
        },
    ],
}


# ------------------------------------------------------------------ helpers
def log(msg: str, echo: bool = True) -> None:
    line = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    if echo:
        print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_tasks() -> dict:
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text(json.dumps(DEFAULT_TASKS, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"tasks.json banayi: {TASKS_FILE}")
    try:
        return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        log(f"tasks.json me galti hai: {e}")
        return {"watch_seconds": 5, "watch": [], "schedules": []}


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"processed": {}, "last_run": {}}


def save_state(s: dict) -> None:
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


def all_jobs(tasks: dict) -> list[dict]:
    jobs = []
    for j in tasks.get("schedules", []):
        jobs.append({"type": "schedule", **j})
    for j in tasks.get("watch", []):
        jobs.append({"type": "watch", **j})
    return jobs


# ------------------------------------------------------------------ runner
def run_prompt(prompt: str, label: str = "job") -> str:
    """Ek agent task chalao. Lock laga ke — ek waqt me ek."""
    with RUN_LOCK:
        pool = core.build_pool()
        if not pool:
            msg = "Koi provider configured nahi (na key, na Ollama)."
            log(msg)
            return msg
        agent = core.AgentState(pool)
        log(f"START {label} | provider={pool[0].label()}")
        t0 = time.time()

        def on_event(kind, data):
            if kind == "tool":
                log(f"   · {data['name']} {data.get('target','')}", echo=False)
            elif kind == "error":
                log(f"   ! {data}", echo=False)

        try:
            out = agent.run(prompt, on_event)
            log(f"DONE {label} ({time.time()-t0:.1f}s)")
            return out
        except Exception as e:  # noqa: BLE001
            log(f"FAIL {label}: {e}\n{traceback.format_exc(limit=2)}")
            return str(e)


def run_job_now(name: str) -> None:
    tasks = load_tasks()
    for j in all_jobs(tasks):
        if j.get("name") == name:
            prompt = j["prompt"].replace("{date}", dt.date.today().isoformat())
            run_prompt(prompt, label=f"manual:{name}")
            return
    log(f"Job '{name}' nahi mila. --list chala ke dekho.")


# ------------------------------------------------------------------ scheduler
def due_now(job: dict, last_run: str | None) -> bool:
    now = dt.datetime.now()

    if "every_minutes" in job:
        mins = int(job["every_minutes"])
        if not last_run:
            return True
        prev = dt.datetime.fromisoformat(last_run)
        return (now - prev).total_seconds() >= mins * 60

    if "at" in job:
        hhmm = str(job["at"])
        try:
            h, m = [int(x) for x in hhmm.split(":")]
        except ValueError:
            return False
        if now.hour != h or now.minute != m:
            return False
        # ek hi din me ek baar
        return not last_run or dt.datetime.fromisoformat(last_run).date() != now.date()

    return False


def scheduler_loop(stop_event: threading.Event) -> None:
    log("Scheduler chal raha hai (har 20 sec check)")
    while not stop_event.is_set():
        tasks = load_tasks()
        state = load_state()
        for job in tasks.get("schedules", []):
            if not job.get("enabled"):
                continue
            name = job.get("name", "unnamed")
            if due_now(job, state.get("last_run", {}).get(name)):
                prompt = job["prompt"].replace("{date}", dt.date.today().isoformat())
                state.setdefault("last_run", {})[name] = dt.datetime.now().isoformat()
                save_state(state)
                threading.Thread(
                    target=run_prompt, args=(prompt, f"scheduled:{name}"), daemon=True
                ).start()
        stop_event.wait(20)


# ------------------------------------------------------------------ watcher
def watcher_loop(tasks: dict, stop_event: threading.Event) -> None:
    interval = max(2, int(tasks.get("watch_seconds", 5)))
    watched = [w for w in tasks.get("watch", []) if w.get("enabled")]
    if not watched:
        log("Watch folder off hai (tasks.json me 'enabled': true karo)")
        return
    log(f"Watcher chal raha hai: {[w.get('folder') for w in watched]} (har {interval}s)")

    while not stop_event.is_set():
        state = load_state()
        processed = state.get("processed", {})
        for w in watched:
            folder = core.WORKSPACE / w.get("folder", "inbox")
            folder.mkdir(parents=True, exist_ok=True)
            for f in folder.iterdir():
                if not f.is_file() or f.name.startswith("."):
                    continue
                stamp = f"{f.name}:{f.stat().st_mtime_ns}"
                if processed.get(f.name) == stamp:
                    continue
                processed[f.name] = stamp
                state["processed"] = processed
                save_state(state)
                prompt = (
                    w["prompt"]
                    .replace("{file}", f"{w.get('folder','inbox')}/{f.name}")
                    .replace("{stem}", f.stem)
                    .replace("{date}", dt.date.today().isoformat())
                )
                threading.Thread(
                    target=run_prompt, args=(prompt, f"watch:{f.name}"), daemon=True
                ).start()
        stop_event.wait(interval)


# ------------------------------------------------------------------ cli
def self_test() -> None:
    ok = True
    print("\n=== SELF TEST ===\n")

    pool = core.build_pool()
    print(f"1. Providers    : {'✅ ' + str(len(pool)) + ' ready' if pool else '❌ koi nahi (key daalo ya ollama)'}")
    ok &= bool(pool)

    try:
        p = core.safe_path("../hack.txt")
        print(f"2. Path safety  : ❌ FAIL ({p})")
        ok = False
    except ValueError:
        print("2. Path safety  : ✅ workspace ke bahar block hai")

    try:
        out = core.tool_run_python("print(6*7)")
        print(f"3. Python tool  : ✅ {out}")
    except Exception as e:  # noqa: BLE001
        print(f"3. Python tool  : ❌ {e}")
        ok = False

    try:
        core.tool_write_file("_test.txt", "ok")
        r = core.tool_read_file("_test.txt")
        core.safe_path("_test.txt").unlink()
        print(f"4. File tools   : ✅ read/write ({r})")
    except Exception as e:  # noqa: BLE001
        print(f"4. File tools   : ❌ {e}")
        ok = False

    tasks = load_tasks()
    sched = [j["name"] for j in tasks.get("schedules", []) if j.get("enabled")]
    watch = [j["name"] for j in tasks.get("watch", []) if j.get("enabled")]
    print(f"5. Schedules    : {len(sched)} on {sched}")
    print(f"6. Watch folders: {len(watch)} on {watch}")

    print(f"\n{'✅ Sab theek' if ok else '⚠️  Kuch missing hai'}\n")


def main() -> None:
    load_dotenv(HERE / ".env")

    args = sys.argv[1:]
    if "--list" in args:
        tasks = load_tasks()
        print("\n=== JOBS ===\n")
        for j in all_jobs(tasks):
            status = "ON " if j.get("enabled") else "off"
            when = j.get("at") or f"har {j.get('every_minutes')} min" or ""
            if j["type"] == "watch":
                when = f"folder={j.get('folder')}"
            print(f"  [{status}] {j['type']:8} {j.get('name','?'):20} {when}")
        print(f"\nFile: {TASKS_FILE}\n")
        return

    if "--test" in args:
        self_test()
        return

    if "--run" in args:
        i = args.index("--run")
        name = args[i + 1] if i + 1 < len(args) else ""
        run_job_now(name)
        return

    log("=" * 50)
    log("AUTO AGENT START (Ctrl+C se band karo)")
    tasks = load_tasks()

    # ek baar sab check
    pool = core.build_pool()
    log(f"Providers ready: {len(pool)} -> {[p.label() for p in pool] or 'KOI NAHI'}")

    stop = threading.Event()
    threads = [
        threading.Thread(target=scheduler_loop, args=(stop,), daemon=True),
        threading.Thread(target=watcher_loop, args=(tasks, stop), daemon=True),
    ]
    for t in threads:
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Band kar raha hoon…")
        stop.set()


if __name__ == "__main__":
    main()

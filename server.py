#!/usr/bin/env python3
"""
SUPERAGENT — Ninja AI jaisa apna agent, Railway pe deploy hone wala.

Features:
  - Login (password)
  - Multi-chat with history (SQLite)
  - Har chat ka apna workspace (files alag-alag)
  - Agent tools: files, multi-language code, terminal, web fetch
  - Live streaming + tool chips
  - Artifact preview (HTML live) + ZIP download
  - Free API keys (Groq/Gemini/OpenRouter) — env vars se
  - /healthz for Railway healthcheck

Local:   APP_PASSWORD=admin python server.py
Prod :   gunicorn -k gthread -w 1 --threads 16 -b 0.0.0.0:$PORT server:app
"""

import hashlib
import hmac
import io
import json
import os
import pathlib
import random
import secrets
import sqlite3
import string
import threading
import time
import zipfile

from flask import Flask, Response, jsonify, redirect, request, send_file

import agent as core

HERE = pathlib.Path(__file__).parent.resolve()
def _pick_data_dir(preferred: str) -> pathlib.Path:
    """Railway volume permission fix.

    Railway volume /data root-owned mount karta hai -> container ka non-root user
    (uid 10001) wahan likh nahi sakta. Aise me /tmp/data pe fallback (chats ephemeral,
    par app chalta rahega — crash nahi hoga).
    """
    candidates = [preferred, "/tmp/data", str(HERE / "data")]
    for c in candidates:
        try:
            p = pathlib.Path(c).resolve()
            p.mkdir(parents=True, exist_ok=True)
            probe = p / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            if c != preferred:
                print(f"  ⚠️  {preferred} writable nahi — fallback: {p}", flush=True)
            return p
        except Exception:
            continue
    return pathlib.Path("/tmp/data")


DATA_DIR = _pick_data_dir(os.getenv("DATA_DIR", str(HERE / "data")))
WS_ROOT = DATA_DIR / "workspaces"
WS_ROOT.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "app.db"
SETTINGS_PATH = DATA_DIR / "settings.json"

APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()
if not APP_PASSWORD:
    APP_PASSWORD = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    print(f"\n  ⚠️  APP_PASSWORD set nahi hai. Temporary password: {APP_PASSWORD}\n"
          f"     Railway pe variable set karo: APP_PASSWORD=strong-password\n", flush=True)

SECRET = os.getenv("SECRET_KEY", secrets.token_hex(32))
COOKIE = "sauth"
# NO_AUTH=1 -> login skip (preview/sandboxed iframe me cookies block hote hain)
NO_AUTH = os.getenv("NO_AUTH", "").strip().lower() in {"1", "true", "yes", "on"}
AGENT_LOCK = threading.Lock()

from ui import LOGIN_HTML, APP_HTML  # noqa: E402

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


# ─────────────────────────────────────────────── db
SCHEMA = """
CREATE TABLE IF NOT EXISTS chats(
    id TEXT PRIMARY KEY, title TEXT, created REAL, updated REAL);
CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT,
    content TEXT, meta TEXT, created REAL);
CREATE INDEX IF NOT EXISTS idx_msg_chat ON messages(chat_id, id);
"""


def db():
    """Self-healing connection: dir/DB delete ho jaye to khud bana leta hai.

    Schema idempotent hai (CREATE ... IF NOT EXISTS) — har call pe chalana safe hai.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    WS_ROOT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


def init_db():
    db().close()


init_db()


def now() -> float:
    return time.time()


# ─────────────────────────────────────────────── auth
def token() -> str:
    return hmac.new(SECRET.encode(), APP_PASSWORD.encode(), hashlib.sha256).hexdigest()


def given_token() -> str:
    return (
        request.args.get("t", "")
        or request.headers.get("X-Auth-Token", "")
        or request.cookies.get(COOKIE, "")
    )


def authed() -> bool:
    if NO_AUTH:
        return True
    got = given_token()
    return bool(got) and hmac.compare_digest(got, token())


@app.before_request
def guard():
    if request.path in {"/login", "/healthz", "/favicon.ico"}:
        return None
    if NO_AUTH:
        return None
    # NOTE: token URL (?t=) ko redirect nahi karte — warna token gir jata hai
    # (sandboxed iframe me cookie block hoti hai, token hi auth ka sahara hai)
    if not authed():
        if request.path.startswith("/api/"):
            return jsonify({"error": "unauthorized"}), 401
        return redirect("/login")
    return None


@app.get("/healthz")
def healthz():
    return "ok", 200


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form.get("password", "") or (request.get_json(silent=True) or {}).get("password", "")
        wants_json = (
            request.headers.get("Accept", "").startswith("application/json")
            or request.headers.get("X-Requested-With") == "fetch"
            or request.is_json
        )
        if hmac.compare_digest(pw, APP_PASSWORD):
            if wants_json:
                return jsonify({"ok": True, "token": token()})
            resp = redirect("/")
            resp.set_cookie(COOKIE, token(), httponly=True, samesite="Lax",
                            secure=request.is_secure, max_age=60 * 60 * 24 * 30)
            return resp
        if wants_json:
            return jsonify({"ok": False, "error": "Galat password"}), 401
        return Response(LOGIN_HTML.replace("<!--ERR-->", "Galat password. Dobara try karo."), 401,
                        mimetype="text/html")
    if authed():
        return redirect("/")
    return Response(LOGIN_HTML.replace("<!--ERR-->", ""), mimetype="text/html")


@app.get("/logout")
def logout():
    resp = redirect("/login")
    resp.delete_cookie(COOKIE)
    return resp


def auth_token_json():
    return {"token": token(), "no_auth": NO_AUTH}


# ─────────────────────────────────────────────── settings
def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def apply_settings():
    for k, v in load_settings().items():
        if v:
            os.environ[k] = v


apply_settings()
POOL_CACHE: list = []


def get_pool():
    global POOL_CACHE
    if not POOL_CACHE:
        POOL_CACHE = core.build_pool()
    return POOL_CACHE


# ─────────────────────────────────────────────── chats
@app.get("/api/chats")
def api_chats():
    with db() as con:
        rows = con.execute("SELECT * FROM chats ORDER BY updated DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/chats")
def api_new_chat():
    cid = secrets.token_urlsafe(8)
    with db() as con:
        con.execute("INSERT INTO chats VALUES(?,?,?,?)", (cid, "New chat", now(), now()))
    (WS_ROOT / cid).mkdir(parents=True, exist_ok=True)
    return jsonify({"id": cid, "title": "New chat"})


@app.delete("/api/chats/<cid>")
def api_del_chat(cid):
    with db() as con:
        con.execute("DELETE FROM messages WHERE chat_id=?", (cid,))
        con.execute("DELETE FROM chats WHERE id=?", (cid,))
    return jsonify({"ok": True})


@app.get("/api/chats/<cid>/messages")
def api_messages(cid):
    with db() as con:
        rows = con.execute(
            "SELECT role, content, meta, created FROM messages WHERE chat_id=? ORDER BY id", (cid,)
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["meta"] = json.loads(d["meta"]) if d["meta"] else None
        except json.JSONDecodeError:
            d["meta"] = None
        out.append(d)
    return jsonify(out)


# ─────────────────────────────────────────────── files
def chat_ws(cid: str) -> pathlib.Path:
    p = WS_ROOT / cid
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_in_ws(cid: str, rel: str) -> pathlib.Path:
    root = chat_ws(cid)
    target = (root / rel).resolve()
    if root not in target.parents and target != root:
        raise ValueError("outside workspace")
    return target


@app.get("/api/files")
def api_files():
    cid = request.args.get("chat_id", "")
    root = chat_ws(cid)
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".codegen" not in p.parts:
            out.append({"path": str(p.relative_to(root)), "size": p.stat().st_size})
    return jsonify(out)


@app.get("/api/raw")
def api_raw():
    cid = request.args.get("chat_id", "")
    rel = request.args.get("path", "")
    try:
        p = safe_in_ws(cid, rel)
    except ValueError:
        return "not allowed", 400
    if not p.is_file():
        return "not found", 404
    ext = p.suffix.lower()
    mime = {
        ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8",
        ".css": "text/css", ".js": "application/javascript", ".json": "application/json",
        ".md": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8",
        ".py": "text/plain; charset=utf-8", ".svg": "image/svg+xml",
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif", ".pdf": "application/pdf",
    }.get(ext, "text/plain; charset=utf-8")
    return Response(p.read_bytes(), mimetype=mime)


@app.get("/api/download")
def api_download():
    cid = request.args.get("chat_id", "")
    root = chat_ws(cid)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in root.rglob("*"):
            if p.is_file() and ".codegen" not in p.parts:
                z.write(p, p.relative_to(root))
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True,
                     download_name=f"agent-{cid}.zip")


# ─────────────────────────────────────────────── status / settings
@app.get("/api/status")
def api_status():
    pool = get_pool()
    keyless = any(p.name in ("pollinations",) for p in pool)
    return jsonify({
        "ready": bool(pool),
        "providers": [p.label() for p in pool],
        "model": pool[0].model if pool else None,
        "keyless": keyless,
        "hint": "Bina key free mode" if keyless else None,
    })


@app.post("/api/settings")
def api_settings():
    global POOL_CACHE
    d = request.get_json(force=True) or {}
    provider, key = (d.get("provider") or "").strip(), (d.get("key") or "").strip()
    preset = core.PRESETS.get(provider)
    if not preset or not key:
        return jsonify({"error": "provider/key missing"}), 400
    s = load_settings()
    s[preset["key_env"]] = key
    s["PROVIDER"] = provider
    SETTINGS_PATH.write_text(json.dumps(s, indent=2))
    apply_settings()
    POOL_CACHE = []
    return jsonify({"ok": True, "ready": bool(get_pool())})


# ─────────────────────────────────────────────── chat (SSE)
@app.post("/api/chat")
def api_chat():
    d = request.get_json(force=True) or {}
    cid, task = d.get("chat_id", ""), (d.get("task") or "").strip()
    if not cid or not task:
        return jsonify({"error": "chat_id/task missing"}), 400
    pool = get_pool()
    if not pool:
        return jsonify({"error": "no_provider"}), 400

    with db() as con:
        row = con.execute("SELECT title FROM chats WHERE id=?", (cid,)).fetchone()
        if not row:
            con.execute("INSERT INTO chats VALUES(?,?,?,?)", (cid, "New chat", now(), now()))
            title = "New chat"
        else:
            title = row["title"]
        con.execute("INSERT INTO messages(chat_id,role,content,meta,created) VALUES(?,?,?,?,?)",
                    (cid, "user", task, None, now()))
        if title == "New chat":
            newtitle = (task[:42] + "…") if len(task) > 42 else task
            con.execute("UPDATE chats SET title=?, updated=? WHERE id=?", (newtitle, now(), cid))
        else:
            con.execute("UPDATE chats SET updated=? WHERE id=?", (now(), cid))
        hist = con.execute(
            "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT 20", (cid,)
        ).fetchall()

    history = [{"role": r["role"], "content": r["content"]} for r in reversed(hist) if r["content"]]

    def gen():
        import queue

        q: "queue.Queue" = queue.Queue()
        events_meta = []

        def emit(kind, data):
            if kind in ("tool", "error"):
                events_meta.append({"kind": kind, "data": data})
            q.put({"kind": kind, "data": data})

        # NOTE: "delta" events stream jaate hain (DB me sirf final jawab)

        def worker():
            try:
                with AGENT_LOCK:
                    core.set_workspace(chat_ws(cid))
                    st = core.AgentState(pool)
                    st.messages = [{"role": "system", "content": core.SYSTEM_PROMPT}] + history
                    final = st.run(task, emit)
                    with db() as con:
                        con.execute(
                            "INSERT INTO messages(chat_id,role,content,meta,created) VALUES(?,?,?,?,?)",
                            (cid, "assistant", final, json.dumps(events_meta), now()),
                        )
            except Exception as e:  # noqa: BLE001
                emit("error", str(e))
            finally:
                q.put(None)

        threading.Thread(target=worker, daemon=True).start()
        while True:
            item = q.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"
        yield 'data: {"kind":"done"}\n\n'

    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ─────────────────────────────────────────────── ui
@app.get("/")
def index():
    return Response(APP_HTML, mimetype="text/html")






if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    init_db()
    print(f"\n  🥷 SuperAgent -> http://localhost:{port}")
    print(f"  🔑 Password  -> {APP_PASSWORD}")
    print(f"  📁 Data      -> {DATA_DIR}")
    print(f"  🆓 Keyless   -> {'ON (koi API key nahi chahiye)' if not any(os.getenv(k) for k in ('GROQ_API_KEY','GEMINI_API_KEY','OPENROUTER_API_KEY')) else 'OFF (key milee)'}\n", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

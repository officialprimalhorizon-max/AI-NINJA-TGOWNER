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


LOGIN_HTML = r"""<!doctype html><html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Login — SuperAgent</title>
<style>
*{box-sizing:border-box}
body{margin:0;height:100vh;display:grid;place-items:center;background:#07090d;color:#e8eef7;
font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.card{width:min(380px,92vw);background:#0e1218;border:1px solid #1e2633;border-radius:18px;padding:28px}
.logo{width:46px;height:46px;border-radius:13px;background:linear-gradient(135deg,#c3f53c,#6ee7b7);
display:grid;place-items:center;font-size:22px;margin-bottom:16px}
h1{font-size:20px;margin:0 0 6px}p{color:#7d8ea6;font-size:13px;margin:0 0 20px;line-height:1.6}
input{width:100%;background:#080b10;border:1px solid #1e2633;color:#e8eef7;border-radius:10px;
padding:12px 14px;font-size:14px;outline:none;font-family:inherit}
input:focus{border-color:#3d5a2a;box-shadow:0 0 0 3px #c3f53c18}
button{width:100%;margin-top:12px;padding:12px;border:none;border-radius:10px;font-weight:800;
background:linear-gradient(135deg,#c3f53c,#94e63a);color:#0a1204;font-size:14px;cursor:pointer}
.err{color:#ff7b7b;font-size:12.5px;margin-top:12px;min-height:16px}
</style></head><body>
<div class="card">
  <div class="logo">🥷</div>
  <h1>SuperAgent</h1>
  <p>Apna private AI agent. Password daalo jo Railway ke <code>APP_PASSWORD</code> variable me set kiya hai.</p>
  <form id="f" onsubmit="return doLogin(event)">
    <input id="pw" type="password" placeholder="Password" autofocus autocomplete="current-password">
    <button type="submit" id="btn">Login</button>
  </form>
  <div class="err" id="err"><!--ERR--></div>
</div>
<script>
async function doLogin(e){
  e.preventDefault();
  const pw=document.getElementById('pw').value, err=document.getElementById('err'), btn=document.getElementById('btn');
  if(!pw){err.textContent='Password daalo';return false}
  btn.disabled=true; btn.textContent='Checking…'; err.textContent='';
  try{
    const r=await fetch('/login',{method:'POST',
      headers:{'Content-Type':'application/json','Accept':'application/json','X-Requested-With':'fetch'},
      body:JSON.stringify({password:pw})});
    const d=await r.json().catch(()=>({}));
    if(r.ok && d.ok){
      // cookie block ho sakti hai (sandboxed iframe) -> token URL fallback
      location.replace('/?t='+encodeURIComponent(d.token));
    } else {
      err.textContent=d.error||('Login fail (HTTP '+r.status+')');
      btn.disabled=false; btn.textContent='Login';
    }
  }catch(ex){
    err.textContent='Network error: '+ex.message;
    btn.disabled=false; btn.textContent='Login';
  }
  return false;
}
</script>
</body></html>"""


APP_HTML = r"""<!doctype html><html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>SuperAgent</title>
<style>
:root{--bg:#07090d;--panel:#0d1117;--panel2:#0a0e14;--line:#1b2430;--text:#e8eef7;
--muted:#7d8ea6;--lime:#c3f53c;--lime2:#94e63a;--err:#ff6b6b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);height:100vh;overflow:hidden;
font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.app{display:grid;grid-template-columns:252px minmax(0,1fr) 0;height:100vh;transition:.2s}
.app.files-open{grid-template-columns:252px minmax(0,1fr) 300px}
@media(max-width:900px){.app,.app.files-open{grid-template-columns:1fr}.side{display:none}}
/* sidebar */
.side{background:var(--panel2);border-right:1px solid var(--line);display:flex;flex-direction:column}
.brand{display:flex;align-items:center;gap:9px;padding:16px 14px 10px}
.brand .ico{width:30px;height:30px;border-radius:9px;background:linear-gradient(135deg,var(--lime),#6ee7b7);
display:grid;place-items:center;font-size:15px}
.brand b{font-size:14px;letter-spacing:.3px}
.newbtn{margin:6px 12px 10px;padding:10px;border-radius:10px;border:1px solid #2b3a1c;
background:linear-gradient(135deg,#1a2410,#101a0a);color:var(--lime);font-weight:700;font-size:13px;cursor:pointer;
display:flex;align-items:center;justify-content:center;gap:7px}
.newbtn:hover{background:#1f2c12;border-color:#3d5a2a}
.chats{flex:1;overflow-y:auto;padding:0 8px}
.chatitem{display:flex;align-items:center;gap:8px;padding:9px 10px;border-radius:8px;cursor:pointer;
font-size:12.8px;color:#c2cfdf;transition:.12s}
.chatitem:hover{background:#141b24}
.chatitem.on{background:#18220f;color:var(--lime);border:1px solid #2b3a1c}
.chatitem .t{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chatitem .del{opacity:0;font-size:14px;color:#5c6a7d;padding:0 3px}
.chatitem:hover .del{opacity:1}
.chatitem .del:hover{color:var(--err)}
.sidefoot{border-top:1px solid var(--line);padding:10px 12px;display:flex;flex-direction:column;gap:7px}
.badge{font-size:10.5px;padding:5px 8px;border-radius:999px;background:#101a0a;border:1px solid #2b3a1c;
color:var(--lime);text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.badge.bad{background:#1c0f0f;border-color:#3a1c1c;color:#ff8f8f}
.lnk{font-size:11.5px;color:#66768c;text-align:center;text-decoration:none}
.lnk:hover{color:var(--lime)}
/* main */
.main{display:flex;flex-direction:column;min-width:0;height:100vh}
.top{display:flex;align-items:center;gap:10px;padding:11px 16px;border-bottom:1px solid var(--line);background:var(--panel2)}
.top h2{font-size:13.5px;margin:0;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:45vw}
.sp{flex:1}
.btn{background:#141b24;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:7px 11px;
font-size:12px;cursor:pointer;transition:.15s}
.btn:hover{background:#1b2430;border-color:#2b3a4a}
.btn.acc{background:#18220f;border-color:#2b3a1c;color:var(--lime)}
#chat{flex:1;overflow-y:auto;padding:20px 16px 8px}
.wrap{max-width:800px;margin:0 auto}
.msg{display:flex;gap:10px;margin-bottom:16px;animation:in .18s ease}
@keyframes in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.av{width:27px;height:27px;border-radius:8px;flex:0 0 auto;display:grid;place-items:center;font-size:11px;font-weight:800}
.msg.user .av{background:#1b2b3f;color:#9cc4ff}
.msg.ai .av{background:linear-gradient(135deg,var(--lime),#6ee7b7);color:#0a1204}
.bubble{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:11px 14px;
font-size:13.8px;line-height:1.62;white-space:pre-wrap;overflow-wrap:anywhere;max-width:100%}
.msg.user .bubble{background:#111a26;border-color:#1e2c3d}
.bubble code{background:#060a10;border:1px solid var(--line);padding:1px 5px;border-radius:5px;font-size:12.5px;
font-family:ui-monospace,Menlo,Consolas,monospace}
.bubble pre{background:#05080d;border:1px solid var(--line);padding:10px;border-radius:9px;overflow-x:auto;font-size:12.3px}
.bubble pre code{background:none;border:none;padding:0}
.tool{display:inline-flex;gap:5px;background:#0b1520;border:1px solid #1d3a52;color:#7fc2ff;font-size:11px;
padding:3px 8px;border-radius:999px;margin:3px 5px 3px 0;font-family:ui-monospace,monospace}
.tool.done{border-color:#284a1c;color:#a8e07a;background:#0d160a}
.typing i{width:5px;height:5px;border-radius:50%;background:var(--muted);display:inline-block;margin-right:3px;
animation:b 1.2s infinite}.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}
@keyframes b{0%,60%,100%{opacity:.25;transform:translateY(0)}30%{opacity:1;transform:translateY(-3px)}}
.composer{border-top:1px solid var(--line);background:var(--panel2);padding:11px 16px 14px}
.cwrap{max-width:800px;margin:0 auto;display:flex;gap:8px;align-items:flex-end;background:#0a0e14;
border:1px solid var(--line);border-radius:13px;padding:7px 7px 7px 13px}
.cwrap:focus-within{border-color:#3d5a2a;box-shadow:0 0 0 3px #c3f53c14}
textarea{flex:1;background:none;border:none;color:var(--text);font-size:13.8px;resize:none;outline:none;
max-height:150px;min-height:22px;line-height:1.5;font-family:inherit;padding:4px 0}
.send{width:34px;height:34px;border-radius:9px;border:none;background:linear-gradient(135deg,var(--lime),var(--lime2));
color:#0a1204;cursor:pointer;display:grid;place-items:center;flex:0 0 auto}
.send:disabled{opacity:.35;cursor:not-allowed}
.hint{max-width:800px;margin:7px auto 0;color:#54657c;font-size:10.5px;text-align:center}
/* files panel */
.files{background:var(--panel2);border-left:1px solid var(--line);display:none;flex-direction:column;overflow:hidden}
.app.files-open .files{display:flex}
.fhead{display:flex;align-items:center;gap:8px;padding:12px 12px 8px;font-size:11px;color:var(--muted);
text-transform:uppercase;letter-spacing:.7px;font-weight:700}
#filelist{flex:1;overflow-y:auto;padding:0 8px 10px}
.fitem{display:flex;align-items:center;gap:7px;padding:8px 9px;border-radius:8px;cursor:pointer;font-size:12.2px}
.fitem:hover{background:#141b24}
.fitem .nm{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fitem .sz{color:#54657c;font-size:10px}
.empty{color:#54657c;font-size:11.5px;padding:8px 14px;line-height:1.6}
.ffoot{padding:9px 10px;border-top:1px solid var(--line);display:flex;gap:7px}
.ffoot .btn{flex:1;text-align:center}
/* preview modal */
.overlay{position:fixed;inset:0;background:#040609dd;backdrop-filter:blur(3px);display:none;z-index:60;padding:22px}
.overlay.on{display:flex;flex-direction:column;gap:10px}
.phead{display:flex;align-items:center;gap:10px;color:#c8d6e8;font-size:12.5px}
.phead .btn{margin-left:auto}
iframe{flex:1;width:100%;border:1px solid var(--line);border-radius:12px;background:#fff}
pre.pcode{flex:1;overflow:auto;background:#05080d;border:1px solid var(--line);border-radius:12px;padding:14px;
font-size:12.3px;color:#cfe0f2;white-space:pre-wrap;margin:0}
</style></head><body>
<div class="app" id="app">
  <aside class="side">
    <div class="brand"><div class="ico">🥷</div><b>SuperAgent</b></div>
    <button class="newbtn" onclick="newChat()">＋ New chat</button>
    <div class="chats" id="chats"></div>
    <div class="sidefoot">
      <div class="badge" id="pbadge">checking…</div>
      <a class="lnk" href="/logout">Logout</a>
    </div>
  </aside>

  <div class="main">
    <div class="top">
      <h2 id="ctitle">New chat</h2>
      <div class="sp"></div>
      <button class="btn" onclick="toggleFiles()">📁 Files</button>
      <a class="btn" id="dl" href="#" download>⬇ ZIP</a>
      <button class="btn" onclick="setKey()">⚙ Key</button>
    </div>
    <div id="chat"><div class="wrap" id="msgs"></div></div>
    <div class="composer">
      <div class="cwrap">
        <textarea id="input" rows="1" placeholder="Kaam bolo… jaise: 'ek portfolio website banao, 3 pages'"></textarea>
        <button class="send" id="send" onclick="send()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/></svg>
        </button>
      </div>
      <div class="hint">Enter = bhejo · Shift+Enter = nayi line · Agent files banana, code chalana, terminal sab khud karega</div>
    </div>
  </div>

  <aside class="files">
    <div class="fhead"><span>Workspace</span><div class="sp"></div><span id="fcount"></span></div>
    <div id="filelist"></div>
    <div class="ffoot">
      <button class="btn acc" onclick="loadFiles()">↻ Refresh</button>
      <button class="btn" onclick="toggleFiles()">✕</button>
    </div>
  </aside>
</div>

<div class="overlay" id="ov" onclick="if(event.target===this)closePrev()">
  <div class="phead"><span id="pname">preview</span><span id="psize"></span>
    <button class="btn" onclick="closePrev()">✕ Close</button></div>
  <div id="pbody" style="flex:1;display:flex;min-height:0"></div>
</div>

<script>
let chats=[], current=null, busy=false, providers=[], keylessMode=false;
const $=id=>document.getElementById(id);

/* ── auth token (cookie block hone par bhi kaam kare) ── */
let _T = new URLSearchParams(location.search).get('t') || '';
try{ if(_T) sessionStorage.setItem('sat', _T); else _T = sessionStorage.getItem('sat') || ''; }catch(e){}
if(new URLSearchParams(location.search).get('t')){ try{ history.replaceState(null,'','/'); }catch(e){} }
const _origFetch = window.fetch.bind(window);
window.fetch = (u, o={}) => {
  if(typeof u === 'string' && u.startsWith('/api/')){
    u += (u.includes('?')?'&':'?') + 't=' + encodeURIComponent(_T);
    o = {...o, headers: {...(o.headers||{}), 'X-Auth-Token': _T}};
  }
  return _origFetch(u, o);
};
const withT = u => u + (u.includes('?')?'&':'?') + 't=' + encodeURIComponent(_T);
const esc=s=>(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
function md(s){s=esc(s);
  s=s.replace(/```([\s\S]*?)```/g,(m,c)=>'<pre><code>'+c.replace(/^\n/,'')+'</code></pre>');
  s=s.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>');return s;}
function scroll(){const c=$('chat');c.scrollTop=c.scrollHeight}

async function status(){
  try{const r=await fetch('/api/status');const d=await r.json();providers=d.providers||[];keylessMode=!!d.keyless;
    const b=$('pbadge');
    if(d.ready){
      const prov=(d.providers[0]||'').split(':')[0];
      b.className='badge';
      b.textContent=(d.keyless?'🆓 free · ':'')+prov+' · '+(d.model||'')
    }
    else{b.className='badge bad';b.textContent='No provider'}
  }catch(e){}
}

async function loadChats(){
  const r=await fetch('/api/chats');chats=await r.json();
  $('chats').innerHTML=chats.map(c=>
    `<div class="chatitem ${c.id===current?'on':''}" onclick="openChat('${c.id}')">
      <span>💬</span><span class="t">${esc(c.title)}</span>
      <span class="del" onclick="event.stopPropagation();delChat('${c.id}')">✕</span></div>`).join('')
    || '<div class="empty">Abhi koi chat nahi.<br>New chat dabao.</div>';
}

async function newChat(){
  const r=await fetch('/api/chats',{method:'POST'});const c=await r.json();
  current=c.id;$('ctitle').textContent=c.title;$('msgs').innerHTML='';
  $('dl').href=withT(`/api/download?chat_id=${c.id}`);await loadChats();loadFiles();
}

async function openChat(id){
  current=id;const c=chats.find(x=>x.id===id);
  $('ctitle').textContent=c?c.title:'Chat';$('dl').href=withT(`/api/download?chat_id=${id}`);
  await loadChats();
  const r=await fetch(`/api/chats/${id}/messages`);const msgs=await r.json();
  const box=$('msgs');box.innerHTML='';
  msgs.forEach(m=>{
    if(m.role==='user')addMsg('user',m.content);
    else{
      const b=addMsg('ai','');
      if(m.meta&&m.meta.length){const chips=document.createElement('div');
        m.meta.filter(e=>e.kind==='tool').forEach(e=>{const s=document.createElement('span');
          s.className='tool done';s.textContent='🔧 '+e.data.name+(e.data.target?' · '+e.data.target:'');
          chips.appendChild(s)});
        b.appendChild(chips);b.appendChild(document.createElement('br'));}
      b.insertAdjacentHTML('beforeend',md(m.content||''));
    }
  });
  loadFiles();scroll();
}

async function delChat(id){
  if(!confirm('Ye chat delete?'))return;
  await fetch('/api/chats/'+id,{method:'DELETE'});
  if(current===id){current=null;$('msgs').innerHTML='';$('ctitle').textContent='New chat'}
  loadChats();
}

function addMsg(role,text){
  const d=document.createElement('div');d.className='msg '+(role==='user'?'user':'ai');
  d.innerHTML=`<div class="av">${role==='user'?'TU':'AI'}</div><div class="bubble">${md(text)}</div>`;
  $('msgs').appendChild(d);scroll();return d.querySelector('.bubble');
}

function toggleFiles(){$('app').classList.toggle('files-open');if($('app').classList.contains('files-open'))loadFiles()}

async function loadFiles(){
  if(!current)return;
  const r=await fetch('/api/files?chat_id='+current);const fs=await r.json();
  $('fcount').textContent=fs.length;
  $('filelist').innerHTML=fs.length?fs.map(f=>
    `<div class="fitem" onclick="preview('${f.path.replace(/'/g,"\\'")}')">
      <span>${/\.(html?|css|js)$/i.test(f.path)?'🌐':/\.(png|jpe?g|webp|gif|svg)$/i.test(f.path)?'🖼️':'📄'}</span>
      <span class="nm">${esc(f.path)}</span><span class="sz">${fmt(f.size)}</span></div>`).join('')
    :'<div class="empty">Abhi koi file nahi.<br>Agent se kuch banao.</div>';
}
const fmt=n=>n<1024?n+' B':(n/1024).toFixed(1)+' KB';

async function preview(p){
  if(!current)return;
  $('ov').classList.add('on');$('pname').textContent=p;
  const url=withT(`/api/raw?chat_id=${current}&path=${encodeURIComponent(p)}`);
  const isHtml=/\.(html?)$/i.test(p), isImg=/\.(png|jpe?g|webp|gif|svg)$/i.test(p), isPdf=/\.pdf$/i.test(p);
  if(isHtml){$('pbody').innerHTML=`<iframe sandbox="allow-scripts allow-forms allow-modals" src="${url}"></iframe>`}
  else if(isImg){$('pbody').innerHTML=`<div style="flex:1;display:grid;place-items:center;background:#05080d;border-radius:12px"><img src="${url}" style="max-width:100%;max-height:100%;border-radius:8px"></div>`}
  else if(isPdf){$('pbody').innerHTML=`<iframe src="${url}"></iframe>`}
  else{const r=await fetch(url);const t=await r.text();
    $('pbody').innerHTML=`<pre class="pcode">${esc(t.slice(0,120000))}</pre>`}
}
function closePrev(){$('ov').classList.remove('on');$('pbody').innerHTML=''}

async function send(){
  if(busy)return;
  async function setKey(){
  const p=prompt('Provider? (groq / gemini / openrouter / mistral)','groq');
  if(!p)return;
  const k=prompt('API key paste karo:');
  if(!k)return;
  const r=await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({provider:p.trim(),key:k.trim()})});
  const d=await r.json();
  alert(d.ready?'✅ Key set ho gayi!':'❌ Key save nahi hui, dobara try karo');
  await status();
}

const ta=$('input');const task=ta.value.trim();if(!task)return;
  if(!current)await newChat();
  if(!providers.length){alert('Pehle API key set karo (Railway variables ya /api/settings)');return}
  ta.value='';ta.style.height='auto';
  addMsg('user',task);
  busy=true;$('send').disabled=true;
  const bubble=addMsg('ai','');
  bubble.innerHTML='<span class="typing"><i></i><i></i><i></i></span>';
  const chips=document.createElement('div');bubble.appendChild(chips);
  const txt=document.createElement('div');bubble.appendChild(txt);
  let acc='';
  try{
    const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({chat_id:current,task})});
    if(!res.ok){const e=await res.json().catch(()=>({}));throw new Error(e.error||'server error')}
    const rd=res.body.getReader(),dec=new TextDecoder();let buf='';
    while(true){
      const {value,done}=await rd.read();if(done)break;
      buf+=dec.decode(value,{stream:true});
      let i;
      while((i=buf.indexOf('\n\n'))>=0){
        const chunk=buf.slice(0,i);buf=buf.slice(i+2);
        if(!chunk.startsWith('data: '))continue;
        let ev;try{ev=JSON.parse(chunk.slice(6))}catch(e){continue}
        if(ev.kind==='tool'){const s=document.createElement('span');s.className='tool';
          s.textContent='🔧 '+ev.data.name+(ev.data.target?' · '+ev.data.target:'');chips.appendChild(s);scroll()}
        else if(ev.kind==='delta'){
          acc+=ev.data;
          txt.textContent=acc;scroll();
        }
        else if(ev.kind==='final'){acc=ev.data;txt.innerHTML=md(acc);
          chips.querySelectorAll('.tool').forEach(x=>x.classList.add('done'));scroll()}
        else if(ev.kind==='error'){txt.innerHTML='<span style="color:#ff7b7b">⚠️ '+esc(ev.data)+'</span>';scroll()}
      }
    }
    if(!acc&&!txt.innerHTML)txt.textContent='(khali jawab)';
  }catch(e){txt.innerHTML='<span style="color:#ff7b7b">⚠️ '+esc(e.message)+'</span>'}
  busy=false;$('send').disabled=false;
  loadFiles();loadChats();status();
}

async function setKey(){
  const p=prompt('Provider? (groq / gemini / openrouter / mistral)','groq');
  if(!p)return;
  const k=prompt('API key paste karo:');
  if(!k)return;
  const r=await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({provider:p.trim(),key:k.trim()})});
  const d=await r.json();
  alert(d.ready?'✅ Key set ho gayi!':'❌ Key save nahi hui, dobara try karo');
  await status();
}

const ta=$('input');
ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
ta.addEventListener('input',()=>{ta.style.height='auto';ta.style.height=Math.min(ta.scrollHeight,150)+'px'});

(async function init(){
  await status();await loadChats();
  if(chats.length)await openChat(chats[0].id);else await newChat();
})();
</script></body></html>"""


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    init_db()
    print(f"\n  🥷 SuperAgent -> http://localhost:{port}")
    print(f"  🔑 Password  -> {APP_PASSWORD}")
    print(f"  📁 Data      -> {DATA_DIR}")
    print(f"  🆓 Keyless   -> {'ON (koi API key nahi chahiye)' if not any(os.getenv(k) for k in ('GROQ_API_KEY','GEMINI_API_KEY','OPENROUTER_API_KEY')) else 'OFF (key milee)'}\n", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

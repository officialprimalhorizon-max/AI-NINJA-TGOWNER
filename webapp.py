#!/usr/bin/env python3
"""
Web UI for Private Agent — apna ChatGPT, apne computer pe.
Chalao:  python webapp.py   ->  http://localhost:5000
"""

import json
import pathlib
import re

from flask import Flask, Response, jsonify, request, send_from_directory

import agent as core

app = Flask(__name__)
STATE_FILE = core.HERE / ".env"
state = None  # global AgentState


def get_state():
    global state
    if state is None:
        pool = core.build_pool()
        state = core.AgentState(pool)
    return state


def parse_env(path: pathlib.Path) -> dict:
    data = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data


def save_env(updates: dict) -> None:
    existing = {}
    order = []
    if STATE_FILE.exists():
        for line in STATE_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k = line.split("=", 1)[0].strip()
                order.append(k)
                existing[k] = line.split("=", 1)[1].strip()
    existing.update(updates)
    lines = ["# Private Agent config (auto-generated)", ""]
    for k in order:
        if k in existing and existing[k] != "":
            lines.append(f"{k}={existing[k]}")
    for k, v in updates.items():
        if k not in order and v:
            lines.append(f"{k}={v}")
    STATE_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ pages
@app.get("/")
def index():
    return Response(HTML, mimetype="text/html")


# ------------------------------------------------------------------ api
@app.get("/api/status")
def status():
    st = get_state()
    p = st.current
    return jsonify(
        {
            "ready": bool(st.pool),
            "provider": p.name if p else None,
            "model": p.model if p else None,
            "providers": [x.label() for x in st.pool],
            "workspace": str(core.WORKSPACE),
            "messages": len(st.messages) - 1,
        }
    )


@app.get("/api/files")
def files():
    out = []
    for p in sorted(core.WORKSPACE.rglob("*")):
        if p.is_file():
            out.append(
                {
                    "path": str(p.relative_to(core.WORKSPACE)),
                    "size": p.stat().st_size,
                }
            )
    return jsonify(out)


@app.get("/api/file")
def file_content():
    rel = request.args.get("path", "")
    try:
        target = core.safe_path(rel)
    except ValueError:
        return jsonify({"error": "not allowed"}), 400
    if not target.is_file():
        return jsonify({"error": "not found"}), 404
    text = target.read_text(encoding="utf-8", errors="replace")
    return jsonify({"path": rel, "content": text[:200000]})


@app.post("/api/settings")
def settings():
    data = request.get_json(force=True) or {}
    provider = (data.get("provider") or "").strip()
    key = (data.get("key") or "").strip()
    updates = {}
    if provider:
        updates["PROVIDER"] = provider
        preset = core.PRESETS.get(provider)
        if preset and key and provider not in {"ollama", "custom"}:
            updates[preset["key_env"]] = key
    if updates:
        save_env(updates)
        for k, v in updates.items():
            import os

            os.environ[k] = v
        global state
        state = None  # rebuild
    return jsonify({"ok": True, "ready": bool(get_state().pool)})


@app.post("/api/reset")
def reset():
    st = get_state()
    st.messages = [{"role": "system", "content": core.SYSTEM_PROMPT}]
    return jsonify({"ok": True})


@app.post("/api/chat")
def chat():
    st = get_state()
    task = (request.get_json(force=True) or {}).get("task", "").strip()
    if not task:
        return jsonify({"error": "empty"}), 400
    if not st.pool:
        return jsonify({"error": "no_provider"}), 400

    def gen():
        import queue
        import threading

        q: queue.Queue = queue.Queue()

        def emit(kind, data):
            q.put({"kind": kind, "data": data})

        def worker():
            try:
                st.run(task, emit)
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
        yield "data: [DONE]\n\n"

    return Response(gen(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


# ------------------------------------------------------------------ html
HTML = r"""<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mera Agent — private AI</title>
<style>
  :root{
    --bg:#0b0e14; --panel:#121722; --panel2:#0f1420; --line:#1f2838;
    --text:#e6edf7; --muted:#8aa0bd; --accent:#5b8cff; --accent2:#22d3a6;
    --warn:#ffb020; --err:#ff5c5c;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;height:100vh;overflow:hidden}
  .app{display:grid;grid-template-columns:minmax(0,1fr) 300px;height:100vh}
  @media(max-width:860px){.app{grid-template-columns:1fr}.side{display:none}}
  /* header */
  header{display:flex;align-items:center;gap:12px;padding:14px 18px;border-bottom:1px solid var(--line);background:var(--panel2)}
  .logo{width:30px;height:30px;border-radius:9px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:grid;place-items:center;font-weight:800;font-size:15px;color:#06111f}
  header h1{font-size:15px;margin:0;font-weight:700;letter-spacing:.2px}
  .pill{font-size:11px;padding:4px 9px;border-radius:999px;border:1px solid var(--line);color:var(--muted);background:#0c111b;white-space:nowrap}
  .pill.ok{color:#0a1a13;background:var(--accent2);border-color:transparent;font-weight:700}
  .pill.bad{color:#2a0d0d;background:var(--err);border-color:transparent;font-weight:700}
  .spacer{flex:1}
  button{font-family:inherit}
  .btn{background:#1a2233;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:7px 12px;font-size:12.5px;cursor:pointer;transition:.15s}
  .btn:hover{background:#222c42;border-color:#2d3b57}
  .btn.primary{background:linear-gradient(135deg,var(--accent),#6f5bff);border:none;font-weight:700;color:#fff}
  .btn.ghost{background:transparent}
  /* chat */
  .main{display:flex;flex-direction:column;min-width:0;height:100vh}
  #chat{flex:1;overflow-y:auto;padding:22px 20px 10px;scroll-behavior:smooth}
  .wrap{max-width:820px;margin:0 auto}
  .msg{display:flex;gap:11px;margin-bottom:18px;animation:in .18s ease}
  @keyframes in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
  .av{width:28px;height:28px;border-radius:8px;flex:0 0 auto;display:grid;place-items:center;font-size:12px;font-weight:800}
  .msg.user .av{background:#22314d;color:#9dc0ff}
  .msg.ai .av{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#06111f}
  .bubble{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:11px 14px;font-size:14px;line-height:1.62;white-space:pre-wrap;word-break:break-word;max-width:100%;overflow-wrap:anywhere}
  .msg.user .bubble{background:#16233a;border-color:#22304a}
  .bubble code{background:#0a0f18;border:1px solid var(--line);padding:1px 5px;border-radius:5px;font-size:12.5px;font-family:ui-monospace,Menlo,Consolas,monospace}
  .bubble pre{background:#080c14;border:1px solid var(--line);padding:11px;border-radius:9px;overflow-x:auto;font-size:12.5px;line-height:1.5}
  .bubble pre code{background:none;border:none;padding:0}
  .tool{display:inline-flex;align-items:center;gap:6px;background:#0d1a2b;border:1px solid #1d3a5c;color:#8fc2ff;font-size:11.5px;padding:4px 9px;border-radius:999px;margin:3px 5px 3px 0;font-family:ui-monospace,monospace}
  .tool.done{border-color:#1c4a3c;color:#7ee2c0;background:#0c1f1a}
  .typing{display:inline-flex;gap:4px;padding:6px 2px}
  .typing i{width:6px;height:6px;border-radius:50%;background:var(--muted);animation:b 1.2s infinite}
  .typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}
  @keyframes b{0%,60%,100%{opacity:.25;transform:translateY(0)}30%{opacity:1;transform:translateY(-3px)}}
  /* composer */
  .composer{border-top:1px solid var(--line);background:var(--panel2);padding:12px 18px 16px}
  .cwrap{max-width:820px;margin:0 auto;display:flex;gap:9px;align-items:flex-end;background:#0d121c;border:1px solid var(--line);border-radius:14px;padding:8px 8px 8px 14px}
  .cwrap:focus-within{border-color:#2f4a78;box-shadow:0 0 0 3px #1b2c4a55}
  textarea{flex:1;background:none;border:none;color:var(--text);font-size:14px;resize:none;outline:none;max-height:150px;min-height:24px;line-height:1.5;font-family:inherit;padding:4px 0}
  .send{width:36px;height:36px;border-radius:10px;border:none;background:linear-gradient(135deg,var(--accent),#6f5bff);color:#fff;cursor:pointer;display:grid;place-items:center;flex:0 0 auto}
  .send:disabled{opacity:.4;cursor:not-allowed}
  .hint{max-width:820px;margin:8px auto 0;color:#5f7391;font-size:11px;text-align:center}
  /* sidebar */
  .side{border-left:1px solid var(--line);background:var(--panel2);display:flex;flex-direction:column;height:100vh}
  .side h2{font-size:11px;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);margin:16px 16px 8px;font-weight:700}
  #files{flex:1;overflow-y:auto;padding:0 8px 12px}
  .file{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;cursor:pointer;font-size:12.5px;color:#c3d2e6;transition:.12s}
  .file:hover{background:#182136}
  .file .nm{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .file .sz{color:#5f7391;font-size:10.5px}
  .empty{color:#5f7391;font-size:12px;padding:10px 16px;line-height:1.6}
  .sidefoot{padding:10px 12px;border-top:1px solid var(--line);display:flex;gap:8px}
  /* modal */
  .overlay{position:fixed;inset:0;background:#04070ccc;backdrop-filter:blur(3px);display:none;place-items:center;padding:18px;z-index:50}
  .overlay.on{display:grid}
  .modal{background:var(--panel);border:1px solid var(--line);border-radius:16px;width:min(520px,100%);padding:20px;box-shadow:0 20px 60px #000a;max-height:90vh;overflow-y:auto}
  .modal h3{margin:0 0 4px;font-size:16px}
  .modal p{color:var(--muted);font-size:12.5px;margin:0 0 16px;line-height:1.6}
  label{display:block;font-size:11.5px;color:var(--muted);margin:12px 0 6px;font-weight:600;letter-spacing:.3px}
  select,input{width:100%;background:#0b1018;border:1px solid var(--line);color:var(--text);border-radius:9px;padding:10px 12px;font-size:13px;outline:none;font-family:inherit}
  select:focus,input:focus{border-color:#2f4a78}
  .note{font-size:11.5px;color:#7d93b3;line-height:1.65;background:#0e1521;border:1px solid var(--line);border-radius:9px;padding:10px 12px;margin-top:12px}
  .note a{color:#7fb0ff}
  .row{display:flex;gap:9px;margin-top:18px}
  .row .btn{flex:1;padding:10px}
  .prev{font-family:ui-monospace,monospace;font-size:11.5px;background:#080c14;border:1px solid var(--line);border-radius:9px;padding:12px;max-height:45vh;overflow:auto;white-space:pre-wrap;margin-top:10px;display:none}
  .toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%) translateY(80px);background:#16233a;border:1px solid #2b3d5c;padding:10px 18px;border-radius:10px;font-size:13px;transition:.25s;z-index:60}
  .toast.on{transform:translateX(-50%) translateY(0)}
</style>
</head>
<body>
<div class="app">
  <div class="main">
    <header>
      <div class="logo">AI</div>
      <h1>Mera Agent</h1>
      <span class="pill" id="status">checking…</span>
      <div class="spacer"></div>
      <button class="btn ghost" onclick="resetChat()">New chat</button>
      <button class="btn" onclick="openSettings()">⚙ Settings</button>
    </header>

    <div id="chat"><div class="wrap" id="msgs"></div></div>

    <div class="composer">
      <div class="cwrap">
        <textarea id="input" rows="1" placeholder="Kuch bhi kaam do… jaise: 'ek calculator banao HTML me'"></textarea>
        <button class="send" id="send" onclick="send()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/></svg>
        </button>
      </div>
      <div class="hint">Enter = bhejo · Shift+Enter = nayi line · Files right side me dikhengi</div>
    </div>
  </div>

  <aside class="side">
    <h2>Workspace files</h2>
    <div id="files"><div class="empty">Abhi koi file nahi.<br>Agent se kuch banao.</div></div>
    <div class="sidefoot">
      <button class="btn" style="flex:1" onclick="loadFiles()">↻ Refresh</button>
    </div>
  </aside>
</div>

<div class="overlay" id="overlay" onclick="if(event.target===this)closeSettings()">
  <div class="modal">
    <h3>⚙ Settings</h3>
    <p>Free key chuno. Ek hi line me comma laga ke 3-4 keys daal sakte ho — limit aate hi agent khud agla key use karega.</p>

    <label for="prov">Provider</label>
    <select id="prov" onchange="provChange()">
      <option value="groq">Groq — free, fast, no card</option>
      <option value="gemini">Google Gemini — free, no card</option>
      <option value="openrouter">OpenRouter — free models</option>
      <option value="mistral">Mistral — free experiment</option>
      <option value="deepseek">DeepSeek — paid (5M free token)</option>
      <option value="ollama">Ollama — LOCAL, unlimited, no key</option>
    </select>

    <div id="keyBox">
      <label for="key">API Key(s)</label>
      <input id="key" type="text" placeholder="key1,key2,key3" autocomplete="off" spellcheck="false">
      <div class="note" id="knote"></div>
    </div>

    <div id="ollamaNote" class="note" style="display:none">
      Ollama mode me koi key nahi chahiye. Pehle install karo:
      <br><code>ollama pull qwen3:8b</code>
      <br>Phir yahan <b>Ollama</b> select karke Save dabao.
      <br><br>⚠️ Web UI agar kisi server/sandbox pe chal raha hai to <code>localhost</code> tumhara
      computer nahi hoga — tab Ollama kaam nahi karega. Apne laptop pe chalane par perfect hai.
    </div>

    <div class="row">
      <button class="btn" onclick="closeSettings()">Cancel</button>
      <button class="btn" onclick="clearKey()" style="flex:.7">Key hatao</button>
      <button class="btn primary" onclick="saveSettings()">Save</button>
    </div>
  </div>
</div>

<div class="prev" id="prev"></div>
<div class="toast" id="toast"></div>

<script>
const LINKS = {
  groq:"https://console.groq.com/keys",
  gemini:"https://aistudio.google.com/apikey",
  openrouter:"https://openrouter.ai/keys",
  mistral:"https://console.mistral.ai/api-keys",
  deepseek:"https://platform.deepseek.com/api_keys"
};
const NOTES = {
  groq:"groq.com → Google login → Create API Key. Free, no card. 30 req/min.",
  gemini:"aistudio.google.com/apikey → Create key. Free, no card, permanent.",
  openrouter:"openrouter.ai/keys → free ':free' models. 50 req/day.",
  mistral:"console.mistral.ai → free Experiment tier (phone verify).",
  deepseek:"Free nahi hai — 5M free token naye account pe, uske baad top-up."
};

let busy=false, statusObj=null;

function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function md(s){
  s=esc(s);
  s=s.replace(/```([\s\S]*?)```/g,(m,c)=>'<pre><code>'+c.replace(/^\n/,'')+'</code></pre>');
  s=s.replace(/`([^`]+)`/g,'<code>$1</code>');
  s=s.replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>');
  return s;
}
function toast(t){const el=document.getElementById('toast');el.textContent=t;el.classList.add('on');setTimeout(()=>el.classList.remove('on'),2000)}
function scroll(){const c=document.getElementById('chat');c.scrollTop=c.scrollHeight}

function addMsg(role,text){
  const w=document.getElementById('msgs');
  const d=document.createElement('div');
  d.className='msg '+(role==='user'?'user':'ai');
  d.innerHTML='<div class="av">'+(role==='user'?'TU':'AI')+'</div><div class="bubble">'+md(text)+'</div>';
  w.appendChild(d);scroll();return d.querySelector('.bubble');
}

async function refreshStatus(){
  try{
    const r=await fetch('/api/status');statusObj=await r.json();
    const p=document.getElementById('status');
    if(statusObj.ready){p.className='pill ok';p.textContent=(statusObj.provider||'local')+' · '+(statusObj.model||'')}
    else{p.className='pill bad';p.textContent='Setup needed';openSettings()}
  }catch(e){}
}

async function loadFiles(){
  try{
    const r=await fetch('/api/files');const fs=await r.json();
    const box=document.getElementById('files');
    if(!fs.length){box.innerHTML='<div class="empty">Abhi koi file nahi.<br>Agent se kuch banao.</div>';return}
    box.innerHTML=fs.map(f=>
      '<div class="file" onclick="viewFile(\''+f.path.replace(/'/g,"\\'")+'\')">'+
      '<span>📄</span><span class="nm">'+esc(f.path)+'</span><span class="sz">'+fmt(f.size)+'</span></div>'
    ).join('');
  }catch(e){}
}
function fmt(n){return n<1024?n+' B':(n/1024).toFixed(1)+' KB'}
async function viewFile(p){
  const r=await fetch('/api/file?path='+encodeURIComponent(p));const d=await r.json();
  const prev=document.getElementById('prev');
  prev.style.display='block';
  prev.innerHTML='<div style="color:#8aa0bd;margin-bottom:8px">📄 '+esc(d.path||p)+'</div>'+esc(d.content||d.error||'');
  prev.scrollIntoView({behavior:'smooth',block:'nearest'});
}

async function send(){
  if(busy)return;
  const ta=document.getElementById('input');
  const task=ta.value.trim();if(!task)return;
  if(!statusObj||!statusObj.ready){openSettings();return}
  ta.value='';ta.style.height='auto';
  addMsg('user',task);
  busy=true;document.getElementById('send').disabled=true;

  const ai=addMsg('ai','');
  ai.innerHTML='<span class="typing"><i></i><i></i><i></i></span>';
  const chips=document.createElement('div');
  ai.appendChild(chips);
  const textSpan=document.createElement('div');
  ai.appendChild(textSpan);
  let acc='';

  try{
    const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task})});
    if(!res.ok||!res.body)throw new Error('server error');
    const reader=res.body.getReader();const dec=new TextDecoder();let buf='';
    while(true){
      const {value,done}=await reader.read();if(done)break;
      buf+=dec.decode(value,{stream:true});
      let i;
      while((i=buf.indexOf('\n\n'))>=0){
        const chunk=buf.slice(0,i);buf=buf.slice(i+2);
        if(chunk.startsWith('data: ')){
          const raw=chunk.slice(6);
          if(raw==='[DONE]')continue;
          let ev;try{ev=JSON.parse(raw)}catch(e){continue}
          if(ev.kind==='tool'){
            const c=document.createElement('span');
            c.className='tool';
            c.textContent='🔧 '+ev.data.name+(ev.data.target?' · '+ev.data.target:'');
            chips.appendChild(c);scroll();
          }else if(ev.kind==='final'){
            acc=ev.data;textSpan.innerHTML=md(acc);
            chips.querySelectorAll('.tool').forEach(x=>x.classList.add('done'));
            scroll();
          }else if(ev.kind==='error'){
            textSpan.innerHTML='<span style="color:#ff7b7b">⚠️ '+esc(ev.data)+'</span>';
            scroll();
          }
        }
      }
    }
    if(!acc&&!textSpan.innerHTML)textSpan.textContent='(khali jawab)';
  }catch(e){
    textSpan.innerHTML='<span style="color:#ff7b7b">⚠️ '+esc(e.message)+'</span>';
  }
  busy=false;document.getElementById('send').disabled=false;
  loadFiles();refreshStatus();
}

async function resetChat(){
  await fetch('/api/reset',{method:'POST'});
  document.getElementById('msgs').innerHTML='';
  document.getElementById('prev').style.display='none';
  toast('Nayi chat shuru');
}

function openSettings(){
  document.getElementById('overlay').classList.add('on');
  if(statusObj&&statusObj.provider)document.getElementById('prov').value=statusObj.provider;
  provChange();
}
function closeSettings(){document.getElementById('overlay').classList.remove('on')}
function provChange(){
  const p=document.getElementById('prov').value;
  const isLocal=p==='ollama';
  document.getElementById('keyBox').style.display=isLocal?'none':'block';
  document.getElementById('ollamaNote').style.display=isLocal?'block':'none';
  const k=document.getElementById('knote');
  if(!isLocal){
    k.innerHTML=(NOTES[p]||'')+'<br><a href="'+(LINKS[p]||'#')+'" target="_blank">→ Key lo yahan se</a>';
  }
}
async function saveSettings(){
  const provider=document.getElementById('prov').value;
  const key=document.getElementById('key').value.trim();
  const r=await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider,key})});
  const d=await r.json();
  document.getElementById('key').value='';
  closeSettings();
  if(d.ready){toast('Saved ✓');refreshStatus()}else{toast('Key check karo');refreshStatus()}
}
async function clearKey(){
  const provider=document.getElementById('prov').value;
  await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider,key:''})});
  document.getElementById('key').value='';
  toast('Key hata di');refreshStatus();
}

const ta=document.getElementById('input');
ta.addEventListener('keydown',e=>{
  if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}
});
ta.addEventListener('input',()=>{ta.style.height='auto';ta.style.height=Math.min(ta.scrollHeight,150)+'px'});

refreshStatus();loadFiles();
addMsg('ai','Namaste bhai 👋 Main tumhara apna agent hoon — tumhare computer pe chalta hoon, tumhare workspace me files banata hoon, Python chalata hoon, aur internet se data laata hoon.\n\nShuru karne ke liye ⚙ Settings me apni free key daalo (ya Ollama select karo — usme koi key nahi chahiye).\n\nPhir aise bolo:\n• "ek calculator banao HTML me"\n• "dummy sales data banao aur chart nikaalo"\n• "mere liye portfolio website banao"');
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv(core.HERE / ".env")
    port = int(os.getenv("PORT", "5000"))
    print(f"\n  Mera Agent chal raha hai ->  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

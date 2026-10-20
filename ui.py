"""ui.py — SuperAgent ka poora frontend (inline, zero external deps).

Do pages: LOGIN_HTML, APP_HTML.
Sab CSS/JS inline hai (CDN nahi) — sandboxed iframe / offline box pe bhi chalta hai.
"""

# ═══════════════════════════════════════════════════════════════ LOGIN
LOGIN_HTML = r"""<!doctype html>
<html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Login — SuperAgent</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%A5%B7%3C/text%3E%3C/svg%3E">
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{
  --bg:#06070b; --panel:#0c0f16; --line:#1a2030; --text:#e9eef8; --muted:#7c8aa3;
  --a1:#7c5cff; --a2:#22d3ee; --ok:#34d399; --err:#f87171;
}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--text);display:grid;place-items:center;
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Inter,Roboto,Arial,sans-serif;
  overflow:hidden;padding:20px}
body::before{content:"";position:fixed;inset:-30%;background:
  radial-gradient(45% 40% at 22% 18%, #7c5cff2e, transparent 62%),
  radial-gradient(40% 36% at 82% 78%, #22d3ee26, transparent 60%),
  radial-gradient(35% 32% at 60% 20%, #f472b61f, transparent 65%);
  filter:blur(28px);pointer-events:none;animation:drift 18s ease-in-out infinite alternate}
@keyframes drift{to{transform:translate3d(2%,-2%,0) scale(1.06)}}
.card{position:relative;width:100%;max-width:396px;background:#0c0f16cc;
  border:1px solid #ffffff14;border-radius:22px;padding:34px 30px 28px;
  box-shadow:0 30px 80px -20px #000000cc,0 0 0 1px #ffffff08 inset;
  backdrop-filter:blur(22px);animation:up .45s cubic-bezier(.2,.9,.2,1)}
@keyframes up{from{opacity:0;transform:translateY(14px) scale(.985)}to{opacity:1;transform:none}}
.logo{width:54px;height:54px;border-radius:16px;display:grid;place-items:center;font-size:26px;
  background:linear-gradient(140deg,var(--a1),var(--a2));margin-bottom:18px;
  box-shadow:0 12px 30px -10px #7c5cff99}
h1{font-size:21px;margin:0 0 6px;letter-spacing:-.3px}
p.sub{margin:0 0 24px;color:var(--muted);font-size:13px;line-height:1.55}
label{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.09em;
  color:#8fa0bb;margin-bottom:8px;font-weight:650}
.field{position:relative}
input{width:100%;padding:13px 46px 13px 15px;border-radius:13px;border:1px solid var(--line);
  background:#080a11;color:var(--text);font-size:14.5px;outline:none;transition:.18s;
  font-family:inherit;letter-spacing:.02em}
input:focus{border-color:#7c5cff88;box-shadow:0 0 0 3px #7c5cff1f}
.eye{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:0;
  color:#63718a;cursor:pointer;padding:8px;border-radius:9px;display:grid;place-items:center}
.eye:hover{color:#a8b6cc;background:#ffffff0a}
button.go{width:100%;margin-top:18px;padding:13px;border-radius:13px;border:0;cursor:pointer;
  font-size:14.5px;font-weight:700;color:#0a0713;letter-spacing:.01em;
  background:linear-gradient(135deg,#a78bfa,#67e8f9);transition:.18s;
  box-shadow:0 14px 34px -14px #7c5cffb3}
button.go:hover{filter:brightness(1.08);transform:translateY(-1px)}
button.go:active{transform:none}
button.go:disabled{opacity:.55;cursor:not-allowed;transform:none}
.err{margin-top:14px;padding:11px 13px;border-radius:11px;background:#2a0f13;border:1px solid #f8717136;
  color:#fca5a5;font-size:12.5px;display:<!--ERR-DISP-->}
.err:empty{display:none}
.foot{margin-top:22px;padding-top:16px;border-top:1px solid var(--line);
  display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#5b6982}
.dot{display:inline-flex;align-items:center;gap:6px}
.dot i{width:6px;height:6px;border-radius:50%;background:var(--ok);box-shadow:0 0 8px var(--ok)}
</style></head><body>
<form class="card" method="post" action="/login" autocomplete="on">
  <div class="logo">🥷</div>
  <h1>SuperAgent</h1>
  <p class="sub">Apna private AI agent — code likhta hai, chalata hai, terminal sab khud.</p>
  <label for="pw">Password</label>
  <div class="field">
    <input id="pw" name="password" type="password" placeholder="••••••••••" autofocus required
           autocomplete="current-password" spellcheck="false">
    <button class="eye" type="button" onclick="tog()" aria-label="show">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.9" stroke-linecap="round"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="2.6"/></svg>
    </button>
  </div>
  <div class="err"><!--ERR--></div>
  <button class="go" type="submit">Andar aao →</button>
  <div class="foot"><span class="dot"><i></i> server live</span><span>private · self-hosted</span></div>
</form>
<script>
function tog(){var i=document.getElementById('pw');i.type=i.type==='password'?'text':'password'}
document.querySelector('form').addEventListener('submit',function(e){
  var b=this.querySelector('.go');b.disabled=true;b.textContent='Checking…';
});
</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════ APP
APP_HTML = r"""<!doctype html>
<html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>SuperAgent</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%A5%B7%3C/text%3E%3C/svg%3E">
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{
  --bg:#06070b;--panel:#0b0e15;--panel2:#090c12;--card:#0e121b;--line:#1a2130;
  --text:#e9eef8;--muted:#7c8aa3;--dim:#556077;
  --a1:#7c5cff;--a2:#22d3ee;--ok:#34d399;--warn:#fbbf24;--err:#f87171;
  --r:14px;
}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--text);overflow:hidden;font-size:14px;
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Inter,Roboto,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
::-webkit-scrollbar{width:9px;height:9px}
::-webkit-scrollbar-thumb{background:#243044;border-radius:9px;border:2px solid transparent;background-clip:content-box}
::-webkit-scrollbar-thumb:hover{background:#324258;background-clip:content-box}
::-webkit-scrollbar-track{background:transparent}

.app{display:grid;grid-template-columns:268px minmax(0,1fr) 0;height:100dvh;transition:grid-template .26s cubic-bezier(.4,0,.2,1)}
.app.files-open{grid-template-columns:268px minmax(0,1fr) 316px}
@media(max-width:920px){
  .app,.app.files-open{grid-template-columns:minmax(0,1fr)}
  .side{position:fixed;inset:0 auto 0 0;width:280px;z-index:70;transform:translateX(-100%);
    transition:transform .26s cubic-bezier(.4,0,.2,1);box-shadow:0 0 60px #000c}
  body.nav .side{transform:none}
  .files{position:fixed;inset:0 0 0 auto;width:min(92vw,340px);z-index:70;transform:translateX(100%);
    transition:transform .26s;box-shadow:0 0 60px #000c}
  .app.files-open .files{transform:none}
  .scrim{position:fixed;inset:0;background:#000000a8;backdrop-filter:blur(2px);z-index:60;opacity:0;
    pointer-events:none;transition:.2s}
  body.nav .scrim,.app.files-open~.scrim{opacity:1;pointer-events:auto}
  .burger{display:grid!important}
  .top h2{max-width:40vw}
  .wrap{max-width:100%!important}
}
.scrim{display:none}
@media(max-width:920px){.scrim{display:block}}

/* ───────── sidebar */
.side{background:linear-gradient(180deg,#0a0d14,#080a10);border-right:1px solid var(--line);
  display:flex;flex-direction:column;min-height:0}
.brand{display:flex;align-items:center;gap:10px;padding:16px 15px 12px}
.brand .ico{width:32px;height:32px;border-radius:10px;display:grid;place-items:center;font-size:16px;
  background:linear-gradient(140deg,var(--a1),var(--a2));box-shadow:0 8px 22px -8px #7c5cffaa}
.brand .nm{font-weight:750;font-size:14.5px;letter-spacing:-.2px;line-height:1.15}
.brand .tg{font-size:10px;color:var(--dim);font-weight:500;letter-spacing:.02em}
.newbtn{margin:2px 12px 12px;padding:11px;border-radius:12px;border:1px solid #7c5cff3d;cursor:pointer;
  background:linear-gradient(135deg,#7c5cff22,#22d3ee14);color:#cfc6ff;font-weight:680;font-size:13px;
  display:flex;align-items:center;justify-content:center;gap:8px;transition:.16s;font-family:inherit}
.newbtn:hover{background:linear-gradient(135deg,#7c5cff33,#22d3ee22);border-color:#7c5cff66;
  color:#fff;box-shadow:0 8px 24px -12px #7c5cffaa}
.search{margin:0 12px 10px;position:relative}
.search input{width:100%;padding:8px 10px 8px 30px;border-radius:10px;border:1px solid var(--line);
  background:#0a0e16;color:var(--text);font-size:12.5px;outline:none;font-family:inherit}
.search input:focus{border-color:#7c5cff66}
.search svg{position:absolute;left:9px;top:50%;transform:translateY(-50%);color:#4d5a70}
.sect{padding:12px 16px 6px;font-size:10px;text-transform:uppercase;letter-spacing:.11em;
  color:#4e5b72;font-weight:750}
.chats{flex:1;overflow-y:auto;padding:0 9px 10px;min-height:0}
.chatitem{display:flex;align-items:center;gap:9px;padding:9px 10px;border-radius:10px;cursor:pointer;
  font-size:13px;color:#b9c6d9;transition:.13s;margin-bottom:2px;position:relative}
.chatitem:hover{background:#121722}
.chatitem.on{background:linear-gradient(135deg,#7c5cff1f,#22d3ee10);color:#e8e3ff;
  box-shadow:inset 0 0 0 1px #7c5cff3d}
.chatitem .ic{color:#4f5d75;flex:0 0 auto;display:grid;place-items:center}
.chatitem.on .ic{color:#a78bfa}
.chatitem .t{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chatitem .del{opacity:0;color:#5c6a7d;padding:2px;border-radius:6px;display:grid;place-items:center;
  transition:.12s;flex:0 0 auto}
.chatitem:hover .del{opacity:1}
.chatitem .del:hover{color:var(--err);background:#f8717118}
.sidefoot{border-top:1px solid var(--line);padding:11px 12px 13px;display:flex;flex-direction:column;gap:8px}
.badge{font-size:11px;padding:7px 10px;border-radius:10px;background:#0b1410;border:1px solid #1d3b2e;
  color:#6ee7b7;display:flex;align-items:center;gap:7px;overflow:hidden}
.badge .d{width:6px;height:6px;border-radius:50%;background:var(--ok);box-shadow:0 0 8px var(--ok);flex:0 0 auto;
  animation:pulse 2.4s infinite}
@keyframes pulse{50%{opacity:.45}}
.badge span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.badge.bad{background:#170f10;border-color:#3a1c20;color:#fca5a5}
.badge.bad .d{background:var(--err);box-shadow:0 0 8px var(--err)}
.badge.warn{background:#171208;border-color:#3d3115;color:#fcd34d}
.badge.warn .d{background:var(--warn);box-shadow:0 0 8px var(--warn)}
.sidefoot a.lnk{font-size:11.5px;color:#5d6b83;text-align:center;text-decoration:none;padding:4px;
  border-radius:8px;transition:.14s}
.sidefoot a.lnk:hover{color:#c4b5fd;background:#7c5cff14}

/* ───────── main */
.main{display:flex;flex-direction:column;min-width:0;min-height:0;position:relative}
.top{display:flex;align-items:center;gap:9px;padding:11px 14px;border-bottom:1px solid var(--line);
  background:#0a0d14e6;backdrop-filter:blur(14px);z-index:20;flex:0 0 auto}
.burger{display:none;width:34px;height:34px;border-radius:10px;border:1px solid var(--line);
  background:#0e121b;color:#a9b7cc;place-items:center;cursor:pointer;flex:0 0 auto}
.top h2{font-size:14px;margin:0;font-weight:640;letter-spacing:-.15px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0}
.chip{font-size:11px;padding:5px 9px;border-radius:999px;border:1px solid var(--line);background:#0b0f17;
  color:#8b9ab3;display:inline-flex;align-items:center;gap:6px;white-space:nowrap;max-width:230px;overflow:hidden}
.chip b{color:#c4b5fd;font-weight:650;overflow:hidden;text-overflow:ellipsis}
.chip .d{width:5px;height:5px;border-radius:50%;background:var(--ok);box-shadow:0 0 6px var(--ok)}
@media(max-width:640px){.chip{display:none}}
.btn{background:#0e121b;color:#c3cfe0;border:1px solid var(--line);border-radius:10px;padding:7px 11px;
  font-size:12px;cursor:pointer;transition:.15s;display:inline-flex;align-items:center;gap:6px;
  font-family:inherit;text-decoration:none;line-height:1.2}
.btn:hover{background:#151b27;border-color:#2b3650;color:#fff}
.btn.acc{background:#12101f;border-color:#7c5cff44;color:#c4b5fd}
.btn.acc:hover{background:#171331;border-color:#7c5cff88}
.btn.ico{padding:7px;width:33px;justify-content:center}

/* ───────── chat area */
#chat{flex:1;overflow-y:auto;overflow-x:hidden;padding:22px 16px 10px;scroll-behavior:smooth;min-height:0}
.wrap{max-width:820px;margin:0 auto;padding-bottom:8px}
.hello{display:flex;flex-direction:column;align-items:center;text-align:center;padding:8vh 10px 30px;
  animation:up .4s ease}
@keyframes up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.hello .big{width:62px;height:62px;border-radius:20px;display:grid;place-items:center;font-size:30px;
  background:linear-gradient(140deg,var(--a1),var(--a2));box-shadow:0 20px 50px -18px #7c5cffcc;margin-bottom:18px}
.hello h3{margin:0 0 7px;font-size:20px;font-weight:730;letter-spacing:-.35px}
.hello p{margin:0 0 26px;color:var(--muted);font-size:13.5px;max-width:430px;line-height:1.6}
.sugg{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;width:100%;max-width:520px}
@media(max-width:560px){.sugg{grid-template-columns:1fr}}
.sugg button{text-align:left;padding:12px 13px;border-radius:13px;border:1px solid var(--line);
  background:#0c1017;color:#b9c6d9;font-size:12.6px;cursor:pointer;transition:.16s;font-family:inherit;
  display:flex;gap:9px;align-items:flex-start;line-height:1.45}
.sugg button:hover{background:#111725;border-color:#7c5cff4d;color:#fff;transform:translateY(-1px);
  box-shadow:0 10px 26px -16px #7c5cffaa}
.sugg .e{font-size:15px;flex:0 0 auto;line-height:1.2}

/* message */
.msg{display:flex;gap:11px;margin-bottom:20px;animation:in .22s ease}
@keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.av{width:30px;height:30px;border-radius:10px;flex:0 0 auto;display:grid;place-items:center;
  font-size:11px;font-weight:800;margin-top:1px}
.msg.user .av{background:#18243a;color:#9cc4ff;border:1px solid #24344e}
.msg.ai .av{background:linear-gradient(140deg,var(--a1),var(--a2));color:#0a0713;
  box-shadow:0 6px 18px -8px #7c5cffaa}
.mbody{flex:1;min-width:0}
.who{font-size:11px;color:#5f6d85;margin-bottom:5px;font-weight:650;letter-spacing:.01em}
.bubble{font-size:14px;line-height:1.68;overflow-wrap:anywhere;color:#dde5f2}
.msg.user .bubble{background:#101728;border:1px solid #1f2c42;border-radius:14px;padding:11px 14px;
  display:inline-block;max-width:100%;white-space:pre-wrap}
.bubble>:first-child{margin-top:0}
.bubble>:last-child{margin-bottom:0}
.bubble p{margin:0 0 11px}
.bubble h1,.bubble h2,.bubble h3,.bubble h4{margin:18px 0 9px;line-height:1.3;letter-spacing:-.2px}
.bubble h1{font-size:19px}.bubble h2{font-size:17px}.bubble h3{font-size:15.5px}.bubble h4{font-size:14px}
.bubble ul,.bubble ol{margin:0 0 11px;padding-left:22px}
.bubble li{margin:4px 0}
.bubble a{color:#8ab4ff;text-decoration:none;border-bottom:1px solid #8ab4ff40}
.bubble a:hover{border-color:#8ab4ff}
.bubble hr{border:0;border-top:1px solid var(--line);margin:16px 0}
.bubble blockquote{margin:0 0 11px;padding:2px 0 2px 13px;border-left:2px solid #7c5cff66;color:#a9b7cc}
.bubble code{background:#0a0f18;border:1px solid #1c2536;padding:1.5px 5px;border-radius:6px;
  font-size:12.6px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:#7dd3fc}
.bubble table{border-collapse:collapse;margin:0 0 12px;font-size:13px;width:100%;display:block;overflow-x:auto}
.bubble th,.bubble td{border:1px solid var(--line);padding:7px 10px;text-align:left}
.bubble th{background:#0d121b;font-weight:680;color:#c9d6e8}
/* code block */
.cb{margin:0 0 12px;border:1px solid #1b2434;border-radius:12px;overflow:hidden;background:#05080e}
.cb .h{display:flex;align-items:center;gap:8px;padding:7px 10px;background:#0a0f18;border-bottom:1px solid #16202e;
  font-size:11px;color:#66748c;font-family:ui-monospace,monospace}
.cb .h .lang{color:#8b9ab3;text-transform:lowercase}
.cb .h .cpy{margin-left:auto;background:none;border:0;color:#5f6d85;cursor:pointer;font-size:10.5px;
  padding:3px 7px;border-radius:6px;display:inline-flex;gap:4px;align-items:center;font-family:inherit}
.cb .h .cpy:hover{color:#c4b5fd;background:#7c5cff14}
.cb pre{margin:0;padding:12px 13px;overflow-x:auto;font-size:12.6px;line-height:1.62;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:#d3e0f0}
.cb pre code{background:none;border:0;padding:0;color:inherit;font-size:inherit}

/* tool steps */
.steps{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
.step{display:inline-flex;align-items:center;gap:6px;font-size:11.2px;padding:5px 9px;border-radius:999px;
  background:#0b1520;border:1px solid #1d3a52;color:#7fc2ff;font-family:ui-monospace,monospace;
  animation:in .2s ease;max-width:100%;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.step .sp{width:9px;height:9px;border:1.6px solid #2f5d80;border-top-color:#7fc2ff;border-radius:50%;
  animation:spin .7s linear infinite;flex:0 0 auto}
@keyframes spin{to{transform:rotate(360deg)}}
.step.done{background:#0c1a0e;border-color:#2a5230;color:#86efac}
.step.done .sp{border:0;width:auto;height:auto;animation:none}
.step.fail{background:#1a0d0f;border-color:#4a1f24;color:#fca5a5}
.think{display:inline-flex;align-items:center;gap:8px;color:#6f7e96;font-size:12.6px;padding:2px 0}
.think i{width:5px;height:5px;border-radius:50%;background:#7c8aa3;display:inline-block;
  animation:bob 1.15s infinite}
.think i:nth-child(2){animation-delay:.14s}.think i:nth-child(3){animation-delay:.28s}
@keyframes bob{0%,60%,100%{opacity:.25;transform:translateY(0)}30%{opacity:1;transform:translateY(-3px)}}
.cursor{display:inline-block;width:7px;height:15px;background:#a78bfa;vertical-align:-2px;
  margin-left:2px;border-radius:1.5px;animation:blink 1s steps(2) infinite}
@keyframes blink{50%{opacity:0}}
.errbox{margin:0 0 12px;padding:10px 12px;border-radius:11px;background:#1c0e12;border:1px solid #f8717136;
  color:#fca5a5;font-size:12.6px;line-height:1.55}

/* ───────── composer */
.composer{flex:0 0 auto;padding:9px 14px max(12px,env(safe-area-inset-bottom));
  background:linear-gradient(180deg,#06070b00,#06070bf2 32%)}
.cwrap{max-width:820px;margin:0 auto;display:flex;gap:8px;align-items:flex-end;background:#0c1119;
  border:1px solid #1d2637;border-radius:16px;padding:8px 8px 8px 14px;transition:.18s;
  box-shadow:0 10px 30px -18px #000}
.cwrap:focus-within{border-color:#7c5cff66;box-shadow:0 0 0 3px #7c5cff1a,0 10px 30px -18px #000}
.cwrap textarea{flex:1;background:none;border:none;color:var(--text);font-size:14px;resize:none;
  outline:none;max-height:168px;min-height:24px;line-height:1.55;font-family:inherit;padding:4px 0}
.cwrap textarea::placeholder{color:#4b5870}
.send{width:36px;height:36px;border-radius:11px;border:none;flex:0 0 auto;cursor:pointer;
  background:linear-gradient(140deg,var(--a1),var(--a2));color:#0a0713;display:grid;place-items:center;
  transition:.16s;box-shadow:0 8px 20px -10px #7c5cffcc}
.send:hover:not(:disabled){filter:brightness(1.1);transform:translateY(-1px)}
.send:disabled{opacity:.3;cursor:not-allowed;transform:none;box-shadow:none}
.send.stop{background:linear-gradient(140deg,#f87171,#fb923c);color:#1a0505}
.hint{max-width:820px;margin:7px auto 0;color:#414d63;font-size:10.5px;text-align:center;letter-spacing:.01em}

/* ───────── files */
.files{background:linear-gradient(180deg,#0a0d14,#080a10);border-left:1px solid var(--line);
  display:none;flex-direction:column;overflow:hidden;min-height:0}
.app.files-open .files{display:flex}
.fhead{display:flex;align-items:center;gap:8px;padding:13px 13px 9px;font-size:11px;
  color:var(--muted);text-transform:uppercase;letter-spacing:.09em;font-weight:750}
.fhead .cnt{background:#141a26;border:1px solid var(--line);border-radius:999px;padding:1px 7px;
  font-size:10px;color:#8b9ab3;letter-spacing:0}
#filelist{flex:1;overflow-y:auto;padding:0 9px 10px;min-height:0}
.fitem{display:flex;align-items:center;gap:9px;padding:9px 10px;border-radius:10px;cursor:pointer;
  font-size:12.6px;transition:.13s;color:#b9c6d9}
.fitem:hover{background:#121722;color:#fff}
.fitem .fi{flex:0 0 auto;width:22px;height:22px;border-radius:7px;display:grid;place-items:center;
  background:#0e1622;border:1px solid #1b2536;font-size:10px}
.fitem .nm{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fitem .sz{color:#4e5b72;font-size:10px;flex:0 0 auto}
.empty{color:#4e5b72;font-size:12px;padding:10px 14px;line-height:1.65}
.ffoot{padding:10px;border-top:1px solid var(--line);display:flex;gap:7px}
.ffoot .btn{flex:1;justify-content:center}

/* ───────── preview */
.overlay{position:fixed;inset:0;background:#04060af0;backdrop-filter:blur(8px);display:none;z-index:90;
  padding:16px;padding-top:max(16px,env(safe-area-inset-top))}
.overlay.on{display:flex;flex-direction:column;gap:11px;animation:in .18s ease}
.phead{display:flex;align-items:center;gap:10px;color:#c8d6e8;font-size:12.5px;flex:0 0 auto}
.phead .nm{font-family:ui-monospace,monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.phead .sp{flex:1}
#pbody{flex:1;display:flex;min-height:0;gap:10px}
#pbody iframe{flex:1;width:100%;border:1px solid var(--line);border-radius:14px;background:#fff}
#pbody .imgwrap{flex:1;display:grid;place-items:center;background:#05080d;border:1px solid var(--line);
  border-radius:14px;overflow:auto;padding:12px}
#pbody img{max-width:100%;max-height:100%;border-radius:10px}
pre.pcode{flex:1;overflow:auto;background:#05080e;border:1px solid var(--line);border-radius:14px;
  padding:15px;font-size:12.6px;color:#d3e0f0;white-space:pre;margin:0;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;line-height:1.6}
.toast{position:fixed;bottom:22px;left:50%;transform:translate(-50%,16px);background:#12172a;
  border:1px solid #7c5cff4d;color:#e8e3ff;padding:9px 16px;border-radius:11px;font-size:12.5px;
  opacity:0;pointer-events:none;transition:.22s;z-index:120;box-shadow:0 16px 40px -16px #000}
.toast.on{opacity:1;transform:translate(-50%,0)}
</style></head><body>
<div class="app" id="app">
  <aside class="side">
    <div class="brand">
      <div class="ico">🥷</div>
      <div><div class="nm">SuperAgent</div><div class="tg">private · self-hosted</div></div>
    </div>
    <button class="newbtn" onclick="newChat()">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"
        stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg> New chat
    </button>
    <div class="search">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
        stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.2-3.2"/></svg>
      <input id="q" placeholder="Search chats…" oninput="renderChats()" spellcheck="false">
    </div>
    <div class="sect">Recent</div>
    <div class="chats" id="chats"></div>
    <div class="sidefoot">
      <div class="badge" id="pbadge"><span class="d"></span><span>checking…</span></div>
      <a class="lnk" href="/logout">Logout →</a>
    </div>
  </aside>

  <div class="main">
    <div class="top">
      <button class="burger" onclick="document.body.classList.toggle('nav')" aria-label="menu">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
          stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
      </button>
      <h2 id="ctitle">New chat</h2>
      <div class="chip" id="mchip"><span class="d"></span><b id="mname">…</b></div>
      <button class="btn ico" onclick="toggleFiles()" title="Files">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"
          stroke-linecap="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
      </button>
      <a class="btn ico" id="dl" href="#" download title="Download ZIP">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"
          stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12m0 0 4-4m-4 4-4-4M4 19h16"/></svg>
      </a>
      <button class="btn ico" onclick="setKey()" title="API key">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"
          stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M19 5l-2 2M7 17l-2 2"/></svg>
      </button>
    </div>

    <div id="chat"><div class="wrap" id="msgs"></div></div>

    <div class="composer">
      <div class="cwrap">
        <textarea id="input" rows="1" placeholder="Kya banau? — 'ek portfolio site banao 3 pages'"
          oninput="grow()" onkeydown="keydown(event)"></textarea>
        <button class="send" id="send" onclick="send()" title="Send">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"
            stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/></svg>
        </button>
      </div>
      <div class="hint">Enter bhejo · Shift+Enter nayi line · agent khud files banata, code chalata, terminal use karta hai</div>
    </div>
  </div>

  <aside class="files">
    <div class="fhead"><span>Workspace</span><div style="flex:1"></div><span class="cnt" id="fcount">0</span></div>
    <div id="filelist"></div>
    <div class="ffoot">
      <button class="btn acc" onclick="loadFiles()">↻ Refresh</button>
      <button class="btn" onclick="toggleFiles()">✕</button>
    </div>
  </aside>
</div>
<div class="scrim" onclick="document.body.classList.remove('nav');document.getElementById('app').classList.remove('files-open')"></div>

<div class="overlay" id="ov">
  <div class="phead"><span class="nm" id="pname">preview</span><span id="psize" style="color:#4e5b72"></span>
    <div class="sp"></div><button class="btn" onclick="closePrev()">✕ Close</button></div>
  <div id="pbody"></div>
</div>
<div class="toast" id="toast"></div>

<script>
/* ═══════════════════════════════════════════ state */
let chats=[], current=null, busy=false, providers=[], keylessMode=false;
let abortCtrl=null, filt='';
const $=id=>document.getElementById(id);
const esc=s=>(s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  .replace(/"/g,'&quot;');

/* auth token (sandbox iframe me cookie block hoti hai) */
let _T=new URLSearchParams(location.search).get('t')||'';
try{ if(_T) sessionStorage.setItem('sat',_T); else _T=sessionStorage.getItem('sat')||''; }catch(e){}
if(new URLSearchParams(location.search).get('t')){ try{history.replaceState(null,'','/')}catch(e){} }
const _f=window.fetch.bind(window);
window.fetch=(u,o={})=>{
  if(typeof u==='string'&&u.startsWith('/api/')){
    u+=(u.includes('?')?'&':'?')+'t='+encodeURIComponent(_T);
    o={...o,headers:{...(o.headers||{}),'X-Auth-Token':_T}};
  }
  return _f(u,o);
};
const withT=u=>u+(u.includes('?')?'&':'?')+'t='+encodeURIComponent(_T);

function toast(msg){const t=$('toast');t.textContent=msg;t.classList.add('on');
  clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('on'),2200)}

/* ═══════════════════════════════════════════ markdown */
function md(src){
  let s=esc(src);
  const blocks=[];
  s=s.replace(/```([^\n`]*)\n?([\s\S]*?)```/g,(m,lang,code)=>{
    const i=blocks.length;
    blocks.push({lang:(lang||'').trim(),code:code.replace(/\n$/,'')});
    return '\u0000CB'+i+'\u0000';
  });
  s=s.replace(/^### (.*)$/gm,'<h4>$1</h4>')
     .replace(/^## (.*)$/gm,'<h3>$1</h3>')
     .replace(/^# (.*)$/gm,'<h2>$1</h2>')
     .replace(/^\s*---+\s*$/gm,'<hr>')
     .replace(/^&gt; (.*)$/gm,'<blockquote>$1</blockquote>');
  s=s.replace(/\*\*([^*\n]+)\*\*/g,'<b>$1</b>')
     .replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s).,!?]|$)/g,'$1<i>$2</i>')
     .replace(/`([^`\n]+)`/g,'<code>$1</code>')
     .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');
  // lists
  s=s.replace(/(?:^|\n)((?:(?:^|\n)\s*[-*+] .*)+)/g,(m,blk)=>{
    const items=blk.trim().split('\n').map(l=>'<li>'+l.replace(/^\s*[-*+]\s+/,'')+'</li>').join('');
    return '\n<ul>'+items+'</ul>';
  });
  s=s.replace(/(?:^|\n)((?:(?:^|\n)\s*\d+\. .*)+)/g,(m,blk)=>{
    const items=blk.trim().split('\n').map(l=>'<li>'+l.replace(/^\s*\d+\.\s+/,'')+'</li>').join('');
    return '\n<ol>'+items+'</ol>';
  });
  // paragraphs
  s=s.split(/\n{2,}/).map(p=>{
    p=p.trim();
    if(!p) return '';
    if(/^<(h[1-6]|ul|ol|hr|blockquote|pre|table|\u0000CB)/.test(p)) return p;
    return '<p>'+p.replace(/\n/g,'<br>')+'</p>';
  }).join('');
  // code blocks wapas
  s=s.replace(/\u0000CB(\d+)\u0000/g,(m,i)=>{
    const b=blocks[+i];
    const label=b.lang||'code';
    return '<div class="cb"><div class="h"><span class="lang">'+esc(label)+
      '</span><button class="cpy" onclick="cpy(this)">'+
      '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'+
      '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>copy</button></div>'+
      '<pre><code>'+esc(b.code)+'</code></pre></div>';
  });
  return s;
}
function cpy(btn){
  const pre=btn.closest('.cb').querySelector('pre');
  const txt=pre.textContent;
  const done=()=>{btn.textContent='copied ✓';setTimeout(()=>{
    btn.innerHTML='<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>copy';
  },1400)};
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done).catch(fb)}
  else fb();
  function fb(){const ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);
    ta.select();try{document.execCommand('copy');done()}catch(e){}ta.remove()}
}

/* ═══════════════════════════════════════════ status */
async function status(){
  try{
    const d=await (await fetch('/api/status')).json();
    providers=d.providers||[]; keylessMode=!!d.keyless;
    const b=$('pbadge'), name=$('mname');
    if(d.ready){
      const first=(d.providers[0]||''), prov=first.split(':')[0], model=(d.model||'').split(':').slice(-2).join(':');
      b.className='badge'; b.innerHTML='<span class="d"></span><span>'+
        (d.keyless?'free · ':'')+esc(prov)+(d.model?' · '+esc(d.model.slice(0,22)):'')+'</span>';
      if(name) name.textContent=(d.model||prov);
    }else{
      b.className='badge bad'; b.innerHTML='<span class="d"></span><span>no provider</span>';
      if(name) name.textContent='offline';
    }
  }catch(e){}
}

/* ═══════════════════════════════════════════ chats */
async function loadChats(){
  try{ chats=await (await fetch('/api/chats')).json(); }catch(e){ chats=chats||[]; }
  renderChats();
}
function renderChats(){
  const q=($('q').value||'').toLowerCase();
  const list=chats.filter(c=>!q||(c.title||'').toLowerCase().includes(q));
  $('chats').innerHTML=list.length?list.map(c=>
    '<div class="chatitem'+(c.id===current?' on':'')+'" onclick="openChat(\''+c.id+'\')">'+
      '<span class="ic"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"><path d="M21 12a8 8 0 0 1-8 8H7l-4 3V12a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8z"/></svg></span>'+
      '<span class="t">'+esc(c.title)+'</span>'+
      '<span class="del" onclick="event.stopPropagation();delChat(\''+c.id+'\')" title="delete">'+
        '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>'+
      '</span></div>').join('')
    : '<div class="empty">'+(q?'Kuch nahi mila.':'Abhi koi chat nahi.<br>New chat dabao.')+'</div>';
}

async function newChat(){
  const c=await (await fetch('/api/chats',{method:'POST'})).json();
  current=c.id; $('ctitle').textContent=c.title;
  $('dl').href=withT('/api/download?chat_id='+c.id);
  $('msgs').innerHTML=''; hello();
  await loadChats(); loadFiles();
  document.body.classList.remove('nav');
  $('input').focus();
}
async function openChat(id){
  current=id; const c=chats.find(x=>x.id===id);
  $('ctitle').textContent=c?c.title:'Chat';
  $('dl').href=withT('/api/download?chat_id='+id);
  await loadChats();
  let msgs=[]; try{ msgs=await (await fetch('/api/chats/'+id+'/messages')).json(); }catch(e){}
  const box=$('msgs'); box.innerHTML='';
  if(!msgs.length){ hello(); }
  msgs.forEach(m=>{
    if(m.role==='user'){ addMsg('user',m.content); return; }
    const ai=addMsg('ai','');
    const steps=m.meta&&m.meta.filter(e=>e.kind==='tool');
    if(steps&&steps.length){
      const wrap=document.createElement('div'); wrap.className='steps';
      steps.forEach(e=>{
        const s=document.createElement('span'); s.className='step done';
        s.textContent='✓ '+e.data.name+(e.data.target?' · '+e.data.target:'');
        wrap.appendChild(s);
      });
      ai.before(wrap);
    }
    ai.innerHTML=md(m.content||'');
  });
  loadFiles(); scroll();
  document.body.classList.remove('nav');
}
async function delChat(id){
  if(!confirm('Ye chat delete karna hai?'))return;
  await fetch('/api/chats/'+id,{method:'DELETE'});
  if(current===id){current=null;$('msgs').innerHTML='';hello();$('ctitle').textContent='New chat'}
  loadChats();
}

/* ═══════════════════════════════════════════ messages */
function hello(){
  $('msgs').innerHTML=
  '<div class="hello"><div class="big">🥷</div><h3>Kya banau aaj?</h3>'+
  '<p>Code likhta hoon, chalata hoon, files banata hoon — sab khud. Bas bolo.</p>'+
  '<div class="sugg">'+
    sug('🌐','Ek portfolio website banao — dark theme, 3 sections','Ek portfolio website banao: hero, projects, contact. Modern dark theme, smooth scroll. Sab files banao aur browser me preview ke liye ready rakho.')+
    sug('🐍','Python script jo CSV padhe aur chart bane','Ek Python script banao jo sales.csv padhe aur matplotlib se bar chart banaye. Sample CSV bhi banao aur script chalao.')+
    sug('⚡','Fibonacci + tests likho aur chalao','fibonacci.py banao jisme memoized fibonacci function ho, phir uske liye pytest tests likho aur chalao.')+
    sug('🖥️','Terminal me CPU info aur system check','Terminal me ye chalao: uname -a, python3 --version, node --version, nproc, free -h. Output table me dikhao.')+
  '</div></div>';
}
function sug(e,label,prompt){
  return '<button onclick="usePrompt('+JSON.stringify(prompt).replace(/"/g,'&quot;')+')">'+
    '<span class="e">'+e+'</span><span>'+esc(label)+'</span></button>';
}
function usePrompt(p){ $('input').value=p; grow(); $('input').focus(); }

function addMsg(role,text){
  const d=document.createElement('div');
  d.className='msg '+(role==='user'?'user':'ai');
  d.innerHTML='<div class="av">'+(role==='user'?'TU':'🥷')+'</div>'+
    '<div class="mbody"><div class="who">'+(role==='user'?'Tum':'SuperAgent')+'</div>'+
    '<div class="bubble">'+md(text)+'</div></div>';
  $('msgs').appendChild(d); scroll();
  return d.querySelector('.bubble');
}
function scroll(force){
  const c=$('chat');
  const near=c.scrollHeight-c.scrollTop-c.clientHeight<170;
  if(force||near) c.scrollTop=c.scrollHeight;
}

/* ═══════════════════════════════════════════ composer */
function grow(){const t=$('input');t.style.height='auto';t.style.height=Math.min(t.scrollHeight,168)+'px'}
function keydown(e){
  if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}
}

async function send(){
  if(busy){ return; }
  const ta=$('input'); const task=ta.value.trim();
  if(!task) return;
  if(!current) await newChat();
  if(!providers.length){ toast('Koi provider nahi — server check karo'); return }

  ta.value=''; ta.style.height='auto';
  const h=$('msgs').querySelector('.hello'); if(h) h.remove();
  addMsg('user',task);

  busy=true;
  const sbtn=$('send');
  sbtn.disabled=false; sbtn.classList.add('stop');
  sbtn.innerHTML='<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2.4"/></svg>';
  sbtn.title='Stop';
  sbtn.onclick=stop;

  const ai=addMsg('ai','');
  const body=ai.closest('.mbody');
  const stepsEl=document.createElement('div'); stepsEl.className='steps';
  const txtEl=document.createElement('div');
  const thinkEl=document.createElement('div');
  thinkEl.className='think';
  thinkEl.innerHTML='<i></i><i></i><i></i><span>soch raha hoon…</span>';
  body.insertBefore(stepsEl,ai); body.insertBefore(thinkEl,ai); body.insertBefore(txtEl,ai);

  let acc='', raf=null, steps={};
  function paint(){
    raf=null;
    txtEl.innerHTML=md(acc)+(busy?'<span class="cursor"></span>':'');
    scroll();
  }
  abortCtrl=new AbortController();

  try{
    const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({chat_id:current,task}), signal:abortCtrl.signal});
    if(!res.ok){ const e=await res.json().catch(()=>({})); throw new Error(e.error||('HTTP '+res.status)); }

    const rd=res.body.getReader(), dec=new TextDecoder(); let buf='';
    while(true){
      const {value,done}=await rd.read(); if(done) break;
      buf+=dec.decode(value,{stream:true});
      let i;
      while((i=buf.indexOf('\n\n'))>=0){
        const chunk=buf.slice(0,i); buf=buf.slice(i+2);
        if(!chunk.startsWith('data: ')) continue;
        let ev; try{ ev=JSON.parse(chunk.slice(6)) }catch(e){ continue }
        const k=ev.kind, d=ev.data;

        if(k==='tool'){
          if(thinkEl) thinkEl.remove();
          const key=(d.step||'')+'_'+d.name;
          let el=steps[key];
          if(!el){
            el=document.createElement('span'); el.className='step';
            el.innerHTML='<span class="sp"></span><span class="tx"></span>';
            el.querySelector('.tx').textContent=d.name+(d.target?' · '+d.target:'');
            stepsEl.appendChild(el); steps[key]=el;
          }
          // pichle step ko done karo
          Object.entries(steps).forEach(([kk,ee])=>{ if(kk!==key&&!ee.classList.contains('done')&&!ee.classList.contains('fail')){
            ee.classList.add('done'); ee.querySelector('.sp').outerHTML=''; 
          }});
          scroll();
        }
        else if(k==='delta'){
          acc+=d||'';
          if(!raf) raf=requestAnimationFrame(paint);
        }
        else if(k==='tool_done'){
          Object.values(steps).forEach(ee=>{ if(!ee.classList.contains('done')&&!ee.classList.contains('fail')){
            ee.classList.add('done'); const sp=ee.querySelector('.sp'); if(sp) sp.outerHTML='';
          }});
        }
        else if(k==='error'){
          if(thinkEl) thinkEl.remove();
          const e=document.createElement('div'); e.className='errbox';
          e.textContent='⚠ '+d; txtEl.appendChild(e); scroll();
        }
        else if(k==='wait'){
          if(thinkEl) thinkEl.querySelector('span').textContent=d;
        }
        else if(k==='done'){ break; }
      }
    }
  }catch(err){
    if(err.name!=='AbortError'){
      const e=document.createElement('div'); e.className='errbox';
      e.textContent='⚠ '+(err.message||'kuch galat hua');
      txtEl.appendChild(e);
    }else{
      acc+='\n\n_(rok diya)_'; txtEl.innerHTML=md(acc);
    }
  }finally{
    busy=false; abortCtrl=null;
    if(thinkEl&&thinkEl.parentNode) thinkEl.remove();
    Object.values(steps).forEach(ee=>{if(!ee.classList.contains('fail')){ee.classList.add('done');const sp=ee.querySelector('.sp');if(sp)sp.outerHTML=''}});
    paint();
    txtEl.innerHTML=md(acc);
    sbtn.classList.remove('stop'); sbtn.disabled=false; sbtn.title='Send';
    sbtn.onclick=send;
    sbtn.innerHTML='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/></svg>';
    loadFiles(); loadChats(); scroll();
  }
}
function stop(){
  if(abortCtrl){ try{abortCtrl.abort()}catch(e){} }
  busy=false;
  const sbtn=$('send'); sbtn.classList.remove('stop');
  sbtn.onclick=send;
  sbtn.innerHTML='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/></svg>';
}

/* ═══════════════════════════════════════════ settings */
async function setKey(){
  const p=prompt('Provider? (groq / gemini / openrouter / mistral)','groq');
  if(!p) return;
  const k=prompt('API key paste karo (sirf is server pe save hoti hai):');
  if(!k) return;
  try{
    const d=await (await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({provider:p.trim(),key:k.trim()})})).json();
    toast(d.ready?'✅ Key set ho gayi':'❌ Key save nahi hui');
    await status();
  }catch(e){ toast('❌ save fail') }
}

/* ═══════════════════════════════════════════ files */
function toggleFiles(){
  const on=$('app').classList.toggle('files-open');
  if(on) loadFiles();
}
async function loadFiles(){
  if(!current) return;
  let fs=[]; try{ fs=await (await fetch('/api/files?chat_id='+current)).json(); }catch(e){}
  $('fcount').textContent=fs.length;
  $('filelist').innerHTML=fs.length?fs.map(f=>{
    const ext=(f.path.split('.').pop()||'').toLowerCase();
    const icon=/^(html?|htm)$/.test(ext)?'🌐':/^(js|mjs|ts)$/.test(ext)?'📜':/^(py)$/.test(ext)?'🐍':
      /^(png|jpe?g|webp|gif|svg|ico)$/.test(ext)?'🖼️':/^(pdf)$/.test(ext)?'📕':
      /^(json|ya?ml|toml)$/.test(ext)?'⚙️':/^(css|scss)$/.test(ext)?'🎨':
      /^(md|txt)$/.test(ext)?'📝':/^(zip|tar|gz)$/.test(ext)?'📦':'📄';
    return '<div class="fitem" onclick="preview(\''+f.path.replace(/'/g,"\\'")+'\')">'+
      '<span class="fi">'+icon+'</span><span class="nm">'+esc(f.path)+'</span>'+
      '<span class="sz">'+fmt(f.size)+'</span></div>';
  }).join(''):'<div class="empty">Abhi koi file nahi.<br>Agent se kuch banwao — yahan dikhega.</div>';
}
const fmt=n=>n<1024?n+' B':n<1048576?(n/1024).toFixed(1)+' KB':(n/1048576).toFixed(1)+' MB';

async function preview(p){
  if(!current) return;
  $('ov').classList.add('on');
  $('pname').textContent=p; $('psize').textContent='';
  const url=withT('/api/raw?chat_id='+current+'&path='+encodeURIComponent(p));
  const ext=(p.split('.').pop()||'').toLowerCase();
  if(/^(html?|htm)$/.test(ext)){
    $('pbody').innerHTML='<iframe sandbox="allow-scripts allow-forms allow-modals allow-popups" src="'+url+'"></iframe>';
  }else if(/^(png|jpe?g|webp|gif|svg|ico|bmp)$/.test(ext)){
    $('pbody').innerHTML='<div class="imgwrap"><img src="'+url+'" alt=""></div>';
  }else if(ext==='pdf'){
    $('pbody').innerHTML='<iframe src="'+url+'"></iframe>';
  }else{
    try{
      const r=await fetch(url); const t=await r.text();
      $('psize').textContent=t.length.toLocaleString()+' chars';
      $('pbody').innerHTML='<pre class="pcode">'+esc(t.slice(0,200000))+'</pre>';
    }catch(e){ $('pbody').innerHTML='<pre class="pcode">load fail</pre>' }
  }
}
function closePrev(){ $('ov').classList.remove('on'); $('pbody').innerHTML='' }

/* ═══════════════════════════════════════════ boot */
(async function boot(){
  await status();
  await loadChats();
  if(chats.length){ await openChat(chats[0].id); } else { hello(); }
  setInterval(status, 20000);
  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'){ closePrev(); document.body.classList.remove('nav') }
    if((e.metaKey||e.ctrlKey)&&e.key==='k'){ e.preventDefault(); $('input').focus() }
  });
})();
</script>
</body></html>"""

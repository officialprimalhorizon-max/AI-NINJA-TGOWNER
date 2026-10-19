#!/usr/bin/env python3
"""
HOST — apni website / app free me online karo.

  python host.py                      # local server (workspace) -> http://localhost:8080
  python host.py --port 3000          # doosra port
  python host.py --tunnel             # internet pe FREE public URL (cloudflared)
  python host.py --guide              # free hosting options ki list

--tunnel ke liye Cloudflare Tunnel (free, no account):
  Windows: winget install Cloudflare.cloudflared
  Mac    : brew install cloudflared
  Linux  : https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
"""

import http.server
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import threading
import time

HERE = pathlib.Path(__file__).parent.resolve()
WORKSPACE = HERE / "workspace"

GUIDE = """
╔══════════════════════════════════════════════════════════════╗
║              FREE HOSTING — kya kahan dalna hai              ║
╚══════════════════════════════════════════════════════════════╝

1) STATIC SITE (HTML/CSS/JS — portfolio, landing page)
   ✅ GitHub Pages      — hamesha free, custom domain free      github.com → Settings → Pages
   ✅ Cloudflare Pages  — unlimited bandwidth, hamesha free      pages.cloudflare.com
   ✅ Netlify Drop      — folder drag-drop, 10 second me live    app.netlify.com/drop
   ✅ Vercel            — free tier, bahut easy                   vercel.com

2) APNA SERVER (Python/Node/Java app — jab tak PC on hai)
   ✅ LOCAL + CLOUDFLARE TUNNEL — bilkul free, no card
        python host.py --tunnel
      → https://random-name.trycloudflare.com  (public URL)
   ✅ ngrok free — 1 static domain free tier

3) 24/7 SERVER (PC band hone pe bhi chale)
   ✅ Oracle Cloud "Always Free" VM — asli free VPS (1-4 CPU, 24GB RAM)
        cloud.oracle.com → Free Tier → Always Free
   ⚠️ Render free  — sota hai (15 min idle pe)
   ⚠️ Railway/Fly  — trial credits, phir paid
   ⚠️ HuggingFace Spaces — free CPU, ML demos ke liye accha

4) AI AGENT 24/7
   Local PC + Oracle free VM + Cloudflare Tunnel = ₹0 hosting.
   (8GB laptop pe bada model mat chalao — VM pe 24GB RAM milti hai)

══════════════════════════════════════════════════════════════
"""


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:  # noqa: BLE001
        return "127.0.0.1"


def main():
    args = sys.argv[1:]
    if "--guide" in args:
        print(GUIDE)
        return

    port = 8080
    if "--port" in args:
        try:
            port = int(args[args.index("--port") + 1])
        except (IndexError, ValueError):
            pass

    directory = WORKSPACE
    if "--dir" in args:
        try:
            directory = (HERE / args[args.index("--dir") + 1]).resolve()
        except IndexError:
            pass
    if not directory.exists():
        print(f"[!] Folder nahi mila: {directory}")
        sys.exit(1)

    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler

    try:
        httpd = http.server.ThreadingHTTPServer(("0.0.0.0", port), handler)
    except OSError as e:
        print(f"[!] Port {port} busy hai: {e}\n    --port 8081 try karo.")
        sys.exit(1)

    print(f"\n  📂 Serving: {directory}")
    print(f"  🏠 Local  : http://localhost:{port}")
    print(f"  📱 Network: http://{lan_ip()}:{port}   (same wifi se phone pe kholo)")

    tunnel = None
    if "--tunnel" in args:
        cf = shutil.which("cloudflared")
        if not cf:
            print("\n  [!] cloudflared installed nahi hai. Install karo:")
            print("      Windows: winget install Cloudflare.cloudflared")
            print("      Mac    : brew install cloudflared")
            print("      Linux  : https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
        else:
            print("\n  🌍 Tunnel ban raha hai (10-20 sec)…")
            tunnel = subprocess.Popen(
                [cf, "tunnel", "--url", f"http://localhost:{port}", "--no-autoupdate"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )

            def watch():
                url = None
                for line in tunnel.stdout:
                    m = re.search(r"(https://[a-z0-9-]+\.trycloudflare\.com)", line)
                    if m and not url:
                        url = m.group(1)
                        print("\n" + "=" * 58)
                        print(f"  ✅ PUBLIC URL (free):  {url}")
                        print("  Ye link kisi ko bhi bhej sakte ho — internet pe khula hai.")
                        print("  Band karne ke liye Ctrl+C.")
                        print("=" * 58 + "\n")

            threading.Thread(target=watch, daemon=True).start()

    print("\n  Ctrl+C se band karo\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server band.")
    finally:
        if tunnel:
            tunnel.terminate()


if __name__ == "__main__":
    main()

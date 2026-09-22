"""The phone page (C22): a small HTTP server on the access point or the joined network.

    GET  /                  status page (HTML, refreshes itself)
    GET  /api/status        unit, policy, wireless state, bays
    GET  /api/certificates  list;  GET /certificates/<name>  one file;  GET /certificates.zip  all
    GET  /api/log           last log lines
    POST /api/wifi          {ssid, psk, key}   join a network and remember it
    POST /api/reset         {kind: wifi|factory, key}

Actions need the unit key shown on the OLED (it is also the access-point passphrase).
Standard library only, so it runs on the Pi without extra packages.
"""

from __future__ import annotations

import io
import json
import logging
import threading
import time
import zipfile
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote

from . import __version__

log = logging.getLogger(__name__)


class RingLog(logging.Handler):
    def __init__(self, n: int = 300):
        super().__init__()
        self.lines: deque[str] = deque(maxlen=n)
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%H:%M:%S"))

    def emit(self, record):
        self.lines.append(self.format(record))


PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>brain-drain</title><style>
body{font:15px system-ui,sans-serif;background:#14161a;color:#e6e8ec;margin:0;padding:12px}
h1{font-size:20px;margin:0 0 8px}h2{font-size:15px;margin:18px 0 6px;color:#9aa4b2}
table{border-collapse:collapse;width:100%}td,th{padding:6px 4px;border-bottom:1px solid #2a2e36;text-align:left;font-size:14px}
.bar{height:6px;background:#2a2e36;border-radius:3px}.bar i{display:block;height:6px;background:#ffc828;border-radius:3px}
input,button,select{font:inherit;padding:8px;border-radius:6px;border:1px solid #3a3f4a;background:#1d2026;color:#e6e8ec}
button{background:#2b4c7e;border-color:#2b4c7e}button.danger{background:#7e2b2b;border-color:#7e2b2b}
form{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0}small{color:#9aa4b2}pre{font-size:11px;white-space:pre-wrap;color:#b8c0cc}
.RUNNING{color:#ffc828}.DONE{color:#5fd38d}.ERROR,.FAIL{color:#ff6b6b}.IDLE{color:#6c7686}
</style></head><body>
<h1>brain-drain <small id="unit"></small></h1>
<div id="wifi"></div>
<h2>Bays</h2><table id="bays"></table>
<h2>Certificates <small id="ncert"></small> <a href="/certificates.zip">download all</a></h2><div id="certs"></div>
<h2>Join a network</h2><small>The unit remembers it and joins at every boot; the page is then at the address your router gives it. The key is the one on the OLED.</small>
<form onsubmit="return post('/api/wifi',this)"><input name="ssid" placeholder="network name" required><input name="psk" placeholder="network password" type="password"><input name="key" placeholder="unit key" required><button>Join</button></form>
<h2>Reset</h2><form onsubmit="return post('/api/reset',this)"><select name="kind"><option value="wifi">Wi-Fi reset: forget the network, back to the access point</option><option value="factory">Factory reset: also delete all certificates</option></select><input name="key" placeholder="unit key" required><button class="danger">Reset</button></form>
<h2>Log</h2><pre id="log"></pre>
<script>
const fmt=b=>b==null?'':b>=1e12?(b/1e12).toFixed(1)+' TB':b>=1e9?(b/1e9).toFixed(0)+' GB':(b/1e6).toFixed(0)+' MB';
const eta=s=>s==null?'':s>=3600?Math.floor(s/3600)+'h'+String(Math.floor(s%3600/60)).padStart(2,'0'):Math.floor(s/60)+'m'+String(Math.floor(s%60)).padStart(2,'0');
async function tick(){try{const s=await (await fetch('/api/status')).json();
document.getElementById('unit').textContent=s.unit+' · '+s.policy+' (DIP '+s.dip+') · v'+s.version;
const w=s.wifi;document.getElementById('wifi').innerHTML=w.mode==='ap'?'Access point <b>'+w.ssid+'</b> at '+w.url:w.mode==='station'?'On network <b>'+w.ssid+'</b> at '+w.url:'Wireless: '+w.mode+(w.error?' — '+w.error:'');
document.getElementById('bays').innerHTML='<tr><th>Bay</th><th>State</th><th>Drive</th><th>Progress</th></tr>'+s.bays.map(b=>'<tr><td>'+b.bay+'</td><td class="'+b.state+'">'+b.state+(b.tier?' '+b.tier:'')+'</td><td>'+(b.drive?b.drive.model+'<br><small>'+b.drive.serial+' · '+fmt(b.drive.size_bytes)+'</small>':'<small>'+(b.message||'empty')+'</small>')+'</td><td>'+(b.state==='RUNNING'?b.phase+' '+(b.percent==null?'?':b.percent+'%')+' '+eta(b.eta_s)+'<div class="bar"><i style="width:'+(b.percent||0)+'%"></i></div>':(b.message||''))+'</td></tr>').join('');
const c=await (await fetch('/api/certificates')).json();document.getElementById('ncert').textContent='('+c.length+')';
document.getElementById('certs').innerHTML=c.slice(-8).reverse().map(f=>'<div><a href="/certificates/'+encodeURIComponent(f.name)+'">'+f.name+'</a></div>').join('');
document.getElementById('log').textContent=(await (await fetch('/api/log')).json()).slice(-30).join('\\n');}catch(e){}}
async function post(u,f){const d=Object.fromEntries(new FormData(f));const r=await fetch(u,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(d)});alert(await r.text());return false}
tick();setInterval(tick,2000);
</script></body></html>"""


class WebUI:
    def __init__(self, cfg, engine, wifi, host: str = "0.0.0.0", port: int | None = None):
        self.cfg, self.engine, self.wifi = cfg, engine, wifi
        self.ring = RingLog()
        logging.getLogger().addHandler(self.ring)
        ui = self
        port = cfg.web_port if port is None else port

        class Handler(BaseHTTPRequestHandler):
            server_version = "brain-drain/" + __version__

            def log_message(self, fmt, *args):  # quiet
                log.debug("web %s " + fmt, self.client_address[0], *args)

            def _send(self, code: int, body: bytes, ctype: str = "application/json", extra: dict | None = None):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                for k, v in (extra or {}).items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(body)

            def _json(self, code: int, obj) -> None:
                self._send(code, json.dumps(obj).encode())

            def do_GET(self):
                path = self.path.split("?")[0]
                if path == "/":
                    return self._send(200, PAGE.encode(), "text/html; charset=utf-8")
                if path == "/health":
                    return self._json(200, {"ok": True})
                if path == "/api/status":
                    return self._json(200, ui.status())
                if path == "/api/certificates":
                    return self._json(200, ui.certificates())
                if path == "/api/log":
                    return self._json(200, list(ui.ring.lines))
                if path == "/certificates.zip":
                    return self._send(200, ui.zip_all(), "application/zip",
                                      {"Content-Disposition": "attachment; filename=brain-drain-certificates.zip"})
                if path.startswith("/certificates/"):
                    name = unquote(path[len("/certificates/"):])
                    f = Path(ui.cfg.report_dir) / name
                    if "/" in name or not name.endswith(".json") or not f.is_file():
                        return self._json(404, {"error": "no such certificate"})
                    return self._send(200, f.read_bytes(), "application/json",
                                      {"Content-Disposition": f"attachment; filename={name}"})
                return self._json(404, {"error": "not found"})

            def _body(self) -> dict:
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n) if n else b""
                ctype = self.headers.get("Content-Type", "")
                if "json" in ctype:
                    try:
                        return json.loads(raw or b"{}")
                    except ValueError:
                        return {}
                return {k: v[0] for k, v in parse_qs(raw.decode()).items()}

            def do_POST(self):
                path = self.path.split("?")[0]
                data = self._body()
                if ui.wifi is None:
                    return self._json(503, {"error": "no wireless on this unit"})
                if not ui.wifi.check_key(data.get("key")):
                    return self._json(403, {"error": "wrong unit key (it is on the OLED)"})
                if path == "/api/wifi":
                    ssid = str(data.get("ssid", "")).strip()
                    if not ssid:
                        return self._json(400, {"error": "ssid required"})
                    ui.wifi.join(ssid, str(data.get("psk", "")))
                    return self._json(202, {"ok": True, "message": f"joining {ssid}; watch the OLED for the new address"})
                if path == "/api/reset":
                    kind = data.get("kind", "wifi")
                    if kind == "factory":
                        r = ui.wifi.factory_reset()
                        return self._json(200, {"ok": True, "message": "factory reset done, access point restarting", **r})
                    ui.wifi.reset_wifi()
                    return self._json(200, {"ok": True, "message": "network forgotten, access point restarting"})
                return self._json(404, {"error": "not found"})

        self.server = ThreadingHTTPServer((host, port), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, name="webui", daemon=True)

    @property
    def port(self) -> int:
        return self.server.server_address[1]

    def start(self) -> None:
        self.thread.start()
        log.info("phone page on port %d", self.port)

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        logging.getLogger().removeHandler(self.ring)

    # ------------------------------------------------------------------ data
    def status(self) -> dict:
        eng = self.engine
        bays = []
        with eng.lock:
            for b, st in sorted(eng.bays.items()):
                p = st.progress
                bays.append({
                    "bay": b, "state": st.state, "message": st.message, "tier": st.tier_label,
                    "countdown": st.countdown, "slot": st.slot if b == eng.cfg.m2_bay else None,
                    "drive": ({"model": st.drive.model, "serial": st.drive.serial, "size_bytes": st.drive.size_bytes,
                               "media": str(getattr(st.drive.media, "value", st.drive.media))} if st.drive else None),
                    "phase": p.phase, "percent": p.percent, "eta_s": p.eta_s, "rate_bps": p.rate_bps,
                })
        w = self.wifi.snapshot().public() if self.wifi else {"mode": "none"}
        return {"unit": eng.cfg.unit_id, "version": __version__, "policy": eng.policy.label, "dip": eng.policy.dip,
                "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "wifi": w, "bays": bays}

    def certificates(self) -> list[dict]:
        rd = Path(self.cfg.report_dir)
        if not rd.is_dir():
            return []
        out = []
        for f in sorted(rd.glob("*.json")):
            st = f.stat()
            out.append({"name": f.name, "size": st.st_size, "mtime": int(st.st_mtime)})
        return out

    def zip_all(self) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for c in self.certificates():
                z.write(Path(self.cfg.report_dir) / c["name"], c["name"])
        return buf.getvalue()

"""Phone page against the simulated engine: status, certificates, join and reset with the unit key."""
import json
import time
import urllib.error
import urllib.request

import pytest

from braindrain.engine import Engine
from braindrain.hal.sim import SimBayPower, SimDisplay, SimPanel
from braindrain.sim.bays import SimWatcher
from braindrain.webui import WebUI
from braindrain.wifi import SimBackend, WifiManager


@pytest.fixture
def web(sim_cfg, sim_dir):
    cfg = sim_cfg
    cfg.wifi_file = sim_dir / "wifi.json"
    cfg.report_dir = sim_dir / "reports"
    cfg.report_dir.mkdir()
    (cfg.report_dir / "2026-09-23T10-00-00_bay1_SER1.json").write_text(json.dumps({"outcome": "sanitized"}))
    wifi = WifiManager(cfg, SimBackend(sim_dir))
    watcher = SimWatcher(cfg)
    eng = Engine(cfg, watcher, SimPanel(cfg), SimBayPower(cfg), SimDisplay("none", sim_dir), wifi=wifi)
    eng.boot()
    wifi.thread.join()
    ui = WebUI(cfg, eng, wifi, host="127.0.0.1", port=0)
    ui.start()
    yield ui, eng, wifi
    ui.stop()


def get(ui, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{ui.port}{path}", timeout=5) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()


def post(ui, path, data):
    req = urllib.request.Request(f"http://127.0.0.1:{ui.port}{path}", data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_status_page_and_api(web):
    ui, eng, _ = web
    code, ctype, body = get(ui, "/")
    assert code == 200 and "text/html" in ctype and b"brain-drain" in body
    code, _, body = get(ui, "/api/status")
    s = json.loads(body)
    assert s["wifi"]["mode"] == "ap" and "key" not in s["wifi"]
    assert [b["bay"] for b in s["bays"]] == eng.cfg.bays and s["policy"] == "AUTO"


def test_certificates_list_download_and_zip(web):
    ui, _, _ = web
    _, _, body = get(ui, "/api/certificates")
    names = [c["name"] for c in json.loads(body)]
    assert names == ["2026-09-23T10-00-00_bay1_SER1.json"]
    code, ctype, body = get(ui, "/certificates/" + names[0])
    assert code == 200 and json.loads(body)["outcome"] == "sanitized"
    code, ctype, body = get(ui, "/certificates.zip")
    assert code == 200 and "zip" in ctype and body[:2] == b"PK"
    with pytest.raises(urllib.error.HTTPError):
        get(ui, "/certificates/../etc/passwd")


def test_actions_need_the_unit_key(web):
    ui, _, wifi = web
    code, r = post(ui, "/api/wifi", {"ssid": "home", "psk": "pw", "key": "wrong"})
    assert code == 403
    code, r = post(ui, "/api/wifi", {"ssid": "home", "psk": "pw", "key": wifi.state.key})
    assert code == 202
    for _ in range(50):
        if wifi.snapshot().mode == "station":
            break
        time.sleep(0.05)
    assert wifi.snapshot().mode == "station"
    key = wifi.state.key
    code, r = post(ui, "/api/reset", {"kind": "factory", "key": key})
    assert code == 200 and r["certificates_deleted"] == 1
    for _ in range(50):
        if wifi.snapshot().mode == "ap":
            break
        time.sleep(0.05)
    assert wifi.snapshot().mode == "ap" and wifi.state.key != key


def test_idle_display_shows_the_qr_frame(web):
    _, eng, wifi = web
    from braindrain import display
    f = display.frame("AUTO", eng.bays, "unit", "", wifi.snapshot())
    assert f.bitmap is not None and f.text_x >= 60 and f.lines[5].strip() == wifi.state.key
    eng.bays[1].state = "RUNNING"
    f = display.frame("AUTO", eng.bays, "unit", "", wifi.snapshot())
    assert f.bitmap is None and wifi.state.ip in f.lines[7] and wifi.state.key in f.lines[6]

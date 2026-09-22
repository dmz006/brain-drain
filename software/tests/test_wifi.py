"""Wi-Fi manager on the simulated backend: AP by default, join persists, resets return to AP."""
import json

from braindrain import qr
from braindrain.config import Config
from braindrain.wifi import SimBackend, WifiManager, ap_ssid


def make(sim_dir, **kw):
    cfg = Config.for_simulation(sim_dir, **kw)
    cfg.wifi_file = sim_dir / "wifi.json"
    cfg.report_dir = sim_dir / "reports"
    cfg.state_file = sim_dir / "state.json"
    return cfg, WifiManager(cfg, SimBackend(sim_dir))


def test_boots_into_access_point_with_ephemeral_key(sim_dir):
    cfg, w = make(sim_dir)
    w.start(wait=True)
    st = w.snapshot()
    assert st.mode == "ap" and st.ssid == ap_ssid(cfg.unit_id) and st.ip == cfg.ap_ip
    assert len(st.key) == 8 and st.url == f"http://{cfg.ap_ip}/"
    assert "key" not in st.public() and st.public()["url"] == st.url
    assert (sim_dir / "wifi.txt").read_text().startswith("ap ")


def test_join_persists_and_next_boot_joins(sim_dir):
    _, w = make(sim_dir)
    w.start(wait=True)
    w.join("home-net", "hunter22", wait=True)
    st = w.snapshot()
    assert st.mode == "station" and st.ssid == "home-net" and st.ip.startswith("192.168.1.")
    assert json.loads((sim_dir / "wifi.json").read_text()) == {"ssid": "home-net", "psk": "hunter22"}
    _, w2 = make(sim_dir)
    w2.start(wait=True)
    assert w2.snapshot().mode == "station"


def test_failed_join_falls_back_to_access_point(sim_dir):
    _, w = make(sim_dir)
    w.start(wait=True)
    w.join("nope-net", "x", wait=True)
    st = w.snapshot()
    assert st.mode == "ap" and "join nope-net failed" in st.error
    assert not (sim_dir / "wifi.json").exists()


def test_wifi_reset_forgets_and_rotates_key(sim_dir):
    _, w = make(sim_dir)
    w.start(wait=True)
    w.join("home-net", "hunter22", wait=True)
    old_key = w.snapshot().key
    w.reset_wifi(wait=True)
    st = w.snapshot()
    assert st.mode == "ap" and not (sim_dir / "wifi.json").exists() and st.key != old_key


def test_factory_reset_deletes_certificates(sim_dir):
    cfg, w = make(sim_dir)
    cfg.report_dir.mkdir()
    (cfg.report_dir / "a_bay1_X.json").write_text("{}")
    cfg.state_file.write_text("{}")
    w.start(wait=True)
    w.join("home-net", "hunter22", wait=True)
    r = w.factory_reset(wait=True)
    assert r["certificates_deleted"] == 1
    assert not list(cfg.report_dir.glob("*.json")) and not cfg.state_file.exists()
    assert w.snapshot().mode == "ap"


def test_key_check_is_exact():
    cfg = Config()
    w = WifiManager(cfg, SimBackend.__new__(SimBackend))
    assert w.check_key(w.state.key) and not w.check_key(w.state.key.upper()) and not w.check_key(None)


def test_wifi_qr_fits_the_panel():
    m = qr.wifi_matrix("brain-drain-1a2b", "abcd2345")
    assert len(m) == len(m[0]) <= 29            # version 3 or smaller
    assert qr.scale_for(m) * len(m) <= 64
    art = qr.text_art(m)
    assert len(art) == (len(m) + 1) // 2 and all(len(r) == len(m) for r in art)
    assert qr.wifi_payload('a;b', 'p"q') == 'WIFI:T:WPA;S:a\\;b;P:p\\"q;;'

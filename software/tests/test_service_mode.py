"""DIP mode 110 = SERVICE: Wi-Fi reset at boot (factory reset with DIP 8), never wipes."""
from braindrain.policy import Dip, Mode, Policy


def test_service_mode_flags():
    p = Policy.from_dip(Dip.from_string("11000000"))
    assert p.mode is Mode.SERVICE and p.no_wipe and not p.factory_reset and p.label == "SERVICE"
    p = Policy.from_dip(Dip.from_string("11000001"))
    assert p.factory_reset and p.no_wipe
    assert Policy.from_dip(Dip.from_string("00000001")).no_wipe


def test_service_mode_resets_wifi_at_boot(sim_cfg, sim_dir):
    from braindrain.engine import Engine
    from braindrain.hal.sim import SimBayPower, SimDisplay, SimPanel
    from braindrain.sim.bays import SimWatcher
    from braindrain.wifi import SimBackend, WifiManager

    cfg = sim_cfg
    cfg.wifi_file = sim_dir / "wifi.json"
    cfg.wifi_file.write_text('{"ssid": "home", "psk": "pw"}')
    (sim_dir / "dip").write_text("11000000\n")
    wifi = WifiManager(cfg, SimBackend(sim_dir))
    eng = Engine(cfg, SimWatcher(cfg), SimPanel(cfg), SimBayPower(cfg), SimDisplay("none", sim_dir), wifi=wifi)
    eng.boot()
    assert not cfg.wifi_file.exists() and wifi.snapshot().mode == "ap" and eng.policy.label == "SERVICE"

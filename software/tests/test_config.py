import json

from braindrain.config import Config


def test_roundtrip(tmp_path):
    cfg = Config()
    cfg.bay_ports = {1: "1-1.3", 2: "1-1.4"}
    cfg.allowed_bridges = frozenset({("174c", "55aa")})
    cfg.hal = "headless"
    cfg.m2_bay = None
    p = cfg.save(tmp_path / "c.json")
    back = Config.load(p)
    assert back.bay_ports == {1: "1-1.3", 2: "1-1.4"}
    assert back.allowed_bridges == frozenset({("174c", "55aa")})
    assert back.hal == "headless" and back.m2_bay is None
    assert back.bays == [1, 2]


def test_missing_file_gives_defaults(tmp_path):
    cfg = Config.load(tmp_path / "nope.json")
    assert cfg.hal == "real" and cfg.bays == [1, 2, 3, 4, 5]


def test_unknown_key_rejected(tmp_path):
    (tmp_path / "c.json").write_text(json.dumps({"bogus": 1}))
    try:
        Config.load(tmp_path / "c.json")
    except KeyError as e:
        assert "bogus" in str(e)
    else:
        raise AssertionError("expected KeyError")


def test_headless_hal_runs_engine(tmp_path):
    """Headless HAL: fixed DIP policy, log display, always-on bays, no M.2."""
    from braindrain.hal import make_hal

    cfg = Config()
    cfg.hal = "headless"
    cfg.m2_bay = None
    cfg.headless_dip = "01000000"
    panel, power, disp = make_hal(cfg)
    assert str(panel.read_dip()) == "01000000"
    assert power.is_on(1)
    disp.show(["x"] * 8)

import pytest

from braindrain.devices import Drive
from braindrain.policy import Dip, Media, Mode, Policy, method_chain


def drive(media, sim_fw=None):
    d = Drive(bay=1, dev_path="/x", size_bytes=1 << 20, media=media, transport="sim")
    if sim_fw:
        d.sim = {"firmware": sim_fw}
    return d


def test_dip_parsing():
    d = Dip.from_string("10100001")
    assert d.bits == (True, False, True, False, False, False, False, True)
    assert str(d) == "10100001"
    with pytest.raises(ValueError):
        Dip.from_string("1010")


@pytest.mark.parametrize("bits,mode", [
    ("000", Mode.AUTO), ("001", Mode.PURGE), ("010", Mode.CLEAR), ("011", Mode.LEGACY_3PASS),
    ("100", Mode.LEGACY_7PASS), ("101", Mode.CRYPTO_ONLY), ("110", Mode.SERVICE), ("111", Mode.DRY_RUN),
])
def test_mode_index(bits, mode):
    p = Policy.from_dip(Dip.from_string(bits + "00000"))
    assert p.mode is mode
    assert not p.random_pattern and not p.sampled_verify and not p.maintenance


def test_flags():
    p = Policy.from_dip(Dip.from_string("00011001"))
    assert p.random_pattern and p.sampled_verify and p.maintenance
    assert p.label == "MAINT"


def test_auto_hdd_is_single_pass_overwrite():
    p = Policy.from_dip(Dip.from_string("00000000"))
    chain = method_chain(p, drive(Media.HDD))
    assert [m.name for m in chain] == ["overwrite-1pass"]
    assert chain[0].passes == ["zeros"]


def test_auto_ssd_prefers_firmware_then_falls_back():
    p = Policy.from_dip(Dip.from_string("00010000"))
    names = [m.name for m in method_chain(p, drive(Media.SSD))]
    assert names[0] == "ata-sanitize-crypto"
    assert names[-1] == "overwrite-1pass"
    assert "sim-sanitize-block" in names
    assert method_chain(p, drive(Media.SSD))[-1].passes == ["random"]


def test_purge_hdd_chain():
    p = Policy.from_dip(Dip.from_string("00100000"))
    names = [m.name for m in method_chain(p, drive(Media.HDD))]
    assert names[0] == "ata-sanitize-overwrite"
    assert "ata-security-erase-enhanced" in names and names[-1] == "overwrite-1pass"


def test_legacy_passes():
    p3 = Policy.from_dip(Dip.from_string("01100000"))
    p7 = Policy.from_dip(Dip.from_string("10000000"))
    assert method_chain(p3, drive(Media.HDD))[0].passes == ["zeros", "ones", "random"]
    assert len(method_chain(p7, drive(Media.HDD))[0].passes) == 7


def test_crypto_only_has_no_overwrite_fallback():
    p = Policy.from_dip(Dip.from_string("10100000"))
    names = [m.name for m in method_chain(p, drive(Media.SSD))]
    assert all("overwrite" not in n for n in names)
    names = [m.name for m in method_chain(p, drive(Media.NVME))]
    assert names == ["nvme-sanitize-crypto"]


def test_dry_run():
    p = Policy.from_dip(Dip.from_string("11100000"))
    assert [m.name for m in method_chain(p, drive(Media.HDD))] == ["dry-run"]

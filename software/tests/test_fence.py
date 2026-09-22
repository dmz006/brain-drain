from braindrain.config import Config
from braindrain.devices import DevInfo, classify


def info(**kw):
    base = {"dev_path": "/dev/sdb", "sysfs_path": "/sys/x", "devtype": "disk", "removable": False,
            "size_bytes": 4_000_000_000_000, "usb_port": "1-1.2", "bridge_vid": "174c",
            "bridge_pid": "55aa", "is_system": False}
    base.update(kw)
    return DevInfo(**base)


def test_bay_drive_is_allowed():
    bay, why = classify(info(), Config())
    assert bay == 2 and why == "ok"


def test_system_disk_is_never_a_candidate():
    bay, why = classify(info(is_system=True), Config())
    assert bay is None and "mounted" in why


def test_partition_is_rejected():
    assert classify(info(devtype="partition"), Config())[0] is None


def test_internal_sata_is_rejected():
    bay, why = classify(info(usb_port=None, bridge_vid=None, bridge_pid=None), Config())
    assert bay is None and "USB" in why


def test_unknown_bridge_is_rejected():
    bay, why = classify(info(bridge_vid="152d", bridge_pid="0578"), Config())
    assert bay is None and "allow-list" in why


def test_non_bay_port_is_rejected():
    bay, why = classify(info(usb_port="3-4"), Config())
    assert bay is None and "not a bay" in why


def test_empty_bridge_is_rejected():
    assert classify(info(size_bytes=0), Config())[0] is None

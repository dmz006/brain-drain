from braindrain.methods.ata import parse_identify, parse_sanitize_status
from braindrain.methods.nvme import parse_sanitize_log
from braindrain.progress import Progress, fmt_eta, fmt_rate, fmt_size

HDPARM_I = """
/dev/sdb:

ATA device, with non-removable media
\tModel Number:       WDC WD40EFRX-68N32N0
\tSerial Number:      WD-WCC7K1234567
\tFirmware Revision:  82.00A82
\tTransport:          Serial, ATA8-AST, SATA 1.0a, SATA II Extensions, SATA Rev 2.5, SATA Rev 2.6, SATA Rev 3.0
Standards:
Configuration:
\tNominal Media Rotation Rate: 5400
Commands/features:
\tEnabled\tSupported:
\t   *\tSMART feature set
\t   *\tSecurity Mode feature set
\t   *\tSANITIZE feature set
\t   *\tOVERWRITE_EXT command
\t   *\tBLOCK_ERASE_EXT command
Security:
\tMaster password revision code = 65534
\t\tsupported
\tnot\tenabled
\tnot\tlocked
\tnot\tfrozen
\tnot\texpired: security count
\t\tsupported: enhanced erase
\t510min for SECURITY ERASE UNIT. 510min for ENHANCED SECURITY ERASE UNIT.
Checksum: correct
"""

HDPARM_I_SSD_FROZEN = """
\tModel Number:       Samsung SSD 860 EVO 1TB
\tSerial Number:      S3Z8NB0K123456A
\tFirmware Revision:  RVT04B6Q
\tNominal Media Rotation Rate: Solid State Device
\t   *\tSANITIZE feature set
\t   *\tCRYPTO_SCRAMBLE_EXT command
\t   *\tBLOCK_ERASE_EXT command
Security:
\tMaster password revision code = 65534
\t\tsupported
\tnot\tenabled
\tnot\tlocked
\t\tfrozen
\tnot\texpired: security count
\t\tsupported: enhanced erase
\t2min for SECURITY ERASE UNIT. 8min for ENHANCED SECURITY ERASE UNIT.
"""


def test_parse_identify_hdd():
    i = parse_identify(HDPARM_I)
    assert i["model"] == "WDC WD40EFRX-68N32N0"
    assert i["serial"] == "WD-WCC7K1234567"
    assert i["rotation_rpm"] == 5400
    assert i["sanitize"] and i["sanitize_overwrite"] and i["sanitize_block"] and not i["sanitize_crypto"]
    assert i["security"] and not i["security_frozen"] and i["security_enhanced"]
    assert i["erase_minutes"] == 510 and i["enhanced_erase_minutes"] == 510


def test_parse_identify_ssd_frozen():
    i = parse_identify(HDPARM_I_SSD_FROZEN)
    assert i["rotation_rpm"] == 0
    assert i["sanitize_crypto"] and i["security_frozen"]
    assert i["enhanced_erase_minutes"] == 8


def test_parse_sanitize_status_variants():
    assert parse_sanitize_status("Sanitize status:\n\tState:  SD3 Sanitize operation In Progress\n\tProgress: 0x28f5 (16%)") == ("in_progress", 0.16)
    assert parse_sanitize_status("Sanitize status:\n\tState:  SD0 Sanitize Idle")[0] == "idle"
    assert parse_sanitize_status("Sanitize Failed")[0] == "failed"
    st, frac = parse_sanitize_status("State: In Progress\n Progress: 0x8000")
    assert st == "in_progress" and abs(frac - 0.5) < 0.01


def test_parse_nvme_log():
    assert parse_sanitize_log('{"sprog":32767,"sstat":2}') == ("in_progress", 32767 / 65535)
    assert parse_sanitize_log('{"sprog":65535,"sstat":257}')[0] == "success"
    assert parse_sanitize_log("garbage")[0] == "unknown"


def test_progress_rate_and_eta():
    import time

    p = Progress()
    p.update("OVW", 0.0, 0)
    time.sleep(0.05)
    p.update("OVW", 0.5, 50_000_000)
    assert p.rate_bps and p.rate_bps > 0
    assert p.percent == 50


def test_formatters():
    assert fmt_eta(None) == "--:--"
    assert fmt_eta(45) == "45s"
    assert fmt_eta(125) == "2m05"
    assert fmt_eta(3600 * 6 + 60 * 12) == "6h12"
    assert fmt_eta(40 * 3600) == "40h"
    assert fmt_rate(150e6) == "150M"
    assert fmt_size(4_000_787_030_016) == "4.0T"
    assert fmt_size(256 * 1024 * 1024) == "268M"

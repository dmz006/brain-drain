"""Wi-Fi QR code for the OLED: the standard WIFI:T:WPA;S:<ssid>;P:<key>;; payload as a
module matrix, plus a text-art form for the simulated display."""

from __future__ import annotations


def _esc(s: str) -> str:
    return "".join("\\" + c if c in '\\;,":' else c for c in s)


def wifi_payload(ssid: str, key: str) -> str:
    return f"WIFI:T:WPA;S:{_esc(ssid)};P:{_esc(key)};;"


def matrix(text: str) -> list[list[bool]]:
    import qrcode

    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, border=0)
    q.add_data(text)
    q.make(fit=True)
    return [[bool(v) for v in row] for row in q.get_matrix()]


def wifi_matrix(ssid: str, key: str) -> list[list[bool]]:
    return matrix(wifi_payload(ssid, key))


def scale_for(m: list[list[bool]], height: int = 64) -> int:
    """Largest whole-pixel module size that fits the panel height (2 px for a version 3 code)."""
    n = len(m)
    return max(1, height // n)


def text_art(m: list[list[bool]]) -> list[str]:
    """Two matrix rows per text row with half-block characters."""
    glyph = {(False, False): " ", (True, False): "▀", (False, True): "▄", (True, True): "█"}
    rows = m + [[False] * len(m[0])] if len(m) % 2 else m
    return ["".join(glyph[(rows[r][c], rows[r + 1][c])] for c in range(len(m[0]))) for r in range(0, len(rows), 2)]

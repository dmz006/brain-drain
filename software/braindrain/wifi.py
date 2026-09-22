"""Wireless: access point with an ephemeral key, joining the owner's network, resets (C22).

The unit boots into access-point mode unless a saved station config exists. The AP
key is regenerated on every boot and shown on the OLED (as text and as a Wi-Fi QR code);
the same key authorises actions on the phone page. A saved station config (pushed from
the page) makes the unit join that network at boot; a Wi-Fi reset (page, DIP service
mode, or `braindrain wifi-reset`) forgets it and returns to the access point. A factory
reset also clears the certificates and the crash-recovery state.

Real backend: NetworkManager via `nmcli` (Raspberry Pi OS Bookworm and newer).
"""

from __future__ import annotations

import abc
import hashlib
import hmac
import json
import logging
import secrets
import shutil
import subprocess
import threading
from dataclasses import asdict, dataclass
from pathlib import Path

log = logging.getLogger(__name__)

AP_CON = "brain-drain-ap"
STA_CON = "brain-drain-sta"
KEY_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"   # no 0/O/1/l/i look-alikes: it is typed from the OLED


def make_key(n: int = 8) -> str:
    return "".join(secrets.choice(KEY_ALPHABET) for _ in range(n))


def ap_ssid(unit_id: str) -> str:
    tag = hashlib.sha256(unit_id.encode()).hexdigest()[:4]
    return f"brain-drain-{tag}"


@dataclass
class WifiState:
    mode: str = "off"        # off | ap | joining | station
    ssid: str = ""
    key: str = ""            # AP passphrase and the phone-page action key, ephemeral per boot
    ip: str = ""
    error: str = ""

    @property
    def url(self) -> str:
        return f"http://{self.ip}/" if self.ip else ""

    def public(self) -> dict:
        d = asdict(self)
        d.pop("key")
        d["url"] = self.url
        return d


class Backend(abc.ABC):
    @abc.abstractmethod
    def start_ap(self, iface: str, ssid: str, key: str, ip: str) -> str:
        """Bring up the access point; returns the unit's IP on it."""

    @abc.abstractmethod
    def join(self, iface: str, ssid: str, psk: str, timeout: float) -> str:
        """Join a network; returns the IP or raises RuntimeError."""

    @abc.abstractmethod
    def forget(self, iface: str) -> None:
        """Drop the station profile."""


class SimBackend(Backend):
    """Writes the pretend link state to <sim_dir>/wifi.txt. A network whose name starts with
    'nope' or whose key is 'wrong' refuses to join, for tests."""

    def __init__(self, sim_dir: Path):
        self.file = Path(sim_dir) / "wifi.txt"

    def _write(self, text: str) -> None:
        self.file.write_text(text + "\n")

    def start_ap(self, iface, ssid, key, ip):
        self._write(f"ap {ssid} {key} {ip}")
        return ip

    def join(self, iface, ssid, psk, timeout):
        if ssid.startswith("nope") or psk == "wrong":
            raise RuntimeError(f"could not join {ssid!r}")
        ip = "192.168.1." + str(50 + sum(map(ord, ssid)) % 200)
        self._write(f"station {ssid} {ip}")
        return ip

    def forget(self, iface):
        self._write("off")


class NmcliBackend(Backend):
    def __init__(self):
        if not shutil.which("nmcli"):
            raise RuntimeError("nmcli not found: install network-manager")

    @staticmethod
    def _run(*args, check=True, timeout=60) -> str:
        cp = subprocess.run(["nmcli", *args], capture_output=True, text=True, timeout=timeout, check=False)
        if check and cp.returncode != 0:
            raise RuntimeError((cp.stderr or cp.stdout).strip() or f"nmcli {' '.join(args)} failed")
        return cp.stdout

    def _ip(self, iface: str) -> str:
        out = self._run("-g", "IP4.ADDRESS", "device", "show", iface, check=False)
        return out.strip().split("\n")[0].split("/")[0] if out.strip() else ""

    def start_ap(self, iface, ssid, key, ip):
        self._run("connection", "delete", AP_CON, check=False)
        self._run("device", "wifi", "hotspot", "ifname", iface, "con-name", AP_CON, "ssid", ssid, "password", key)
        self._run("connection", "modify", AP_CON, "ipv4.addresses", f"{ip}/24", "ipv4.method", "shared",
                  "connection.autoconnect", "no")
        self._run("connection", "up", AP_CON)
        return ip

    def join(self, iface, ssid, psk, timeout):
        self._run("connection", "down", AP_CON, check=False)
        self._run("connection", "delete", STA_CON, check=False)
        try:
            self._run("device", "wifi", "connect", ssid, "password", psk, "ifname", iface, "name", STA_CON,
                      timeout=timeout)
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            self._run("connection", "delete", STA_CON, check=False)
            raise RuntimeError(str(e)) from e
        ip = self._ip(iface)
        if not ip:
            raise RuntimeError("joined but no IPv4 address")
        return ip

    def forget(self, iface):
        self._run("connection", "delete", STA_CON, check=False)


class WifiManager:
    def __init__(self, cfg, backend: Backend):
        self.cfg = cfg
        self.backend = backend
        self.state = WifiState(key=make_key())
        self.lock = threading.Lock()
        self.thread: threading.Thread | None = None

    # ------------------------------------------------------------------ persistence
    def saved(self) -> dict | None:
        try:
            d = json.loads(Path(self.cfg.wifi_file).read_text())
            return d if d.get("ssid") else None
        except (OSError, ValueError):
            return None

    def _save(self, ssid: str, psk: str) -> None:
        p = Path(self.cfg.wifi_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"ssid": ssid, "psk": psk}) + "\n")
        try:
            p.chmod(0o600)
        except OSError:
            pass

    def _forget_saved(self) -> None:
        try:
            Path(self.cfg.wifi_file).unlink()
        except OSError:
            pass

    # ------------------------------------------------------------------ bring-up
    def start(self, wait: bool = False) -> None:
        """Join the saved network if there is one, else start the access point. Runs in a
        thread so the engine can boot while NetworkManager works."""
        saved = self.saved()

        def run():
            if saved:
                self._join(saved["ssid"], saved["psk"], persist=False)
            else:
                self._start_ap()

        self.thread = threading.Thread(target=run, name="wifi", daemon=True)
        self.thread.start()
        if wait:
            self.thread.join()

    def _start_ap(self) -> None:
        ssid = ap_ssid(self.cfg.unit_id)
        with self.lock:
            self.state.mode = "joining"
        try:
            ip = self.backend.start_ap(self.cfg.wifi_iface, ssid, self.state.key, self.cfg.ap_ip)
            with self.lock:
                self.state.mode, self.state.ssid, self.state.ip, self.state.error = "ap", ssid, ip, ""
            log.info("access point %s up at %s", ssid, ip)
        except Exception as e:  # noqa: BLE001
            with self.lock:
                self.state.mode, self.state.ssid, self.state.ip, self.state.error = "off", ssid, "", str(e)
            log.error("access point failed: %s", e)

    def _join(self, ssid: str, psk: str, persist: bool) -> bool:
        with self.lock:
            self.state.mode, self.state.ssid, self.state.error = "joining", ssid, ""
        try:
            ip = self.backend.join(self.cfg.wifi_iface, ssid, psk, self.cfg.wifi_join_timeout)
        except Exception as e:  # noqa: BLE001
            log.error("join %s failed: %s; back to the access point", ssid, e)
            self._start_ap()
            with self.lock:
                self.state.error = f"join {ssid} failed: {e}"
            return False
        if persist:
            self._save(ssid, psk)
        with self.lock:
            self.state.mode, self.state.ip = "station", ip
        log.info("joined %s at %s", ssid, ip)
        return True

    def join(self, ssid: str, psk: str, wait: bool = False) -> None:
        """Asked from the phone page: join now and remember it for the next boot."""
        t = threading.Thread(target=self._join, args=(ssid, psk, True), name="wifi-join", daemon=True)
        t.start()
        if wait:
            t.join()

    # ------------------------------------------------------------------ resets
    def reset_wifi(self, wait: bool = False) -> None:
        self._forget_saved()
        try:
            self.backend.forget(self.cfg.wifi_iface)
        except Exception as e:  # noqa: BLE001
            log.warning("forget: %s", e)
        with self.lock:
            self.state.key = make_key()
        t = threading.Thread(target=self._start_ap, name="wifi-reset", daemon=True)
        t.start()
        if wait:
            t.join()

    def factory_reset(self, wait: bool = False) -> dict:
        """Wi-Fi reset plus: certificates and the crash-recovery state are deleted."""
        removed = 0
        rd = Path(self.cfg.report_dir)
        if rd.is_dir():
            for f in rd.glob("*.json"):
                try:
                    f.unlink(); removed += 1
                except OSError:
                    pass
        try:
            Path(self.cfg.state_file).unlink()
        except OSError:
            pass
        self.reset_wifi(wait=wait)
        log.warning("factory reset: %d certificate(s) deleted, Wi-Fi forgotten", removed)
        return {"certificates_deleted": removed}

    def check_key(self, key: str | None) -> bool:
        return bool(key) and hmac.compare_digest(str(key), self.state.key)

    def snapshot(self) -> WifiState:
        with self.lock:
            return WifiState(**asdict(self.state))

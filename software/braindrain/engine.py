"""Per-bay state machine and job workers. ARCHITECTURE.md §4.6.

    IDLE -(add)-> DETECTED -(grace elapsed)-> RUNNING -> DONE | ERROR | ABORTED
    any state -(remove)-> IDLE
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field

from . import display, report, verify
from .devices import Drive
from .methods.base import Cancelled, MethodError, RunContext
from .policy import Media, Policy, Tier, method_chain
from .progress import Progress

log = logging.getLogger(__name__)

TIER_RANK = {Tier.NONE: 0, Tier.CLEAR: 1, Tier.PURGE: 2}


@dataclass
class BayStatus:
    bay: int
    state: str = "IDLE"
    drive: Drive | None = None
    progress: Progress = field(default_factory=Progress)
    message: str = ""
    tier_label: str = ""
    countdown: int = 0
    detected_at: float = 0.0
    done_at: float = 0.0
    done_serial: str | None = None
    cancel: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None
    cert: report.Certificate | None = None
    cert_path: str | None = None
    # bay 5 only
    slot: str = "OFF"          # OFF | POWERING | ON | LATCHED (timed out, wait for a door cycle)
    slot_since: float = 0.0


class Engine:
    def __init__(self, cfg, watcher, panel, bay_power, disp, unit_line_fn=None):
        self.cfg = cfg
        self.watcher = watcher
        self.panel = panel
        self.bay_power = bay_power
        self.display = disp
        self.unit_line_fn = unit_line_fn or (lambda: f"{cfg.unit_id}")
        self.bays: dict[int, BayStatus] = {b: BayStatus(b) for b in cfg.bays}
        self.policy: Policy = Policy.from_dip(panel.read_dip())
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.message = ""

    # ------------------------------------------------------------------ lifecycle

    def boot(self) -> None:
        prior = report.load_state(self.cfg.state_file)
        if prior:
            paths = report.write_interrupted(self.cfg, prior)
            log.warning("previous session was interrupted; wrote %d certificate(s)", len(paths))
            report.save_state(self.cfg.state_file, {})
        if self.cfg.m2_bay is not None:
            self.bay_power.set(self.cfg.m2_bay, False)  # the M.2 slot stays dark until its door is shut
        for i, bay in enumerate(self.cfg.usb_bays):
            if i and self.cfg.stagger_seconds > 0:
                self.message = f"powering bay {bay}..."
                self.draw()
                if self.stop.wait(self.cfg.stagger_seconds):
                    return
            self.bay_power.set(bay, True)
        self.message = ""
        self.panel.set_status("green")

    def run_forever(self) -> None:
        self.boot()
        last_draw = 0.0
        try:
            while not self.stop.is_set():
                self.step()
                now = time.monotonic()
                if now - last_draw >= 1.0 / self.cfg.display_hz:
                    self.draw()
                    last_draw = now
                self.stop.wait(self.cfg.poll_interval)
        finally:
            for st in self.bays.values():
                st.cancel.set()
            for st in self.bays.values():
                if st.thread and st.thread.is_alive():
                    st.thread.join(timeout=10)
            self.draw()

    def step(self) -> None:
        """One scheduler tick: consume watcher events, start jobs whose grace expired."""
        for ev in self.watcher.poll():
            if ev.action == "add":
                self.on_add(ev.bay, ev.drive)
            else:
                self.on_remove(ev.bay)
        now = time.monotonic()
        if self.cfg.m2_bay is not None:
            self.step_m2(now)
        for st in self.bays.values():
            if st.state == "DETECTED":
                remaining = self.cfg.grace_seconds - (now - st.detected_at)
                st.countdown = max(0, int(remaining + 0.999))
                if remaining <= 0:
                    self.start_job(st)

    # ------------------------------------------------------------------- bay 5

    def step_m2(self, now: float) -> None:
        """Door shut + PCIe module -> power the slot and rescan; door open -> abort, detach, power off."""
        bay = self.cfg.m2_bay
        st = self.bays[bay]
        closed = self.panel.m2_door_closed()
        if not closed:
            if st.slot != "OFF":
                log.info("bay %d: door opened", bay)
                if st.state in ("DETECTED", "RUNNING", "DONE", "ERROR", "ABORTED"):
                    dev = st.drive.sysfs_path if st.drive else ""
                    self.on_remove(bay)
                    if dev:
                        self.bay_power.pci_remove(dev)
                self.bay_power.set(bay, False)
                st.slot = "OFF"
            st.message = ""
            return
        if st.slot == "LATCHED":
            return
        if st.slot == "OFF":
            if not self.panel.m2_pedet_pcie():
                if self.message != "bay 5: SATA M.2 not supported":
                    log.warning("bay %d: PEDET low, M.2 SATA module refused", bay)
                self.message = "bay 5: SATA M.2 not supported"
                return
            self.bay_power.set(bay, True)
            st.slot, st.slot_since = "POWERING", now
            self.message = ""
            return
        if st.slot == "POWERING" and now - st.slot_since >= self.cfg.m2_settle_seconds:
            self.bay_power.pci_rescan()
            st.slot, st.slot_since = "ON", now
            return
        if st.slot == "ON" and st.state == "IDLE" and now - st.slot_since > self.cfg.m2_appear_seconds:
            # nothing enumerated: power down and wait for the next door cycle
            log.warning("bay %d: no NVMe device appeared within %.0fs; powering slot off", bay, self.cfg.m2_appear_seconds)
            self.bay_power.set(bay, False)
            st.slot = "LATCHED"
            self.message = "bay 5: no NVMe found, reopen door"

    # --------------------------------------------------------------------- events

    def on_add(self, bay: int, drive: Drive) -> None:
        st = self.bays[bay]
        self.policy = Policy.from_dip(self.panel.read_dip())
        if st.state == "DONE" and st.done_serial == drive.serial and \
                time.monotonic() - st.done_at < self.cfg.reinsert_guard_seconds:
            log.info("bay %d: %s re-enumerated within guard window, staying DONE", bay, drive.serial)
            st.drive = drive
            return
        if st.state != "IDLE":
            log.warning("bay %d: add while %s; treating as re-plug", bay, st.state)
            self.on_remove(bay)
        st.drive = drive
        st.progress = Progress()
        st.message = ""
        st.cancel = threading.Event()
        if self.policy.maintenance:
            st.state = "IDLE"
            self.message = "MAINT: wipes disabled"
            log.warning("bay %d: %s %s detected but maintenance mode is on", bay, drive.model, drive.serial)
            return
        st.state = "DETECTED"
        st.detected_at = time.monotonic()
        st.countdown = int(self.cfg.grace_seconds + 0.999)
        log.info("bay %d: detected %s %s %s %d bytes; wiping in %.0fs (mode %s)",
                 bay, drive.model, drive.serial, drive.media.value, drive.size_bytes,
                 self.cfg.grace_seconds, self.policy.label)
        self.panel.buzz("tick")

    def on_remove(self, bay: int) -> None:
        st = self.bays[bay]
        prev = st.state
        if prev == "RUNNING":
            st.cancel.set()
            if st.thread:
                st.thread.join(timeout=30)
        st.state = "IDLE"
        st.drive = None
        st.message = ""
        st.thread = None
        self._save_state()
        log.info("bay %d: drive removed (was %s)", bay, prev)

    # ------------------------------------------------------------------------ job

    def start_job(self, st: BayStatus) -> None:
        st.state = "RUNNING"
        st.progress = Progress()
        st.cert = report.new_certificate(self.cfg, st.drive, self.policy)
        self._save_state()
        st.thread = threading.Thread(target=self._job, args=(st,), name=f"bay{st.bay}", daemon=True)
        st.thread.start()

    def _job(self, st: BayStatus) -> None:
        drive, cert = st.drive, st.cert
        assert drive and cert
        blog = logging.getLogger(f"braindrain.bay{st.bay}")
        ctx = RunContext(cancel=st.cancel, progress=st.progress.update, config=self.cfg, log=blog,
                         policy=self.policy)
        t0 = time.monotonic()
        try:
            self._run_chain(st, drive, cert, ctx, blog)
        except Cancelled:
            cert.outcome = "aborted"
            cert.notes.append("drive removed or job cancelled before completion; NOT sanitized")
            st.state = "ABORTED"
            st.message = "removed"
            blog.warning("aborted")
        except Exception as e:  # noqa: BLE001
            cert.outcome = "failed"
            cert.notes.append(f"unexpected error: {e!r}")
            st.state = "ERROR"
            st.message = str(e)[:40]
            blog.exception("job crashed")
        finally:
            cert.finished = report.now_iso()
            cert.elapsed_s = round(time.monotonic() - t0, 1)
            if cert.elapsed_s and drive.size_bytes and cert.outcome == "sanitized":
                cert.throughput_bps = round(drive.size_bytes / cert.elapsed_s)
            try:
                st.cert_path = str(report.write_certificate(cert, self.cfg.report_dir))
                blog.info("certificate: %s", st.cert_path)
            except OSError as e:
                blog.error("could not write certificate: %s", e)
            if st.state == "DONE":
                self.panel.buzz("done")
            elif st.state == "ERROR":
                self.panel.buzz("error")
            self._save_state()

    def _run_chain(self, st, drive, cert, ctx, blog) -> None:
        chain = method_chain(self.policy, drive)
        blog.info("method chain: %s", [m.name for m in chain])
        result = None
        used = None
        for m in chain:
            ok, why = m.supported(drive)
            att = report.Attempt(method=m.name, supported=ok, reason=why)
            cert.attempts.append(att)
            if not ok:
                blog.info("skip %s: %s", m.name, why)
                continue
            canaries = None
            if m.firmware and self.policy.mode.name != "DRY_RUN":
                canaries = verify.write_canaries(drive, self.cfg, blog)
            att.started = report.now_iso()
            try:
                blog.info("running %s", m.name)
                result = m.run(drive, ctx)
                att.ok, att.detail, att.facts = result.ok, result.detail, result.facts
                att.finished = report.now_iso()
                if result.ok:
                    used = m
                    result.facts["canaries"] = canaries
                    break
            except MethodError as e:
                att.ok, att.detail, att.finished = False, str(e), report.now_iso()
                blog.warning("%s failed: %s", m.name, e)
                continue
        if not used or not result:
            cert.outcome = "failed"
            cert.notes.append("no method in the chain succeeded")
            st.state = "ERROR"
            st.message = "no method"
            return

        cert.method_used = used.name
        if used.name == "dry-run":
            cert.outcome = "dry-run"
            cert.tier_claimed = Tier.NONE.value
            st.state = "DONE"
            st.tier_label = "DRY"
            return

        # ----- verification
        ctx.progress("VRFY", 0.0, None)
        if used.firmware:
            vres = verify.check_canaries(drive, result.facts.pop("canaries") or [], ctx)
        elif self.policy.sampled_verify:
            vres = verify.sampled_verify(drive, result.expect_block, ctx)
        else:
            vres = verify.full_verify(drive, result.expect_block, ctx)
        cert.verification = {"kind": vres.kind, "ok": vres.ok, "detail": vres.detail,
                             "bytes_checked": vres.bytes_checked, "mismatches": vres.mismatches[:16],
                             **vres.facts}
        if not vres.ok:
            cert.outcome = "failed"
            cert.tier_claimed = Tier.NONE.value
            cert.notes.append(f"verification failed: {vres.detail}")
            st.state = "ERROR"
            st.message = "verify fail"
            return

        tier = used.tier
        if tier is Tier.CLEAR and drive.media in (Media.SSD, Media.NVME):
            cert.notes.append("host overwrite on flash media may not reach over-provisioned or "
                              "remapped blocks; Clear only, not Purge")
        cert.tier_claimed = tier.value
        cert.outcome = "sanitized"
        st.tier_label = tier.name
        st.state = "DONE"
        st.done_serial = drive.serial
        st.done_at = time.monotonic()
        blog.info("sanitized (%s via %s, verify %s)", tier.name, used.name, vres.kind)

    # ---------------------------------------------------------------------- misc

    def _save_state(self) -> None:
        running = {}
        for b, st in self.bays.items():
            if st.state == "RUNNING" and st.cert:
                running[b] = {"drive": st.cert.drive, "policy": st.cert.policy, "started": st.cert.started}
        try:
            report.save_state(self.cfg.state_file, running)
        except OSError as e:
            log.error("state save failed: %s", e)

    def draw(self) -> None:
        lines = display.render(self.policy.label, self.bays, self.unit_line_fn(), self.message)
        try:
            self.display.show(lines)
        except Exception as e:  # noqa: BLE001
            log.error("display: %s", e)
        if self.cfg.display_file:
            try:
                self.cfg.display_file.parent.mkdir(parents=True, exist_ok=True)
                self.cfg.display_file.write_text("\n".join(lines) + "\n")
            except OSError:
                pass

    def bay_states(self) -> dict[int, str]:
        return {b: st.state for b, st in self.bays.items()}

    def m2_visible(self, bay: int) -> bool:
        """For the simulated watcher: the M.2 bay only enumerates while its slot is powered and rescanned."""
        if bay != self.cfg.m2_bay:
            return True
        return self.bays[bay].slot == "ON"

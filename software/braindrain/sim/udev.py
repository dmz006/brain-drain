"""Real udev-driven watcher producing the same events as SimWatcher. Needs pyudev."""

from __future__ import annotations

import logging
import queue
import threading

from ..devices import DevInfo, classify, collect_real, identify_real, system_devices
from .bays import SimEvent

log = logging.getLogger(__name__)


class UdevWatcher:
    def __init__(self, cfg):
        import pyudev

        self.cfg = cfg
        self.present: dict[int, str] = {}  # bay -> dev_path
        self.q: queue.Queue = queue.Queue()
        self.ctx = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.ctx)
        self.monitor.filter_by("block", "disk")
        self.observer = pyudev.MonitorObserver(self.monitor, callback=self._cb, name="udev-watch")
        self.observer.daemon = True
        self.observer.start()
        for info, bay, reason in collect_real(cfg):
            if bay is not None:
                self.q.put(("add", bay, info))
            else:
                log.debug("ignoring %s: %s", info.dev_path, reason)

    def _cb(self, device):
        action = device.action
        if action == "add":
            # Re-run the whole collection for this device so the fence sees fresh mount state
            for info, bay, reason in collect_real(self.cfg):
                if info.dev_path == device.device_node:
                    if bay is not None:
                        self.q.put(("add", bay, info))
                    else:
                        log.info("ignoring %s: %s", info.dev_path, reason)
        elif action == "remove":
            for bay, path in list(self.present.items()):
                if path == device.device_node:
                    self.q.put(("remove", bay, None))

    def poll(self) -> list[SimEvent]:
        events: list[SimEvent] = []
        while True:
            try:
                action, bay, info = self.q.get_nowait()
            except queue.Empty:
                break
            if action == "add":
                if bay in self.present:
                    continue
                try:
                    drive = identify_real(bay, info)
                except Exception as e:  # noqa: BLE001
                    log.error("identify %s failed: %s", info.dev_path, e)
                    continue
                self.present[bay] = info.dev_path
                events.append(SimEvent("add", bay, drive))
            else:
                self.present.pop(bay, None)
                events.append(SimEvent("remove", bay))
        return events

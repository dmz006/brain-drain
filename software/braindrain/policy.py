"""DIP switch decoding and NIST SP 800-88 Rev. 2 policy selection.

ARCHITECTURE.md §4.4 and §4.5. The DIP switch is the only control on the unit:

    DIP 1-3  mode index (ON = 1, DIP1 is the MSB)
    DIP 4    overwrite pattern: ON = random block, OFF = zeros
    DIP 5    verification:      ON = sampled,      OFF = full read-back
    DIP 6-7  reserved
    DIP 8    maintenance:       ON = never wipe
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Mode(Enum):
    AUTO = 0  # HDD: Clear (1-pass + full verify). SSD/NVMe: Purge (firmware sanitize)
    PURGE = 1  # firmware sanitize / secure erase for everything, overwrite as last resort
    CLEAR = 2  # host overwrite, 1 pass, for everything
    LEGACY_3PASS = 3  # 0x00, 0xFF, random
    LEGACY_7PASS = 4  # DoD 5220.22-M ECE style
    CRYPTO_ONLY = 5  # cryptographic erase only, fail if unsupported
    RESERVED = 6
    DRY_RUN = 7  # exercise everything, write nothing

    @property
    def label(self) -> str:
        return {
            Mode.AUTO: "AUTO",
            Mode.PURGE: "PURGE",
            Mode.CLEAR: "CLEAR",
            Mode.LEGACY_3PASS: "3PASS",
            Mode.LEGACY_7PASS: "7PASS",
            Mode.CRYPTO_ONLY: "CRYPT",
            Mode.RESERVED: "RSRVD",
            Mode.DRY_RUN: "DRY",
        }[self]


class Media(Enum):
    HDD = "hdd"
    SSD = "ssd"
    NVME = "nvme"
    UNKNOWN = "unknown"


class Tier(Enum):
    """NIST SP 800-88 sanitization tier actually achieved."""

    NONE = "none"
    CLEAR = "clear"
    PURGE = "purge"


@dataclass(frozen=True)
class Dip:
    """Eight switch positions; True means ON. Index 0 is DIP 1."""

    bits: tuple[bool, bool, bool, bool, bool, bool, bool, bool]

    @classmethod
    def from_string(cls, s: str) -> Dip:
        s = s.strip()
        if len(s) != 8 or any(c not in "01" for c in s):
            raise ValueError(f"DIP string must be 8 chars of 0/1, got {s!r}")
        return cls(tuple(c == "1" for c in s))  # type: ignore[arg-type]

    def __str__(self) -> str:
        return "".join("1" if b else "0" for b in self.bits)


@dataclass(frozen=True)
class Policy:
    mode: Mode
    random_pattern: bool
    sampled_verify: bool
    maintenance: bool
    dip: str

    @classmethod
    def from_dip(cls, dip: Dip) -> Policy:
        b = dip.bits
        idx = (b[0] << 2) | (b[1] << 1) | b[2]
        return cls(
            mode=Mode(idx),
            random_pattern=b[3],
            sampled_verify=b[4],
            maintenance=b[7],
            dip=str(dip),
        )

    @property
    def label(self) -> str:
        if self.maintenance:
            return "MAINT"
        return self.mode.label


def method_chain(policy: Policy, drive) -> list:
    """Ordered list of Method instances to try for this drive; first success wins.

    Real firmware methods report unsupported on simulated drives, and the
    simulated firmware method reports unsupported on real ones, so one chain
    serves both.
    """
    from .methods import ata, nvme, overwrite, simfw
    from .methods.dryrun import DryRun

    pattern = "random" if policy.random_pattern else "zeros"
    one_pass = overwrite.Overwrite([pattern])
    media = drive.media

    if policy.mode is Mode.DRY_RUN:
        return [DryRun()]
    if policy.mode is Mode.CLEAR:
        return [one_pass]
    if policy.mode is Mode.LEGACY_3PASS:
        return [overwrite.Overwrite(["zeros", "ones", "random"])]
    if policy.mode is Mode.LEGACY_7PASS:
        return [overwrite.Overwrite(["zeros", "ones", "random", "zeros", "ones", "random", "random"])]

    if policy.mode is Mode.CRYPTO_ONLY:
        if media is Media.NVME:
            return [nvme.NvmeSanitize("crypto")]
        return [ata.AtaSanitize("crypto"), simfw.SimSanitize("crypto")]

    ssd_purge = [
        ata.AtaSanitize("crypto"),
        ata.AtaSanitize("block"),
        ata.AtaSecurityErase(enhanced=True),
        simfw.SimSanitize("crypto"),
        simfw.SimSanitize("block"),
    ]
    nvme_purge = [
        nvme.NvmeSanitize("crypto"),
        nvme.NvmeSanitize("block"),
        nvme.NvmeFormat(ses=1),
        simfw.SimSanitize("crypto"),
        simfw.SimSanitize("block"),
    ]
    hdd_purge = [
        ata.AtaSanitize("overwrite"),
        ata.AtaSecurityErase(enhanced=True),
        ata.AtaSecurityErase(enhanced=False),
        simfw.SimSanitize("overwrite"),
    ]

    if policy.mode is Mode.AUTO:
        if media is Media.HDD:
            return [one_pass]
        if media is Media.SSD:
            return ssd_purge + [one_pass]
        if media is Media.NVME:
            return nvme_purge + [one_pass]
        return [one_pass]

    # PURGE (and RESERVED, treated as PURGE)
    if media is Media.HDD:
        return hdd_purge + [one_pass]
    if media is Media.SSD:
        return ssd_purge + [one_pass]
    if media is Media.NVME:
        return nvme_purge + [one_pass]
    return [one_pass]

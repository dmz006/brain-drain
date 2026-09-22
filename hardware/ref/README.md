# Reference data

* `cm5-pinout.csv` — all 200 CM5 connector pins, extracted from Table 4 of the
  official Raspberry Pi Compute Module 5 datasheet
  (https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf, September 2026 copy).
  The schematic symbol for the CM5 is generated from this file; do not hand-edit.
* `usb5744-pinout.csv` — Microchip USB5744 56-VQFN pin assignments, Table 3-1 of
  DS00001855M (public).
* `asm1153e-pinout.csv` — ASMedia ASM1153E QFN-48 pin list, section 6 of the
  Rev 0.4 datasheet. The PDF itself is vendor-confidential and is kept only in
  the gitignored `datasheets/` folder.
* `datasheets/` (gitignored) — local copies of the CM5, CM5IO, USB5744 and
  ASM1153E datasheets used for this design.
* `m2-mkey-pinout.csv` — M.2 Socket 3 / M-key host pin assignment (PCIe x4
  positions; only lane 0 is used). Signal names are from the host's point of
  view: PETp/n = host transmit, PERp/n = host receive. Pins 59–66 are the key
  notch. Source: pinoutguide.com M.2 table, cross-checked against the PCI-SIG
  M.2 naming; verify against the socket vendor's drawing before layout.

# Files to download by hand

Vendor sites block scripted downloads (Molex, TE, Amphenol, Richtek, LCSC and
Mouser all returned HTML or 403 to curl). Save each file into
`hardware/ref/datasheets/` with the name shown; that folder is gitignored, so
the PDFs stay local. Tell me when they are in place and I will build the
footprints from them.

## Needed now

| # | File | Save as | Where | Why |
|---|---|---|---|---|
| 1 | Molex 47018-4001 sales drawing **SD-47018-001** (SATA 22-pin right-angle SMT host receptacle) | `molex-47018-4001-sd.pdf` | https://www.molex.com/en-us/products/part-detail/470184001 → "Drawing (PDF)" / "Sales Drawing". Alternate: Digi-Key page https://www.digikey.com/en/products/detail/molex/0470184001/2440226 → Datasheet link | the four SATA bay footprints (decision C17); currently placeholders |
| 2 | TE 2199230-4 **Customer Drawing** (M.2 M-key socket, 4.2 mm) | `te-2199230-4-drawing.pdf` | https://www.te.com/en/product-2199230-4.html → Documents → "Customer Drawing". Alternate: Digi-Key https://www.digikey.com/en/products/detail/te-connectivity-amp-connectors/2199230-4/6119433 | verify the copied CM5IO M.2 footprint's peg/standoff holes against TE's drawing (decision C18) |

## Optional (nice to have)

| # | File | Save as | Where | Why |
|---|---|---|---|---|
| 3 | Richtek RT9742 datasheet | `rt9742.pdf` | https://www.richtek.com/Products/Power%20Management/Load%20Switch/RT9742 → Datasheet | the CM5IO uses it as the microSD power switch; I substituted a TPS22965 already on the BOM. Only needed if you prefer the exact reference part |
| 4 | VIA VL817-Q7 datasheet | `vl817.pdf` | https://www.lcsc.com/product-detail/C209756.html → Datasheet | not used any more (C11 chose USB5744); keep only if you want the alternate documented |
| 5 | 12 V / 10 A power brick datasheet, the exact one you will buy | `psu-12v-10a.pdf` | your supplier | its 4-pin DIN pin assignment sets how J21 is wired (C13); layout cannot start on the DIN pins without it |

## Already on disk (fetched by me, for reference)

`cm5-datasheet.pdf`, `cm5io-datasheet.pdf`, `usb5744-DS00001855M.pdf`,
`tps56637.pdf`, `tps22965.pdf`, `kpjx-4s-s.pdf`, `asm1153e.pdf` (Rev 0.4 mirror copy),
`amphenol-m2-farnell.pdf` (brochure only, no footprint), and the Raspberry Pi
CM5IO rev 2 KiCad project in `cm5io-kicad/`. I can also fetch the CM5 STEP model
from pip.raspberrypi.com myself when the enclosure work starts.

## Added 2026-09-23 for the bay-card architecture (D9 A)

| What | Part | Where | Why |
|---|---|---|---|
| PCI Express x1 card-edge socket, through-hole, customer drawing | Amphenol 10018783-10100TLF (or TE 1-1734774-1) | amphenol-cs.com / te.com product page, "Drawing" | the eight bay slots on the brain: pin rows, peg holes, housing outline. Footprint is generated from the PCI Express CEM spec meanwhile and checked against the drawing before ordering |
| 12 V brick, 150–180 W, with its DIN pinout | your choice | vendor page | eight spinning 3.5" drives draw about 9 A at 12 V |

## P-FET datasheets (pin tables, before ordering)

| Part | Where | Why |
|---|---|---|
| AO4407A (Q20, SO-8) | https://www.aosmd.com/res/datasheets/AO4407A.pdf | confirm S 1–3, G 4, D 5–8 (symbol `PMOS_SSSGDDDD`) |
| AON7403 (bay-card Q1, Q2, DFN 3x3-8), chosen 2026-09-23 | https://www.aosmd.com/res/datasheets/AON7403.pdf | confirm S 1–3, G 4, D 5–8 + EP and the DFN land pattern |

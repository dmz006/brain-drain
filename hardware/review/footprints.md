# Footprint provenance

| footprint | source | verification |
|---|---|---|
| PCIe_x1_Socket_THT | generated (`fpgen.py`) from the Amphenol FCI customer drawing 10018784 sheets 1, 3, 5 | hole pattern and pegs from the drawing; the housing ends (x -2.1 .. 22.9) are assumed symmetrical about the contacts, check against the 3D model |
| SATA_22pin_Receptacle_RA | generated (`fpgen.py`) from the Molex sales drawing SD-47018-001 sheets 1, 2 | pads, pegs and slots from the drawing; the mating face is assumed flush with the PCB edge; the two 0.5 mm key rectangles are not modelled; slot hole 1.0 x 2.15 mm read off the drawing |
| BUS_PCIexpress_x1 | KiCad stock library (Connector_PCBEdge), card-edge fingers with the tab outline | PCI-SIG CEM geometry; our pinout is custom |
| Raspberry-Pi-5-Compute-Module | copied unchanged from the Raspberry Pi CM5IO rev 2 KiCad project | Raspberry Pi design files |
| M2_Socket3_MKey_CM5IO | copied from the CM5IO project, renamed | peg and standoff holes still to be compared with the TE 2199230-4 customer drawing (STATUS R2) |
| Kycon_KPJX-4S-S | generated from the Kycon drawing A17 | pin positions from the drawing; DIN pin assignment must match the brick (STATUS R3) |
| Texas_RPA0010A_VQFN-HR-10_3x3mm | generated from the TPS56637 datasheet land pattern | datasheet example board layout |
| DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm, SOIC-8, SOT-23, TSOT-23-6, QFN-56 / QFN-48, WSON-8, passives, crystals, LEDs, headers | KiCad stock libraries | stock; check the QFN exposed-pad sizes against the ASM1153E and USB5744 datasheets |

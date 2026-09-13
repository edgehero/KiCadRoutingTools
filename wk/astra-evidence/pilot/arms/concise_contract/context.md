# Component context -- board.kicad_pcb

Board 31.75 x 14.5 mm, layers F.Cu, B.Cu, floors clearance 0.25mm / track 0.3mm.
Differential pairs: /D_P//D_N.

Every derived column names its source; `unknown` means the tool looked and could not tell, which is not the same as absent. See the SOURCES section at the end.

## Pin-order agreement

A CROSSED pair forces at least `inversions` crossings on ANY router: on a 2-layer board that is a via per net or back-side copper. Rotation cannot fix it -- parity flips only under a mirror.

| A | B | scope | nets | span mm | inversions | max planar | verdict |
|---|---|---|---|---|---|---|---|
| U1 | USB1 | pair /D_P//D_N | 2 | 9.139 | 1 | 1 | CROSSED |
| CON2 | U2 | interface | 3 | 5.621 | 2 | 2 | CROSSED |
| C3 | CON2 | interface | 2 | 8.512 | 1 | 1 | CROSSED |
| C3 | U1 | interface | 2 | 8.851 | 1 | 1 | CROSSED |
| CON2 | USB1 | interface | 2 | 21.796 | 1 | 1 | CROSSED |
| U1 | U2 | interface | 2 | 8.501 | 1 | 1 | CROSSED |
| U1 | USB1 | interface | 3 | 14.292 | 1 | 2 | CROSSED |
| C1 | CON2 | interface | 2 | 10.732 | 0 | 2 | AGREES |
| C1 | U2 | interface | 2 | 5.772 | 0 | 2 | AGREES |
| C1 | USB1 | interface | 2 | 23.193 | 0 | 2 | AGREES |
| C3 | CON1 | interface | 2 | 11.746 | 0 | 2 | AGREES |
| C3 | U2 | interface | 2 | 5.134 | 0 | 2 | AGREES |
| CON1 | CON2 | interface | 6 | 15.939 | 0 | 6 | AGREES |
| CON1 | U1 | interface | 2 | 18.664 | 0 | 2 | AGREES |
| CON1 | U2 | interface | 2 | 12.01 | 0 | 2 | AGREES |
| CON2 | U1 | interface | 2 | 12.052 | 0 | 2 | AGREES |
| U2 | USB1 | interface | 2 | 17.749 | 0 | 2 | AGREES |

`span mm` is the WORST straight-line pad-to-pad distance over the nets the two parts share -- the length this pair or bus is forced to run. Compare it against the shortest the two bodies allow side by side (their `body_mm` are below); a ratio much above 1.5 is a finding to explain. The threshold is a judgement, which is why the tool reports the measurement and not a verdict.

## Parts

### #00000000-0000-0000-0000-00005a3b5201  --  unknown  (looked)

`OLIMEX_LOGOs-FP:LOGO_RECYCLEBIN_1`  --  body no body geometry from **none**, 0 pad(s), side B, pose (115.25, 95.75, 90.0deg)  LOCKED

### #00000000-0000-0000-0000-00005d8c51dd  --  unknown  (looked)

`OLIMEX_LOGOs-FP:LOGO_PBFREE`  --  body no body geometry from **none**, 0 pad(s), side B, pose (119.2, 100.9, 0.0deg)  LOCKED

### #00000000-0000-0000-0000-00005e7dd057  --  unknown  (looked)

`OLIMEX_LOGOs-FP:OLIMEX_LOGO_TB`  --  body no body geometry from **none**, 0 pad(s), side B, pose (130.0, 99.0, 180.0deg)  LOCKED

### C1  --  capacitor  (ref_prefix)

`OLIMEX_RLC-FP:C_0603_5MIL_DWS`  value `2.2uF`  --  body 0.762 x 1.524 mm from **fab**, 2 pad(s), side F, pose (138.46, 96.23, 90.0deg)  LOCKED

- **east**: 1 Net-(C1-Pad1) -> CON2 U2 USB1
- **north**: 2 GND -> C2 C3 C4 CON1 CON2 U1 U2 USB1 Y1

- partners by shared nets: USB1 (2), U2 (2), CON2 (2), Y1 (1), U1 (1), CON1 (1), C4 (1), C3 (1)

### C2  --  capacitor  (ref_prefix)

`OLIMEX_RLC-FP:C_0402_5MIL_DWS`  value `27pF`  --  body 0.996 x 0.498 mm from **fab**, 2 pad(s), side F, pose (128.0, 99.5, 0.0deg)

Serves **U1** (0.0mm away).

- **north**: 1 Net-(C2-Pad1) -> U1 Y1 | 2 GND -> C1 C3 C4 CON1 CON2 U1 U2 USB1 Y1

- partners by shared nets: Y1 (2), U1 (2), USB1 (1), U2 (1), CON2 (1), CON1 (1), C4 (1), C3 (1)

### C3  --  capacitor  (ref_prefix)

`OLIMEX_RLC-FP:C_0603_5MIL_DWS`  value `2.2uF`  --  body 1.524 x 0.762 mm from **fab**, 2 pad(s), side F, pose (132.55, 100.22, 180.0deg)  LOCKED

Serves **U1** (1.125mm away).

- **north**: 1 /+3.3V -> CON1 CON2 U1 U2 | 2 GND -> C1 C2 C4 CON1 CON2 U1 U2 USB1 Y1

- partners by shared nets: U2 (2), U1 (2), CON2 (2), CON1 (2), Y1 (1), USB1 (1), C4 (1), C2 (1)

### C4  --  capacitor  (ref_prefix)

`OLIMEX_RLC-FP:C_0402_5MIL_DWS`  value `27pF`  --  body 0.996 x 0.498 mm from **fab**, 2 pad(s), side F, pose (128.0, 99.5, 0.0deg)

Serves **U1** (0.0mm away).

- **north**: 1 Net-(C4-Pad1) -> U1 Y1 | 2 GND -> C1 C2 C3 CON1 CON2 U1 U2 USB1 Y1

- partners by shared nets: Y1 (2), U1 (2), USB1 (1), U2 (1), CON2 (1), CON1 (1), C3 (1), C2 (1)

### CON1  --  unknown  (looked)

`OLIMEX_Connectors-FP:WU06SM`  value `CON6`  --  body 3.2 x 9.7 mm from **silk**, 6 pad(s), side F, pose (143.4, 100.0, -90.0deg)  LOCKED

Mating face **E**, 0.25mm from that edge

- **east**: 2 /DCOM -> CON2 Q1 | 3 /U0RXD -> CON2 R3 | 4 GND -> C1 C2 C3 C4 CON2 U1 U2 USB1 Y1 | 5 /+3.3V -> C3 CON2 U1 U2 | 6 /EN -> CON2 Q2
- **north**: 1 /U0TXD -> CON2 R4

- partners by shared nets: CON2 (6), U2 (2), U1 (2), C3 (2), Y1 (1), USB1 (1), R4 (1), R3 (1)

### CON2  --  pin header  (footprint)

`OLIMEX_Connectors-FP:HN1x7`  value `CON6`  --  body 17.78 x 2.54 mm from **silk**, 7 pad(s), side F, pose (136.17, 93.0, 180.0deg)  LOCKED

Mating face **E**, 0.69mm from that edge

- **north**: 1 /U0TXD -> CON1 R4 | 2 /DCOM -> CON1 Q1 | 3 /U0RXD -> CON1 R3 | 4 GND -> C1 C2 C3 C4 CON1 U1 U2 USB1 Y1 | 5 /+3.3V -> C3 CON1 U1 U2 | 6 /EN -> CON1 Q2 | 7 Net-(C1-Pad1) -> C1 U2 USB1

- partners by shared nets: CON1 (6), U2 (3), USB1 (2), U1 (2), C3 (2), C1 (2), Y1 (1), R4 (1)

### Q1  --  npn/pnp transistor  (footprint)

`OLIMEX_Transistors-FP:SOT23`  value `BC817-40(SOT23)`  --  body 3.61 x 2.902 mm from **pad_bbox**, 3 pad(s), side F, pose (139.0, 99.7, 180.0deg)  LOCKED

- **east**: 3 /DCOM -> CON1 CON2
- **north**: 1 Net-(Q1-Pad1) -> R1
- **south**: 2 /DTR -> R2 U1

- partners by shared nets: U1 (1), R2 (1), R1 (1), CON2 (1), CON1 (1)

### Q2  --  npn/pnp transistor  (footprint)

`OLIMEX_Transistors-FP:SOT23`  value `BC817-40(SOT23)`  --  body 3.61 x 2.902 mm from **pad_bbox**, 3 pad(s), side F, pose (139.0, 103.1, 180.0deg)  LOCKED

- **east**: 3 /EN -> CON1 CON2
- **north**: 1 Net-(Q2-Pad1) -> R2
- **south**: 2 /RTS -> R1 U1

- partners by shared nets: U1 (1), R2 (1), R1 (1), CON2 (1), CON1 (1)

### R1  --  resistor  (ref_prefix)

`OLIMEX_RLC-FP:R_0402_5MIL_DWS`  value `1K`  --  body 0.498 x 0.996 mm from **fab**, 2 pad(s), side F, pose (136.4, 98.8, -90.0deg)  LOCKED

- **east**: 2 /RTS -> Q2 U1
- **north**: 1 Net-(Q1-Pad1) -> Q1

- partners by shared nets: U1 (1), Q2 (1), Q1 (1)

### R2  --  resistor  (ref_prefix)

`OLIMEX_RLC-FP:R_0402_5MIL_DWS`  value `1K`  --  body 0.498 x 0.996 mm from **fab**, 2 pad(s), side F, pose (136.4, 101.6, 90.0deg)  LOCKED

- **east**: 1 Net-(Q2-Pad1) -> Q2
- **north**: 2 /DTR -> Q1 U1

- partners by shared nets: U1 (1), Q2 (1), Q1 (1)

### R3  --  resistor  (ref_prefix)

`OLIMEX_RLC-FP:R_0402_5MIL_DWS`  value `100R`  --  body 0.996 x 0.498 mm from **fab**, 2 pad(s), side F, pose (141.0, 101.5, 180.0deg)  LOCKED

- **north**: 1 /U0RXD -> CON1 CON2 | 2 Net-(R3-Pad2) -> U1

- partners by shared nets: U1 (1), CON2 (1), CON1 (1)

### R4  --  resistor  (ref_prefix)

`OLIMEX_RLC-FP:R_0402_5MIL_DWS`  value `100R`  --  body 0.996 x 0.498 mm from **fab**, 2 pad(s), side F, pose (141.0, 98.1, 180.0deg)  LOCKED

- **north**: 1 /U0TXD -> CON1 CON2 | 2 Net-(R4-Pad2) -> U1

- partners by shared nets: U1 (1), CON2 (1), CON1 (1)

### Ref*  --  fiducial  (part_class)

`OLIMEX_Other-FP:Fiducial1x3_transp`  value `Val**`  --  body 1.0 x 1.0 mm from **pad_bbox**, 1 pad(s), side F, pose (141.2, 95.9, 0.0deg)  LOCKED

- **north**: Fid1 -

### Ref*~2  --  fiducial  (part_class)

`OLIMEX_Other-FP:Fiducial1x3_transp`  value `Val**`  --  body 1.0 x 1.0 mm from **pad_bbox**, 1 pad(s), side F, pose (118.1, 99.9, 0.0deg)  LOCKED

- **north**: Fid1 -

### U1  --  integrated circuit  (ref_prefix)

`OLIMEX_IC-FP:SSOP-20W`  value `CH340H/T`  --  body 7.62 x 8.509 mm from **silk**, 20 pad(s), side F, pose (128.0, 99.5, 0.0deg)

- **east**: 10 Net-(C2-Pad1) -> C2 Y1
- **north**: 11 Net-(U1-Pad11) | 12 Net-(U1-Pad12) | 13 Net-(U1-Pad13) | 14 Net-(U1-Pad14) | 15 /DTR -> Q1 R2 | 16 /RTS -> Q2 R1 | 17 - | 18 Net-(U1-Pad18) | 19 /+3.3V -> C3 CON1 CON2 U2 | 20 Net-(U1-Pad20)
- **south**: 1 - | 2 - | 3 Net-(R3-Pad2) -> R3 | 4 Net-(R4-Pad2) -> R4 | 5 /+3.3V -> C3 CON1 CON2 U2 | 6 /D_P -> USB1 | 7 /D_N -> USB1 | 8 GND -> C1 C2 C3 C4 CON1 CON2 U2 USB1 Y1 | 9 Net-(C4-Pad1) -> C4 Y1

- partners by shared nets: Y1 (3), USB1 (3), U2 (2), CON2 (2), CON1 (2), C4 (2), C3 (2), C2 (2)

### U2  --  regulator  (footprint)

`OLIMEX_Transistors-FP:SOT89`  value `ME6210-SOT89`  --  body 5.2 x 5.2 mm from **silk**, 3 pad(s), side F, pose (134.34, 96.69, -90.0deg)  LOCKED

- **east**: 2 Net-(C1-Pad1) -> C1 CON2 USB1
- **north**: 1 GND -> C1 C2 C3 C4 CON1 CON2 U1 USB1 Y1
- **south**: 3 /+3.3V -> C3 CON1 CON2 U1

- partners by shared nets: CON2 (3), USB1 (2), U1 (2), CON1 (2), C3 (2), C1 (2), Y1 (1), C4 (1)

### USB1  --  edge receptacle  (part_class)

`OLIMEX_Connectors-FP:USB-MICRO_MISB-SWMM-5B_LF`  value `USB-uicro-B`  --  body 7.12 x 7.4 mm from **fab**, 13 pad(s), side F, pose (117.5, 100.0, 180.0deg)  LOCKED

Mating face **W**, 0.0mm from that edge

- **east**: 0 GND -> C1 C2 C3 C4 CON1 CON2 U1 U2 Y1 | 1 Net-(C1-Pad1) -> C1 CON2 U2 | 2 /D_N -> U1 | 3 /D_P -> U1 | 4 Net-(USB1-Pad4) | 5 GND -> C1 C2 C3 C4 CON1 CON2 U1 U2 Y1
- **interior**:  - |  -
- **north**: 0 GND -> C1 C2 C3 C4 CON1 CON2 U1 U2 Y1 | 0 GND -> C1 C2 C3 C4 CON1 CON2 U1 U2 Y1
- **south**: 0 GND -> C1 C2 C3 C4 CON1 CON2 U1 U2 Y1
- **west**: 0 GND -> C1 C2 C3 C4 CON1 CON2 U1 U2 Y1 | 0 GND -> C1 C2 C3 C4 CON1 CON2 U1 U2 Y1

- partners by shared nets: U1 (3), U2 (2), CON2 (2), C1 (2), Y1 (1), CON1 (1), C4 (1), C3 (1)

### Y1  --  crystal  (footprint)

`OLIMEX_Crystal-FP:TSX-3.2x2.5mm_GND(3)`  value `Q12MHz/20pF/10ppm/4P/3.2x2.5mm`  --  body 3.2 x 2.5 mm from **fab**, 4 pad(s), side F, pose (128.0, 99.5, 0.0deg)

- **east**: 3 GND -> C1 C2 C3 C4 CON1 CON2 U1 U2 USB1
- **north**: 2 Net-(C2-Pad1) -> C2 U1 | 3 GND -> C1 C2 C3 C4 CON1 CON2 U1 U2 USB1
- **south**: 1 Net-(C4-Pad1) -> C4 U1

- partners by shared nets: U1 (3), C4 (2), C2 (2), USB1 (1), U2 (1), CON2 (1), CON1 (1), C3 (1)

## Sources

- **body_mm / body_source** -- placement.body.board_bodies (#896)
- **diff_pairs** -- list_nets.find_differential_pairs (rejects 2-terminal resonators)
- **mating** -- which parts count as connectors: render_placement.connector_edge_facts. Where the edge is: measured from the placement.body occupancy rect, because that function reads the quench pad-box ladder and would put two geometries on one sheet
- **pads_by_face** -- placement.escape.assign_faces (#850)
- **part_class** -- placement.part_class.classify_part
- **pin_order** -- placement.pair_order.pair_metrics
- **role** -- inferred here from footprint / prefix / value; the board carries no datasheet or 3D-model field to cite
- **serves** -- placement.groups tether election (DECAP_MIN_IC_PADS = 4, so a 3-pad regulator can never be a target -- see #902)


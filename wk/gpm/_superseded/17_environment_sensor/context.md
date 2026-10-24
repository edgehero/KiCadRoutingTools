# Component context -- fixed.kicad_pcb

Board 50.0 x 26.5 mm, layers F.Cu, In1.Cu, In2.Cu, B.Cu, floors clearance 0.15mm / track 0.15mm.

**This board is a PILE** (footprints span 10.0% of the board diagonal; 100% of footprints lie outside the board outline): its poses are staging, not decisions. Every claim read off a pose -- a pin-order verdict, a leg distance, a mating edge, a nearest-cap election -- is WITHHELD unless every part it reads is KiCad-locked (none is). A part's printed `pose` is where the file has it. Withheld: emc_roles legs 8, parts[].mating 3, parts[].serves 20, pin_order.rows 306.

Copper pours: +3V3 on In2.Cu (unfilled, 72% of the board); GND on B.Cu/F.Cu/In1.Cu (unfilled, 93% of the board).
Differential pairs: /USB_D_P//USB_D_N.

Every derived column names its source; `unknown` means the tool looked and could not tell, which is not the same as absent. See the SOURCES section at the end.

## Pin-order agreement

306 pin-order row(s) WITHHELD: the board is a pile, and a verdict measured at staging poses is not a claim. Place the parts, then read this section.


## EMC roles (report only)

REPORT ONLY: no intent key is written. Each row is in the shape `proximity[]` reads (`ref`, `near`, `pads`) with `max_mm` left null: the limit is the author's, from the datasheet, and copying the measured gap into it would bless the current pose (#902). Legs are reported, never a loop area, which a self-crossing pad polygon can shrink while every leg grows (#1254).

Legs: pad edge to pad edge: placement.legality.pad_rect + rect_gap, signed (negative = the pad boxes overlap) -- what rule_proximity measures for a declared row: each subject pad against the nearest partner pad on its own net.

### Y1  --  crystal  value `Resonator_32.768kHz_ECX-31B`

- Y1 is in the role table's crystal row: footprint name contains 'resonator'
- U3 pad 3 is PC14-OSC32_IN
- U3 pad 4 is PC15-OSC32_OUT

| leg | from | to | net | gap mm | sides |
|---|---|---|---|---|---|
| crystal -> load pin | Y1.1 | U3.3 (PC14-OSC32_IN) | /OSC32_IN | - | F / F |
| crystal -> load pin | Y1.2 | U3.4 (PC15-OSC32_OUT) | /OSC32_OUT | - | F / F |

- row, worst leg withheld (staging poses): `{"max_mm": null, "near": "U3", "pads": {"U3": ["3", "4"], "Y1": ["1", "2"]}, "ref": "Y1"}`

### Y2  --  crystal  value `Resonator_8MHz_ABM3B`

- Y2 is in the role table's crystal row: footprint name contains 'resonator'
- U3 pad 6 is PF1-OSC_OUT
- U3 pad 5 is PF0-OSC_IN

| leg | from | to | net | gap mm | sides |
|---|---|---|---|---|---|
| crystal -> load pin | Y2.1 | U3.6 (PF1-OSC_OUT) | Net-(U3-PF1-OSC_OUT) | - | F / F |
| crystal -> load pin | Y2.3 | U3.5 (PF0-OSC_IN) | Net-(U3-PF0-OSC_IN) | - | F / F |

- row, worst leg withheld (staging poses): `{"max_mm": null, "near": "U3", "pads": {"U3": ["5", "6"], "Y2": ["1", "3"]}, "ref": "Y2"}`

### D1  --  esd diode  value `ESD9X5.0ST5G`

- D1 is a two-terminal diode (reference prefix 'D' (convention only); value 'ESD9X5.0ST5G') from /VBUS to GND
- J1 is the one connector carrying /VBUS

| leg | from | to | net | gap mm | sides |
|---|---|---|---|---|---|
| ESD line -> connector | D1.2 | J1.A9 (VBUS) | /VBUS | - | F / F |

- row, worst leg withheld (staging poses): `{"max_mm": null, "near": "J1", "pads": {"D1": ["2"], "J1": ["A4", "A9", "B4", "B9"]}, "ref": "D1"}`

### D2  --  esd diode  value `ESD9X5.0ST5G`

- D2 is a two-terminal diode (reference prefix 'D' (convention only); value 'ESD9X5.0ST5G') from /VBUS to GND
- J1 is the one connector carrying /VBUS

| leg | from | to | net | gap mm | sides |
|---|---|---|---|---|---|
| ESD line -> connector | D2.2 | J1.A4 (VBUS) | /VBUS | - | F / F |

- row, worst leg withheld (staging poses): `{"max_mm": null, "near": "J1", "pads": {"D2": ["2"], "J1": ["A4", "A9", "B4", "B9"]}, "ref": "D2"}`

### D3  --  esd diode  value `ESD9X5.0ST5G`

- D3 is a two-terminal diode (reference prefix 'D' (convention only); value 'ESD9X5.0ST5G') from /USB_CC1 to GND
- J1 is the one connector carrying /USB_CC1

| leg | from | to | net | gap mm | sides |
|---|---|---|---|---|---|
| ESD line -> connector | D3.2 | J1.A5 (CC_{1}) | /USB_CC1 | - | F / F |

- row, worst leg withheld (staging poses): `{"max_mm": null, "near": "J1", "pads": {"D3": ["2"], "J1": ["A5"]}, "ref": "D3"}`

### D4  --  esd diode  value `ESD9X5.0ST5G`

- D4 is a two-terminal diode (reference prefix 'D' (convention only); value 'ESD9X5.0ST5G') from /USB_CC2 to GND
- J1 is the one connector carrying /USB_CC2

| leg | from | to | net | gap mm | sides |
|---|---|---|---|---|---|
| ESD line -> connector | D4.2 | J1.B5 (CC_{2}) | /USB_CC2 | - | F / F |

- row, worst leg withheld (staging poses): `{"max_mm": null, "near": "J1", "pads": {"D4": ["2"], "J1": ["B5"]}, "ref": "D4"}`

## Parts

### BAT1  --  unknown  (looked)

`antmicro-footprints:BAT_BAT-HLD-012-SMT-TR`  value `BAT-HLD-012-SMT-TR`  --  body 18.338 x 11.097 mm from **courtyard**, 3 pad(s), side B, pose (182.999, 147.1, 0.0deg)

- **east**: P2 Net-(U3-VBAT) -> U3
- **north**: N GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2
- **west**: P1 Net-(U3-VBAT) -> U3

- partners by shared nets: U3 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U2 (1), U1 (1), TP10 (1)

### C1  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_4u7_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.444, 147.1, 0.0deg)

- **north**: 1 GND -> BAT1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +5V -> C3 C7 C8 FB2 LD1 R2 U1 U2

- partners by shared nets: U2 (2), U1 (2), C8 (2), C7 (2), C3 (2), Y2 (1), U6 (1), U5 (1)

### C10  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_4u7_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.888, 147.1, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 -> C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C11  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_2u2_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.333, 147.1, 0.0deg)

- **north**: 1 +3V3 -> C10 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6 | 2 GND -> BAT1 C1 C10 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C12  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.778, 147.1, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 -> C10 C11 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C13  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.222, 147.1, 0.0deg)

- **north**: 1 +3V3 -> C10 C11 C12 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6 | 2 GND -> BAT1 C1 C10 C11 C12 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C14  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_16p_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.667, 147.1, 0.0deg)

- **north**: 1 /OSC32_IN -> R18 U3 Y1 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U3 (2), Y2 (1), Y1 (1), U6 (1), U5 (1), U4 (1), U2 (1), U1 (1)

### C15  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.112, 147.1, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 -> C10 C11 C12 C13 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C16  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_16p_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.556, 147.1, 0.0deg)

- **north**: 1 /OSC32_OUT -> R18 U3 Y1 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U3 (2), Y2 (1), Y1 (1), U6 (1), U5 (1), U4 (1), U2 (1), U1 (1)

### C17  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (187.001, 147.1, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 -> C10 C11 C12 C13 C15 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C18  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (182.999, 147.5, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C19  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.444, 147.5, 0.0deg)

- **north**: 1 Net-(U3-VDDA) -> C20 FB3 U3 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U3 (2), C20 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U2 (1), U1 (1)

### C2  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.888, 147.5, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 GNDREF -> FB1 J1 R1

- partners by shared nets: R1 (2), J1 (2), FB1 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1)

### C20  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_2u2_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.333, 147.5, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(U3-VDDA) -> C19 FB3 U3

- partners by shared nets: U3 (2), C19 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U2 (1), U1 (1)

### C21  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_10p_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.778, 147.5, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(U3-PF1-OSC_OUT) -> R25 U3 Y2

- partners by shared nets: Y2 (2), U3 (2), U6 (1), U5 (1), U4 (1), U2 (1), U1 (1), TP10 (1)

### C22  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.222, 147.5, 0.0deg)

- **north**: 1 Net-(U3-VREF+) -> C24 U3 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U3 (2), C24 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U2 (1), U1 (1)

### C23  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_10p_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.667, 147.5, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(U3-PF0-OSC_IN) -> R25 U3 Y2

- partners by shared nets: Y2 (2), U3 (2), U6 (1), U5 (1), U4 (1), U2 (1), U1 (1), TP10 (1)

### C24  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_2u2_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.112, 147.5, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(U3-VREF+) -> C22 U3

- partners by shared nets: U3 (2), C22 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U2 (1), U1 (1)

### C25  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.556, 147.5, 0.0deg)

- **north**: 1 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C26  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (187.001, 147.5, 0.0deg)

- **north**: 1 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C27  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (182.999, 147.9, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C28  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.444, 147.9, 0.0deg)

- **north**: 1 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### C3  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.888, 147.9, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +5V -> C1 C7 C8 FB2 LD1 R2 U1 U2

- partners by shared nets: U2 (2), U1 (2), C8 (2), C7 (2), C1 (2), Y2 (1), U6 (1), U5 (1)

### C4  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_2u2_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.333, 147.9, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 /VBUS -> D1 D2 FB2 J1

- partners by shared nets: J1 (2), D2 (2), D1 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1)

### C5  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.778, 147.9, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(U1-3V3OUT) -> C6 U1

- partners by shared nets: U1 (2), C6 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1), U2 (1)

### C6  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.222, 147.9, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(U1-3V3OUT) -> C5 U1

- partners by shared nets: U1 (2), C5 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1), U2 (1)

### C7  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_2u2_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.667, 147.9, 0.0deg)

- **north**: 1 +5V -> C1 C3 C8 FB2 LD1 R2 U1 U2 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U2 (2), U1 (2), C8 (2), C3 (2), C1 (2), Y2 (1), U6 (1), U5 (1)

### C8  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_100n_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.112, 147.9, 0.0deg)

- **north**: 1 +5V -> C1 C3 C7 FB2 LD1 R2 U1 U2 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: U2 (2), U1 (2), C7 (2), C3 (2), C1 (2), Y2 (1), U6 (1), U5 (1)

### C9  --  capacitor  (ref_prefix)

`antmicro-footprints:C_0402_1005Metric`  value `C_4u7_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.556, 147.9, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### D1  --  diode  (ref_prefix)

`antmicro-footprints:SOD-923`  value `ESD9X5.0ST5G`  --  body 1.36 x 0.82 mm from **courtyard**, 2 pad(s), side F, pose (187.001, 147.9, 0.0deg)

- **north**: 1 GND (C) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 /VBUS (A) -> C4 D2 FB2 J1

- partners by shared nets: J1 (2), D2 (2), C4 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1)

### D2  --  diode  (ref_prefix)

`antmicro-footprints:SOD-923`  value `ESD9X5.0ST5G`  --  body 1.36 x 0.82 mm from **courtyard**, 2 pad(s), side F, pose (182.999, 148.3, 0.0deg)

- **north**: 1 GND (C) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 /VBUS (A) -> C4 D1 FB2 J1

- partners by shared nets: J1 (2), D1 (2), C4 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1)

### D3  --  diode  (ref_prefix)

`antmicro-footprints:SOD-923`  value `ESD9X5.0ST5G`  --  body 1.36 x 0.82 mm from **courtyard**, 2 pad(s), side F, pose (183.444, 148.3, 0.0deg)

- **north**: 1 GND (C) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 /USB_CC1 (A) -> J1 R3

- partners by shared nets: R3 (2), J1 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1), U2 (1)

### D4  --  diode  (ref_prefix)

`antmicro-footprints:SOD-923`  value `ESD9X5.0ST5G`  --  body 1.36 x 0.82 mm from **courtyard**, 2 pad(s), side F, pose (183.888, 148.3, 0.0deg)

- **north**: 1 GND (C) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 /USB_CC2 (A) -> J1 R4

- partners by shared nets: R4 (2), J1 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1), U2 (1)

### D5  --  diode  (ref_prefix)

`antmicro-footprints:SOT-723`  value `TPD2E009_SOT-9X3`  --  body 1.66 x 1.66 mm from **courtyard**, 3 pad(s), side F, pose (184.333, 148.3, 0.0deg)

- **east**: 3 GND (3) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2
- **north**: 1 /USB_D_P (1) -> J1 U1
- **south**: 2 /USB_D_N (2) -> J1 U1

- partners by shared nets: U1 (3), J1 (3), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1), U2 (1)

### D6  --  diode  (ref_prefix)

`antmicro-footprints:SOT-723`  value `TPD2E009_SOT-9X3`  --  body 1.66 x 1.66 mm from **courtyard**, 3 pad(s), side F, pose (184.778, 148.3, 0.0deg)

- **east**: 3 GND (3) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2
- **north**: 1 I2C_1_SCL (1) -> D8 J2 J3 R22 R23 R27 R37 TP12 U4 U5 U6
- **south**: 2 I2C_1_SDA (2) -> D8 J2 J3 R21 R28 R38 TP11 U4 U5 U6

- partners by shared nets: U6 (3), U5 (3), U4 (3), J3 (3), J2 (3), D8 (3), Y2 (1), U3 (1)

### D7  --  diode  (ref_prefix)

`antmicro-footprints:SOD-923`  value `ESD9X5.0ST5G`  --  body 1.36 x 0.82 mm from **courtyard**, 2 pad(s), side F, pose (185.222, 148.3, 0.0deg)

- **north**: 1 GND (C) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 (A) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D9 (2)

### D8  --  diode  (ref_prefix)

`antmicro-footprints:SOT-723`  value `TPD2E009_SOT-9X3`  --  body 1.66 x 1.66 mm from **courtyard**, 3 pad(s), side F, pose (185.667, 148.3, 0.0deg)

- **east**: 3 GND (3) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2
- **north**: 1 I2C_1_SCL (1) -> D6 J2 J3 R22 R23 R27 R37 TP12 U4 U5 U6
- **south**: 2 I2C_1_SDA (2) -> D6 J2 J3 R21 R28 R38 TP11 U4 U5 U6

- partners by shared nets: U6 (3), U5 (3), U4 (3), J3 (3), J2 (3), D6 (3), Y2 (1), U3 (1)

### D9  --  diode  (ref_prefix)

`antmicro-footprints:SOD-923`  value `ESD9X5.0ST5G`  --  body 1.36 x 0.82 mm from **courtyard**, 2 pad(s), side F, pose (186.112, 148.3, 0.0deg)

- **north**: 1 GND (C) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 (A) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U2 (2), J3 (2), J2 (2), D7 (2)

### FB1  --  ferrite bead  (ref_prefix)

`antmicro-footprints:FB_0603_1608Metric`  value `FB_120Z_2A_Murata-BLM18PG_0603`  --  body 2.5 x 1.3 mm from **courtyard**, 2 pad(s), side F, pose (186.556, 148.3, 0.0deg)

- **north**: 1 GNDREF -> C2 J1 R1 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: R1 (2), J1 (2), C2 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1)

### FB2  --  ferrite bead  (ref_prefix)

`antmicro-footprints:FB_0603_1608Metric`  value `FB_120Z_2A_Murata-BLM18PG_0603`  --  body 2.5 x 1.3 mm from **courtyard**, 2 pad(s), side F, pose (187.001, 148.3, 0.0deg)

- **north**: 1 /VBUS -> C4 D1 D2 J1 | 2 +5V -> C1 C3 C7 C8 LD1 R2 U1 U2

- partners by shared nets: U2 (1), U1 (1), R2 (1), LD1 (1), J1 (1), D2 (1), D1 (1), C8 (1)

### FB3  --  ferrite bead  (ref_prefix)

`antmicro-footprints:FB_0603_1608Metric`  value `FB_120Z_2A_Murata-BLM18PG_0603`  --  body 2.5 x 1.3 mm from **courtyard**, 2 pad(s), side F, pose (182.999, 148.701, 0.0deg)

- **north**: 1 Net-(U3-VDDA) -> C19 C20 U3 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U3 (2), U6 (1), U5 (1), U4 (1), U2 (1), TP9 (1), R38 (1), R37 (1)

### J1  --  edge receptacle  (part_class)

`antmicro-footprints:USB-C_Receptacle_GCT_USB4105-GF-A`  value `USB-C_GCT_USB4105-GF-A`  --  body 10.2 x 8.3 mm from **courtyard**, 22 pad(s), side F, pose (183.444, 148.701, 0.0deg)

- **east**: SH GNDREF (SH) -> C2 FB1 R1
- **interior**:  - |  -
- **north**: A1 GND (GND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | A4 /VBUS (VBUS) -> C4 D1 D2 FB2 | A5 /USB_CC1 (CC_{1}) -> D3 R3 | A6 /USB_D_P (D_{A}+) -> D5 U1 | A7 /USB_D_N (D_{A}-) -> D5 U1 | A8 unconnected-(J1-SBU_{1}-PadA8) (SBU_{1}) | A9 /VBUS (VBUS) -> C4 D1 D2 FB2 | A12 GND (GND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | B1 GND (GND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | B4 /VBUS (VBUS) -> C4 D1 D2 FB2 | B5 /USB_CC2 (CC_{2}) -> D4 R4 | B6 /USB_D_P (D_{B}+) -> D5 U1 | B7 /USB_D_N (D_{B}-) -> D5 U1 | B8 unconnected-(J1-SBU_{2}-PadB8) (SBU_{2}) | B9 /VBUS (VBUS) -> C4 D1 D2 FB2 | B12 GND (GND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2
- **south**: SH GNDREF (SH) -> C2 FB1 R1 | SH GNDREF (SH) -> C2 FB1 R1
- **west**: SH GNDREF (SH) -> C2 FB1 R1

- partners by shared nets: U1 (3), D5 (3), R4 (2), R3 (2), R1 (2), FB1 (2), D4 (2), D3 (2)

### J2  --  connector  (ref_prefix)

`antmicro-footprints:Conn_JST_SH_1x4_SM04B-SRSS-TB-LF-SN`  value `JST_SH_1x4_SM04B-SRSS-TB-LF-SN`  --  body 7.3 x 6.04 mm from **courtyard**, 6 pad(s), side F, pose (183.888, 148.701, 0.0deg)

- **east**: MP unconnected-(J2-PadMP)
- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6 | 3 I2C_1_SDA -> D6 D8 J3 R21 R28 R38 TP11 U4 U5 U6 | 4 I2C_1_SCL -> D6 D8 J3 R22 R23 R27 R37 TP12 U4 U5 U6
- **south**: MP unconnected-(J2-PadMP)

- partners by shared nets: U6 (4), U5 (4), U4 (4), J3 (4), D8 (3), D6 (3), U3 (2), U2 (2)

### J3  --  connector  (ref_prefix)

`antmicro-footprints:Conn_JST_SH_1x4_SM04B-SRSS-TB-LF-SN`  value `JST_SH_1x4_SM04B-SRSS-TB-LF-SN`  --  body 7.3 x 6.04 mm from **courtyard**, 6 pad(s), side B, pose (184.333, 148.701, 0.0deg)

- **north**: MP unconnected-(J3-PadMP) | MP unconnected-(J3-PadMP)
- **south**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6 | 3 I2C_1_SDA -> D6 D8 J2 R21 R28 R38 TP11 U4 U5 U6 | 4 I2C_1_SCL -> D6 D8 J2 R22 R23 R27 R37 TP12 U4 U5 U6

- partners by shared nets: U6 (4), U5 (4), U4 (4), J2 (4), D8 (3), D6 (3), U3 (2), U2 (2)

### LD1  --  unknown  (looked)

`antmicro-footprints:LED_0603_1608Metric_G`  value `LED_G_0603_KP-1608ZGC`  --  body 2.5 x 1.3 mm from **courtyard**, 2 pad(s), side F, pose (184.778, 148.701, 0.0deg)

- **north**: 1 +5V (C) -> C1 C3 C7 C8 FB2 R2 U1 U2 | 2 Net-(LD1-A) (A) -> R12

- partners by shared nets: U2 (1), U1 (1), R2 (1), R12 (1), FB2 (1), C8 (1), C7 (1), C3 (1)

### LD2  --  unknown  (looked)

`antmicro-footprints:LED_0603_1608Metric_G`  value `LED_G_0603_KP-1608ZGC`  --  body 2.5 x 1.3 mm from **courtyard**, 2 pad(s), side F, pose (185.222, 148.701, 0.0deg)

- **north**: 1 /LD2 (C) -> U3 | 2 Net-(LD2-A) (A) -> R17

- partners by shared nets: U3 (1), R17 (1)

### MP1  --  unknown  (looked)

`antmicro-footprints:MP_Pad5.4mm_Drill2.7mm`  value `MP_Pad5.4mm_Drill2.7mm`  --  body 5.4 x 5.4 mm from **pad_bbox**, 1 pad(s), side F, pose (185.667, 148.701, 0.0deg)

- **north**: 1 unconnected-(MP1-Pad1)

### MP2  --  unknown  (looked)

`antmicro-footprints:MP_Pad5.4mm_Drill2.7mm`  value `MP_Pad5.4mm_Drill2.7mm`  --  body 5.4 x 5.4 mm from **pad_bbox**, 1 pad(s), side F, pose (186.112, 148.701, 0.0deg)

- **north**: 1 unconnected-(MP2-Pad1)

### MP3  --  unknown  (looked)

`antmicro-footprints:MP_Pad5.4mm_Drill2.7mm`  value `MP_Pad5.4mm_Drill2.7mm`  --  body 5.4 x 5.4 mm from **pad_bbox**, 1 pad(s), side F, pose (186.556, 148.701, 0.0deg)

- **north**: 1 unconnected-(MP3-Pad1)

### R1  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_1M_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (187.001, 148.701, 0.0deg)  DNP

- **north**: 1 GNDREF -> C2 FB1 J1 | 2 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: J1 (2), FB1 (2), C2 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1)

### R10  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (182.999, 149.101, 0.0deg)

- **north**: 1 Net-(U1-RI#) -> U1 | 2 JTDI -> R20 TP6

- partners by shared nets: U1 (1), TP6 (1), R20 (1)

### R11  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.444, 149.101, 0.0deg)  DNP

- **north**: 1 Net-(U1-CBUS0) -> U1 | 2 /FTDI_USER_PB -> U3

- partners by shared nets: U3 (1), U1 (1)

### R12  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_470R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.888, 149.101, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(LD1-A) -> LD1

- partners by shared nets: Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1), U2 (1), U1 (1), TP10 (1)

### R13  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.333, 149.101, 0.0deg)

- **north**: 1 Net-(U1-TXD) -> R15 U1 | 2 LPUART_1_STM_RX -> R16 U3

- partners by shared nets: U3 (1), U1 (1), R16 (1), R15 (1)

### R14  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.778, 149.101, 0.0deg)

- **north**: 1 Net-(U1-RXD) -> R16 U1 | 2 LPUART_1_STM_TX -> R15 U3

- partners by shared nets: U3 (1), U1 (1), R16 (1), R15 (1)

### R15  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.222, 149.101, 0.0deg)  DNP

- **north**: 1 Net-(U1-TXD) -> R13 U1 | 2 LPUART_1_STM_TX -> R14 U3

- partners by shared nets: U3 (1), U1 (1), R14 (1), R13 (1)

### R16  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.667, 149.101, 0.0deg)  DNP

- **north**: 1 Net-(U1-RXD) -> R14 U1 | 2 LPUART_1_STM_RX -> R13 U3

- partners by shared nets: U3 (1), U1 (1), R14 (1), R13 (1)

### R17  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_470R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.112, 149.101, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(LD2-A) -> LD2

- partners by shared nets: Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1), U2 (1), U1 (1), TP10 (1)

### R18  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_1M_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.556, 149.101, 0.0deg)  DNP

- **north**: 1 /OSC32_IN -> C14 U3 Y1 | 2 /OSC32_OUT -> C16 U3 Y1

- partners by shared nets: Y1 (2), U3 (2), C16 (1), C14 (1)

### R19  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (187.001, 149.101, 0.0deg)

- **north**: 1 NRST -> R8 TP1 U3 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U3 (2), U6 (1), U5 (1), U4 (1), U2 (1), TP9 (1), TP1 (1), R8 (1)

### R2  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_1k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (182.999, 149.501, 0.0deg)

- **north**: 1 +5V -> C1 C3 C7 C8 FB2 LD1 U1 U2 | 2 Net-(U1-RESET#) -> U1

- partners by shared nets: U1 (2), U2 (1), LD1 (1), FB2 (1), C8 (1), C7 (1), C3 (1), C1 (1)

### R20  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.444, 149.501, 0.0deg)

- **north**: 1 JTDI -> R10 TP6 | 2 Net-(U3-PA15) -> R23 U3

- partners by shared nets: U3 (1), TP6 (1), R23 (1), R10 (1)

### R21  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.888, 149.501, 0.0deg)  DNP

- **north**: 1 Net-(U3-PA8) -> U3 | 2 I2C_1_SDA -> D6 D8 J2 J3 R28 R38 TP11 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), U3 (1), TP11 (1), R38 (1), R28 (1), J3 (1)

### R22  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.333, 149.501, 0.0deg)  DNP

- **north**: 1 Net-(U3-PA9) -> U3 | 2 I2C_1_SCL -> D6 D8 J2 J3 R23 R27 R37 TP12 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), U3 (1), TP12 (1), R37 (1), R27 (1), R23 (1)

### R23  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.778, 149.501, 0.0deg)  DNP

- **north**: 1 Net-(U3-PA15) -> R20 U3 | 2 I2C_1_SCL -> D6 D8 J2 J3 R22 R27 R37 TP12 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), U3 (1), TP12 (1), R37 (1), R27 (1), R22 (1)

### R24  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.222, 149.501, 0.0deg)

- **north**: 1 JTRST -> R7 TP2 U3 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U3 (2), U6 (1), U5 (1), U4 (1), U2 (1), TP9 (1), TP2 (1), R7 (1)

### R25  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_1M_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.667, 149.501, 0.0deg)  DNP

- **north**: 1 Net-(U3-PF1-OSC_OUT) -> C21 U3 Y2 | 2 Net-(U3-PF0-OSC_IN) -> C23 U3 Y2

- partners by shared nets: Y2 (2), U3 (2), C23 (1), C21 (1)

### R26  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_1k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.112, 149.501, 0.0deg)

- **north**: 1 /FRAM_WP -> TP7 U3 U4 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U4 (2), U3 (2), U6 (1), U5 (1), U2 (1), TP9 (1), TP7 (1), R38 (1)

### R27  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.556, 149.501, 0.0deg)

- **north**: 1 Net-(U3-PB8-BOOT0) -> R29 R30 TP8 U3 | 2 I2C_1_SCL -> D6 D8 J2 J3 R22 R23 R37 TP12 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), U3 (1), TP8 (1), TP12 (1), R37 (1), R30 (1)

### R28  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (187.001, 149.501, 0.0deg)

- **north**: 1 Net-(U3-PB9) -> U3 | 2 I2C_1_SDA -> D6 D8 J2 J3 R21 R38 TP11 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), U3 (1), TP11 (1), R38 (1), R21 (1), J3 (1)

### R29  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (182.999, 149.901, 0.0deg)

- **north**: 1 Net-(U3-PB8-BOOT0) -> R27 R30 TP8 U3 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U3 (2), U6 (1), U5 (1), U4 (1), U2 (1), TP9 (1), TP8 (1), R38 (1)

### R3  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_5k1_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.444, 149.901, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 /USB_CC1 -> D3 J1

- partners by shared nets: J1 (2), D3 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1), U2 (1)

### R30  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.888, 149.901, 0.0deg)  DNP

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(U3-PB8-BOOT0) -> R27 R29 TP8 U3

- partners by shared nets: U3 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U2 (1), U1 (1), TP8 (1)

### R31  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.333, 149.901, 0.0deg)  DNP

- **north**: 1 Net-(U4-A1) -> R32 U4 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R33 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U4 (2), U6 (1), U5 (1), U3 (1), U2 (1), TP9 (1), R38 (1), R37 (1)

### R32  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.778, 149.901, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(U4-A1) -> R31 U4

- partners by shared nets: U4 (2), Y2 (1), U6 (1), U5 (1), U3 (1), U2 (1), U1 (1), TP10 (1)

### R33  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.222, 149.901, 0.0deg)  DNP

- **north**: 1 Net-(U4-A2) -> R34 U4 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R35 R37 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U4 (2), U6 (1), U5 (1), U3 (1), U2 (1), TP9 (1), R38 (1), R37 (1)

### R34  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.667, 149.901, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R36 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(U4-A2) -> R33 U4

- partners by shared nets: U4 (2), Y2 (1), U6 (1), U5 (1), U3 (1), U2 (1), U1 (1), TP10 (1)

### R35  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.112, 149.901, 0.0deg)  DNP

- **north**: 1 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R37 R38 TP9 U2 U3 U4 U5 U6 | 2 Net-(U6-SDO) -> R36 U6

- partners by shared nets: U6 (2), U5 (1), U4 (1), U3 (1), U2 (1), TP9 (1), R38 (1), R37 (1)

### R36  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_100k_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (186.556, 149.901, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R4 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 Net-(U6-SDO) -> R35 U6

- partners by shared nets: U6 (2), Y2 (1), U5 (1), U4 (1), U3 (1), U2 (1), U1 (1), TP10 (1)

### R37  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_5k1_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (187.001, 149.901, 0.0deg)

- **north**: 1 I2C_1_SCL -> D6 D8 J2 J3 R22 R23 R27 TP12 U4 U5 U6 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R38 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), J3 (2), J2 (2), U3 (1), U2 (1), TP9 (1)

### R38  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_5k1_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (182.999, 150.301, 0.0deg)

- **north**: 1 I2C_1_SDA -> D6 D8 J2 J3 R21 R28 TP11 U4 U5 U6 | 2 +3V3 -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 TP9 U2 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), J3 (2), J2 (2), U3 (1), U2 (1), TP9 (1)

### R4  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_5k1_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.444, 150.301, 0.0deg)

- **north**: 1 GND -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 TP10 U1 U2 U3 U4 U5 U6 Y2 | 2 /USB_CC2 -> D4 J1

- partners by shared nets: J1 (2), D4 (2), Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1), U2 (1)

### R5  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (183.888, 150.301, 0.0deg)

- **north**: 1 Net-(U1-DTR#) -> U1 | 2 SWDIO-JTMS -> TP3 U3

- partners by shared nets: U3 (1), U1 (1), TP3 (1)

### R6  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.333, 150.301, 0.0deg)

- **north**: 1 Net-(U1-RTS#) -> U1 | 2 SWCLK-JTCK -> TP4 U3

- partners by shared nets: U3 (1), U1 (1), TP4 (1)

### R7  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (184.778, 150.301, 0.0deg)

- **north**: 1 Net-(U1-DSR#) -> U1 | 2 JTRST -> R24 TP2 U3

- partners by shared nets: U3 (1), U1 (1), TP2 (1), R24 (1)

### R8  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.222, 150.301, 0.0deg)

- **north**: 1 Net-(U1-DCD#) -> U1 | 2 NRST -> R19 TP1 U3

- partners by shared nets: U3 (1), U1 (1), TP1 (1), R19 (1)

### R9  --  resistor  (ref_prefix)

`antmicro-footprints:R_0402_1005Metric`  value `R_0R_0402`  --  body 1.85 x 0.94 mm from **courtyard**, 2 pad(s), side F, pose (185.667, 150.301, 0.0deg)

- **north**: 1 Net-(U1-CTS#) -> U1 | 2 JTDO -> TP5 U3

- partners by shared nets: U3 (1), U1 (1), TP5 (1)

### TP1  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1.5mm`  value `TP_1.5mm_SMD`  --  body 1.5 x 1.5 mm from **pad_bbox**, 1 pad(s), side F, pose (186.112, 150.301, 0.0deg)

- **north**: 1 NRST (1) -> R19 R8 U3

- partners by shared nets: U3 (1), R8 (1), R19 (1)

### TP10  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1mm`  value `TP_1mm_SMD`  --  body 1.0 x 1.0 mm from **pad_bbox**, 1 pad(s), side F, pose (186.556, 150.301, 0.0deg)

- **north**: 1 GND (1) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 U1 U2 U3 U4 U5 U6 Y2

- partners by shared nets: Y2 (1), U6 (1), U5 (1), U4 (1), U3 (1), U2 (1), U1 (1), R4 (1)

### TP11  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1mm`  value `TP_1mm_SMD`  --  body 1.0 x 1.0 mm from **pad_bbox**, 1 pad(s), side F, pose (187.001, 150.301, 0.0deg)

- **north**: 1 I2C_1_SDA (1) -> D6 D8 J2 J3 R21 R28 R38 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), R38 (1), R28 (1), R21 (1), J3 (1), J2 (1)

### TP12  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1mm`  value `TP_1mm_SMD`  --  body 1.0 x 1.0 mm from **pad_bbox**, 1 pad(s), side F, pose (182.999, 150.701, 0.0deg)

- **north**: 1 I2C_1_SCL (1) -> D6 D8 J2 J3 R22 R23 R27 R37 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), R37 (1), R27 (1), R23 (1), R22 (1), J3 (1)

### TP2  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1.5mm`  value `TP_1.5mm_SMD`  --  body 1.5 x 1.5 mm from **pad_bbox**, 1 pad(s), side F, pose (183.444, 150.701, 0.0deg)

- **north**: 1 JTRST (1) -> R24 R7 U3

- partners by shared nets: U3 (1), R7 (1), R24 (1)

### TP3  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1.5mm`  value `TP_1.5mm_SMD`  --  body 1.5 x 1.5 mm from **pad_bbox**, 1 pad(s), side F, pose (183.888, 150.701, 0.0deg)

- **north**: 1 SWDIO-JTMS (1) -> R5 U3

- partners by shared nets: U3 (1), R5 (1)

### TP4  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1.5mm`  value `TP_1.5mm_SMD`  --  body 1.5 x 1.5 mm from **pad_bbox**, 1 pad(s), side F, pose (184.333, 150.701, 0.0deg)

- **north**: 1 SWCLK-JTCK (1) -> R6 U3

- partners by shared nets: U3 (1), R6 (1)

### TP5  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1.5mm`  value `TP_1.5mm_SMD`  --  body 1.5 x 1.5 mm from **pad_bbox**, 1 pad(s), side F, pose (184.778, 150.701, 0.0deg)

- **north**: 1 JTDO (1) -> R9 U3

- partners by shared nets: U3 (1), R9 (1)

### TP6  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1.5mm`  value `TP_1.5mm_SMD`  --  body 1.5 x 1.5 mm from **pad_bbox**, 1 pad(s), side F, pose (185.222, 150.701, 0.0deg)

- **north**: 1 JTDI (1) -> R10 R20

- partners by shared nets: R20 (1), R10 (1)

### TP7  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1mm`  value `TP_1mm_SMD`  --  body 1.0 x 1.0 mm from **pad_bbox**, 1 pad(s), side F, pose (185.667, 150.701, 0.0deg)

- **north**: 1 /FRAM_WP (1) -> R26 U3 U4

- partners by shared nets: U4 (1), U3 (1), R26 (1)

### TP8  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1mm`  value `TP_1mm_SMD`  --  body 1.0 x 1.0 mm from **pad_bbox**, 1 pad(s), side F, pose (186.112, 150.701, 0.0deg)

- **north**: 1 Net-(U3-PB8-BOOT0) (1) -> R27 R29 R30 U3

- partners by shared nets: U3 (1), R30 (1), R29 (1), R27 (1)

### TP9  --  testpoint  (part_class)

`antmicro-footprints:TP_SMD_1mm`  value `TP_1mm_SMD`  --  body 1.0 x 1.0 mm from **pad_bbox**, 1 pad(s), side F, pose (186.556, 150.701, 0.0deg)

- **north**: 1 +3V3 (1) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 U2 U3 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), U3 (1), U2 (1), R38 (1), R37 (1), R35 (1)

### U1  --  integrated circuit  (ref_prefix)

`antmicro-footprints:QFN-32-1EP_5x5mm`  value `FT232R_QFN`  --  body 5.49 x 5.49 mm from **courtyard**, 33 pad(s), side F, pose (187.001, 150.701, 0.0deg)

- **east**: 17 GND (GND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U2 U3 U4 U5 U6 Y2 | 18 Net-(U1-RESET#) (RESET#) -> R2 | 19 +5V (VCC) -> C1 C3 C7 C8 FB2 LD1 R2 U2 | 20 GND (GND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U2 U3 U4 U5 U6 Y2 | 21 unconnected-(U1-CBUS1-Pad21) (CBUS1) | 22 Net-(U1-CBUS0) (CBUS0) -> R11 | 23 unconnected-(U1-NC-Pad23) (NC) | 24 GND (AGND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U2 U3 U4 U5 U6 Y2
- **interior**: 33 GND (EP) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U2 U3 U4 U5 U6 Y2
- **north**: 25 unconnected-(U1-NC-Pad25) (NC) | 26 GND (TEST) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U2 U3 U4 U5 U6 Y2 | 27 unconnected-(U1-OSCI-Pad27) (OSCI) | 28 unconnected-(U1-OSCO-Pad28) (OSCO) | 29 unconnected-(U1-NC-Pad29) (NC) | 30 Net-(U1-TXD) (TXD) -> R13 R15 | 31 Net-(U1-DTR#) (DTR#) -> R5 | 32 Net-(U1-RTS#) (RTS#) -> R6
- **south**: 9 unconnected-(U1-CBUS4-Pad9) (CBUS4) | 10 unconnected-(U1-CBUS2-Pad10) (CBUS2) | 11 unconnected-(U1-CBUS3-Pad11) (CBUS3) | 12 unconnected-(U1-NC-Pad12) (NC) | 13 unconnected-(U1-NC-Pad13) (NC) | 14 /USB_D_P (USBDP) -> D5 J1 | 15 /USB_D_N (USBDM) -> D5 J1 | 16 Net-(U1-3V3OUT) (3V3OUT) -> C5 C6
- **west**: 1 Net-(U1-3V3OUT) (VCCIO) -> C5 C6 | 2 Net-(U1-RXD) (RXD) -> R14 R16 | 3 Net-(U1-RI#) (RI#) -> R10 | 4 GND (GND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U2 U3 U4 U5 U6 Y2 | 5 unconnected-(U1-NC-Pad5) (NC) | 6 Net-(U1-DSR#) (DSR#) -> R7 | 7 Net-(U1-DCD#) (DCD#) -> R8 | 8 Net-(U1-CTS#) (CTS#) -> R9

- partners by shared nets: J1 (3), D5 (3), U2 (2), R2 (2), C8 (2), C7 (2), C6 (2), C5 (2)

### U2  --  regulator  (footprint)

`antmicro-footprints:SOT-23-3`  value `AP7370-33SA-7`  --  body 3.5 x 3.25 mm from **courtyard**, 3 pad(s), side F, pose (182.999, 151.101, 0.0deg)

- **east**: 3 +5V (VIN) -> C1 C3 C7 C8 FB2 LD1 R2 U1
- **north**: 1 GND (GND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U3 U4 U5 U6 Y2
- **south**: 2 +3V3 (VOUT) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U3 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U3 (2), U1 (2), J3 (2), J2 (2), D9 (2)

### U3  --  integrated circuit  (ref_prefix)

`antmicro-footprints:LQFP-48_7x7mm_P0.5mm`  value `STM32G474CET6`  --  body 9.7 x 9.7 mm from **courtyard**, 48 pad(s), side F, pose (183.444, 151.101, 0.0deg)

- **east**: 25 /FRAM_WP (PB11) -> R26 TP7 U4 | 26 unconnected-(U3-PB12-Pad26) (PB12) | 27 unconnected-(U3-PB13-Pad27) (PB13) | 28 unconnected-(U3-PB14-Pad28) (PB14) | 29 unconnected-(U3-PB15-Pad29) (PB15) | 30 Net-(U3-PA8) (PA8) -> R21 | 31 Net-(U3-PA9) (PA9) -> R22 | 32 unconnected-(U3-PA10-Pad32) (PA10) | 33 unconnected-(U3-PA11-Pad33) (PA11) | 34 unconnected-(U3-PA12-Pad34) (PA12) | 35 GND (VSS) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U4 U5 U6 Y2 | 36 +3V3 (VDD) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U4 U5 U6
- **north**: 37 SWDIO-JTMS (PA13) -> R5 TP3 | 38 SWCLK-JTCK (PA14) -> R6 TP4 | 39 Net-(U3-PA15) (PA15) -> R20 R23 | 40 JTDO (PB3) -> R9 TP5 | 41 JTRST (PB4) -> R24 R7 TP2 | 42 unconnected-(U3-PB5-Pad42) (PB5) | 43 unconnected-(U3-PB6-Pad43) (PB6) | 44 unconnected-(U3-PB7-Pad44) (PB7) | 45 Net-(U3-PB8-BOOT0) (PB8-BOOT0) -> R27 R29 R30 TP8 | 46 Net-(U3-PB9) (PB9) -> R28 | 47 GND (VSS) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U4 U5 U6 Y2 | 48 +3V3 (VDD) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U4 U5 U6
- **south**: 13 /LD2 (PA5) -> LD2 | 14 unconnected-(U3-PA6-Pad14) (PA6) | 15 unconnected-(U3-PA7-Pad15) (PA7) | 16 unconnected-(U3-PB0-Pad16) (PB0) | 17 unconnected-(U3-PB1-Pad17) (PB1) | 18 unconnected-(U3-PB2-Pad18) (PB2) | 19 GND (VSSA) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U4 U5 U6 Y2 | 20 Net-(U3-VREF+) (VREF+) -> C22 C24 | 21 Net-(U3-VDDA) (VDDA) -> C19 C20 FB3 | 22 unconnected-(U3-PB10-Pad22) (PB10) | 23 GND (VSS) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U4 U5 U6 Y2 | 24 +3V3 (VDD) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U4 U5 U6
- **west**: 1 Net-(U3-VBAT) (VBAT) -> BAT1 | 2 /FTDI_USER_PB (PC13) -> R11 | 3 /OSC32_IN (PC14-OSC32_IN) -> C14 R18 Y1 | 4 /OSC32_OUT (PC15-OSC32_OUT) -> C16 R18 Y1 | 5 Net-(U3-PF0-OSC_IN) (PF0-OSC_IN) -> C23 R25 Y2 | 6 Net-(U3-PF1-OSC_OUT) (PF1-OSC_OUT) -> C21 R25 Y2 | 7 NRST (PG10-NRST) -> R19 R8 TP1 | 8 unconnected-(U3-PA0-Pad8) (PA0) | 9 unconnected-(U3-PA1-Pad9) (PA1) | 10 LPUART_1_STM_TX (PA2) -> R14 R15 | 11 LPUART_1_STM_RX (PA3) -> R13 R16 | 12 unconnected-(U3-PA4-Pad12) (PA4)

- partners by shared nets: Y2 (3), U4 (3), Y1 (2), U6 (2), U5 (2), U2 (2), R30 (2), R29 (2)

### U4  --  integrated circuit  (ref_prefix)

`antmicro-footprints:SOP-8_3.9x5.05mm_P1.27mm`  value `MB85RC1MTPNF-G`  --  body 5.55 x 7.54 mm from **courtyard**, 8 pad(s), side F, pose (183.888, 151.101, 0.0deg)

- **east**: 4 GND (VSS) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U5 U6 Y2
- **north**: 5 I2C_1_SDA (SDA) -> D6 D8 J2 J3 R21 R28 R38 TP11 U5 U6 | 6 I2C_1_SCL (SCL) -> D6 D8 J2 J3 R22 R23 R27 R37 TP12 U5 U6 | 7 /FRAM_WP (WP) -> R26 TP7 U3 | 8 +3V3 (VDD) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U5 U6
- **south**: 1 unconnected-(U4-NC-Pad1) (NC) | 2 Net-(U4-A1) (A1) -> R31 R32 | 3 Net-(U4-A2) (A2) -> R33 R34

- partners by shared nets: U6 (4), U5 (4), J3 (4), J2 (4), U3 (3), D8 (3), D6 (3), U2 (2)

### U5  --  integrated circuit  (ref_prefix)

`antmicro-footprints:Sensirion_DFN-4-1.5x1.5x0.5mm_P0.8mm`  value `SHT45`  --  body 2.498 x 2.498 mm from **courtyard**, 4 pad(s), side F, pose (184.333, 151.101, 0.0deg)

- **east**: 3 +3V3 (VDD) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U6
- **north**: 1 I2C_1_SDA (SDA) -> D6 D8 J2 J3 R21 R28 R38 TP11 U4 U6 | 4 GND (VSS) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U6 Y2
- **south**: 2 I2C_1_SCL (SCL) -> D6 D8 J2 J3 R22 R23 R27 R37 TP12 U4 U6

- partners by shared nets: U6 (4), U4 (4), J3 (4), J2 (4), D8 (3), D6 (3), U3 (2), U2 (2)

### U6  --  integrated circuit  (ref_prefix)

`antmicro-footprints:LGA-8_2.5x2.5mm_BME280`  value `BME280`  --  body 3.2 x 3.2 mm from **courtyard**, 8 pad(s), side F, pose (184.778, 151.101, 0.0deg)

- **east**: 5 Net-(U6-SDO) (SDO) -> R35 R36
- **north**: 1 GND (GND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 Y2 | 2 +3V3 (CSB) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 | 3 I2C_1_SDA (SDI) -> D6 D8 J2 J3 R21 R28 R38 TP11 U4 U5 | 4 I2C_1_SCL (SCK) -> D6 D8 J2 J3 R22 R23 R27 R37 TP12 U4 U5
- **south**: 6 +3V3 (VDDIO) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5 | 7 GND (GND) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 Y2 | 8 +3V3 (VDD) -> C10 C11 C12 C13 C15 C17 C18 C25 C26 C27 C28 C9 D7 D9 FB3 J2 J3 R19 R24 R26 R29 R31 R33 R35 R37 R38 TP9 U2 U3 U4 U5

- partners by shared nets: U5 (4), U4 (4), J3 (4), J2 (4), D8 (3), D6 (3), U3 (2), U2 (2)

### Y1  --  crystal  (footprint)

`antmicro-footprints:Resonator_SMD_ECS_ECX-31B_3.2x1.5x0.9mm`  value `Resonator_32.768kHz_ECX-31B`  --  body 4.001 x 2.498 mm from **courtyard**, 2 pad(s), side F, pose (185.222, 151.101, 0.0deg)

- **north**: 1 /OSC32_IN -> C14 R18 U3 | 2 /OSC32_OUT -> C16 R18 U3

- partners by shared nets: U3 (2), R18 (2), C16 (1), C14 (1)

### Y2  --  crystal  (footprint)

`antmicro-footprints:Resonator_SMD_Abracon_ABM3B_5x3.2mm`  value `Resonator_8MHz_ABM3B`  --  body 4.175 x 6.35 mm from **courtyard**, 4 pad(s), side F, pose (185.667, 151.101, 0.0deg)

- **east**: 3 Net-(U3-PF0-OSC_IN) -> C23 R25 U3
- **north**: 1 Net-(U3-PF1-OSC_OUT) -> C21 R25 U3 | 4 GND (SH) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6
- **south**: 2 GND (SH) -> BAT1 C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C23 C24 C25 C26 C27 C28 C3 C4 C5 C6 C7 C8 C9 D1 D2 D3 D4 D5 D6 D7 D8 D9 FB1 J1 J2 J3 R1 R12 R17 R3 R30 R32 R34 R36 R4 TP10 U1 U2 U3 U4 U5 U6

- partners by shared nets: U3 (3), R25 (2), C23 (2), C21 (2), U6 (1), U5 (1), U4 (1), U2 (1)

## Sources

- **body_mm / body_source** -- placement.body.board_bodies (#896)
- **diff_pairs** -- list_nets.find_differential_pairs (rejects 2-terminal resonators)
- **emc_roles** -- placement.emc_roles (#1254): roles read off PIN FUNCTIONS (SW/LX, VIN, PGND/GND; I/O or CH lines) and the role table (crystals); every leg pad edge to pad edge (legality.pad_rect + rect_gap), never a loop area; `unknown` where the pins carry no function; rows carry max_mm null -- the limit is the author's. `keep_away`: PROPOSED design-brief rules (#1253), each clock part's nets against the switch nodes, in route.py's --keep-away syntax (parsed and resolved by keep_away), at a derived default gap, measured by check_floorplan's own keep_away grade
- **mating** -- which parts count as connectors: render_placement.connector_edge_facts. `edge` is the edge the mating face points at when the body names one (placement.mating, #1155), else the nearest, and `dist_mm` / `overhang_mm` measure to THAT edge; `nearest_*` always to the nearest. Both from the placement.body occupancy rect, because connector_edge_facts reads the placement state pad-box ladder and would put two geometries on one sheet
- **pads_by_face** -- placement.escape.assign_faces (#850)
- **part_class** -- placement.part_class.classify_part
- **pin_order** -- placement.pair_order.pair_metrics; a pair through per-leg series parts (#1251): the junctions of diff_xnet.find_ac_coupled_xnets, judged by pair_order.composed_pair_metrics
- **pours** -- board_brief.pour_census (the brief's own `pours`)
- **role** -- placement.roles.infer_role, from footprint name, pins (pintype / pin function) and reference prefix; the board carries no datasheet or 3D-model field to cite
- **serves** -- placement.groups tether election: the nearest cap owner on the cap's rail -- an IC (4+ copper pads, not a row) or a supply owner such as a 3-pad regulator (#1249)


Copper-to-hole 0.25mm for NPTH holes (from the board's own min_hole_clearance, above the 0.2mm fab floor); plated holes and vias: copper clearance
# Component context -- fixed.kicad_pcb

Board 50.0 x 60.0 mm, layers F.Cu, B.Cu, floors clearance 0.15mm / track 0.15mm.

**This board is a PILE** (footprints span 10.0% of the board diagonal; 100% of footprints lie outside the board outline): its poses are staging, not decisions. Every claim read off a pose -- a pin-order verdict, a leg distance, a mating edge, a nearest-cap election -- is WITHHELD unless every part it reads is KiCad-locked (none is). A part's printed `pose` is where the file has it. Withheld: emc_roles legs 2, parts[].mating 5, parts[].serves 20, pin_order.rows 187.

Copper pours: +3V3 on F.Cu (fill unknown, 100% of the board); GND on B.Cu (fill unknown, 100% of the board).
Differential pairs: /USB_DP//USB_DM.

Every derived column names its source; `unknown` means the tool looked and could not tell, which is not the same as absent. See the SOURCES section at the end.

## Pin-order agreement

187 pin-order row(s) WITHHELD: the board is a pile, and a verdict measured at staging poses is not a claim. Place the parts, then read this section.


## EMC roles (report only)

REPORT ONLY: no intent key is written. Each row is in the shape `proximity[]` reads (`ref`, `near`, `pads`) with `max_mm` left null: the limit is the author's, from the datasheet, and copying the measured gap into it would bless the current pose (#902). Legs are reported, never a loop area, which a self-crossing pad polygon can shrink while every leg grows (#1254).

Legs: pad edge to pad edge: placement.legality.pad_rect + rect_gap, signed (negative = the pad boxes overlap) -- what rule_proximity measures for a declared row: each subject pad against the nearest partner pad on its own net.

### Y1  --  crystal

- Y1 is in the role table's crystal row: footprint name contains 'crystal'
- U1 pad 2 is OSCI
- U1 pad 3 is OSCO

| leg | from | to | net | gap mm | sides |
|---|---|---|---|---|---|
| crystal -> load pin | Y1.1 | U1.2 (OSCI) | /OSCI | - | F / F |
| crystal -> load pin | Y1.3 | U1.3 (OSCO) | /OSCO | - | F / F |

- row, worst leg withheld (staging poses): `{"max_mm": null, "near": "U1", "pads": {"U1": ["2", "3"], "Y1": ["1", "3"]}, "ref": "Y1"}`

## Parts

### C1  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.239, 118.45, 0.0deg)

- **north**: 1 +5V -> FB1 U2 | 2 GND -> C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U2 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1), U4 (1)

### C10  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.929, 118.45, 0.0deg)

- **north**: 1 +1V8 -> C11 C12 C7 U1 | 2 GND -> C1 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U1 (2), C7 (2), C12 (2), C11 (2), Y1 (1), U9 (1), U8 (1), U7 (1)

### C11  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (123.619, 118.45, 0.0deg)

- **north**: 1 +1V8 -> C10 C12 C7 U1 | 2 GND -> C1 C10 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U1 (2), C7 (2), C12 (2), C10 (2), Y1 (1), U9 (1), U8 (1), U7 (1)

### C12  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (124.31, 118.45, 0.0deg)

- **north**: 1 +1V8 -> C10 C11 C7 U1 | 2 GND -> C1 C10 C11 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U1 (2), C7 (2), C11 (2), C10 (2), Y1 (1), U9 (1), U8 (1), U7 (1)

### C13  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (125.0, 118.45, 0.0deg)

- **north**: 1 +3V3 -> C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6 | 2 GND -> C1 C10 C11 C12 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U6 (2), U5 (2), U4 (2), U2 (2), U11 (2), U1 (2), J4 (2), C22 (2)

### C14  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (125.69, 118.45, 0.0deg)

- **north**: 1 +3V3 -> C13 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6 | 2 GND -> C1 C10 C11 C12 C13 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U6 (2), U5 (2), U4 (2), U2 (2), U11 (2), U1 (2), J4 (2), C22 (2)

### C15  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (126.381, 118.45, 0.0deg)

- **north**: 1 +3V3 -> C13 C14 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6 | 2 GND -> C1 C10 C11 C12 C13 C14 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U6 (2), U5 (2), U4 (2), U2 (2), U11 (2), U1 (2), J4 (2), C22 (2)

### C16  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.071, 118.45, 0.0deg)

- **north**: 1 +3V3 -> C13 C14 C15 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U6 (2), U5 (2), U4 (2), U2 (2), U11 (2), U1 (2), J4 (2), C22 (2)

### C17  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.761, 118.45, 0.0deg)

- **north**: 1 Vdrive -> C19 C20 C21 R11 R17 R25 U10 U12 U7 U8 U9 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U9 (2), U8 (2), U7 (2), U12 (2), U10 (2), C21 (2), C20 (2), C19 (2)

### C18  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.239, 119.064, 0.0deg)

- **north**: 1 +3V3 -> C13 C14 C15 C16 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U6 (2), U5 (2), U4 (2), U2 (2), U11 (2), U1 (2), J4 (2), C22 (2)

### C19  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.929, 119.064, 0.0deg)

- **north**: 1 Vdrive -> C17 C20 C21 R11 R17 R25 U10 U12 U7 U8 U9 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U9 (2), U8 (2), U7 (2), U12 (2), U10 (2), C21 (2), C20 (2), C17 (2)

### C2  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (123.619, 119.064, 0.0deg)

- **north**: 1 +3V3 -> C13 C14 C15 C16 C18 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U6 (2), U5 (2), U4 (2), U2 (2), U11 (2), U1 (2), J4 (2), C22 (2)

### C20  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (124.31, 119.064, 0.0deg)

- **north**: 1 Vdrive -> C17 C19 C21 R11 R17 R25 U10 U12 U7 U8 U9 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U9 (2), U8 (2), U7 (2), U12 (2), U10 (2), C21 (2), C19 (2), C17 (2)

### C21  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (125.0, 119.064, 0.0deg)

- **north**: 1 Vdrive -> C17 C19 C20 R11 R17 R25 U10 U12 U7 U8 U9 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U9 (2), U8 (2), U7 (2), U12 (2), U10 (2), C20 (2), C19 (2), C17 (2)

### C22  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (125.69, 119.064, 0.0deg)

- **north**: 1 +3V3 -> C13 C14 C15 C16 C18 C2 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U6 (2), U5 (2), U4 (2), U2 (2), U11 (2), U1 (2), J4 (2), C2 (2)

### C3  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (126.381, 119.064, 0.0deg)

- **north**: 1 /OSCI -> U1 Y1 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: Y1 (2), U1 (2), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1), U4 (1)

### C4  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.071, 119.064, 0.0deg)

- **north**: 1 /OSCO -> U1 Y1 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: Y1 (2), U1 (2), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1), U4 (1)

### C5  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.761, 119.064, 0.0deg)

- **north**: 1 /VPLL -> C8 FB2 U1 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U1 (2), C8 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1)

### C6  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.239, 119.677, 0.0deg)

- **north**: 1 /VPHY -> C9 FB3 U1 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U1 (2), C9 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1)

### C7  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.929, 119.677, 0.0deg)

- **north**: 1 +1V8 -> C10 C11 C12 U1 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U1 (2), C12 (2), C11 (2), C10 (2), Y1 (1), U9 (1), U8 (1), U7 (1)

### C8  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (123.619, 119.677, 0.0deg)

- **north**: 1 /VPLL -> C5 FB2 U1 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U1 (2), C5 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1)

### C9  --  capacitor  (ref_prefix)

`Capacitor_SMD:C_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (124.31, 119.677, 0.0deg)

- **north**: 1 /VPHY -> C6 FB3 U1 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U1 (2), C6 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1)

### D1  --  diode  (ref_prefix)

`LED_SMD:LED_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (125.0, 119.677, 0.0deg)

- **north**: 1 /ACT_LED_K (K) -> R7 | 2 +3V3 (A) -> C13 C14 C15 C16 C18 C2 C22 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), U2 (1), U11 (1), U1 (1), R7 (1), R6 (1)

### D2  --  diode  (ref_prefix)

`LED_SMD:LED_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (125.69, 119.677, 0.0deg)

- **north**: 1 /RX_LED_K (K) -> R8 | 2 +3V3 (A) -> C13 C14 C15 C16 C18 C2 C22 D1 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), U2 (1), U11 (1), U1 (1), R8 (1), R6 (1)

### D3  --  diode  (ref_prefix)

`LED_SMD:LED_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (126.381, 119.677, 0.0deg)

- **north**: 1 /TX_LED_K (K) -> R9 | 2 +3V3 (A) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), U2 (1), U11 (1), U1 (1), R9 (1), R6 (1)

### D4  --  diode  (ref_prefix)

`LED_SMD:LED_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.071, 119.677, 0.0deg)

- **north**: 1 /USB_LED_K (K) -> R10 | 2 +3V3 (A) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6

- partners by shared nets: U6 (1), U5 (1), U4 (1), U2 (1), U11 (1), U1 (1), R6 (1), R23 (1)

### D5  --  diode  (ref_prefix)

`LED_SMD:LED_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.761, 119.677, 0.0deg)

- **north**: 1 GND (K) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 2 /PWR_LED_A (A) -> R18

- partners by shared nets: Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1), U4 (1), U3 (1)

### D6  --  diode  (ref_prefix)

`LED_SMD:LED_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.239, 120.291, 0.0deg)

- **north**: 1 GND (K) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 2 /SWD_EN_LED (A) -> R21

- partners by shared nets: Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1), U4 (1), U3 (1)

### FB1  --  ferrite bead  (ref_prefix)

`Inductor_SMD:L_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.929, 120.291, 0.0deg)

- **north**: 1 +5V -> C1 U2 | 2 VBUS -> J1 U3

- partners by shared nets: U3 (1), U2 (1), J1 (1), C1 (1)

### FB2  --  ferrite bead  (ref_prefix)

`Inductor_SMD:L_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (123.619, 120.291, 0.0deg)

- **north**: 1 /VPLL -> C5 C8 U1 | 2 +3V3 -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6

- partners by shared nets: U1 (2), U6 (1), U5 (1), U4 (1), U2 (1), U11 (1), R6 (1), R23 (1)

### FB3  --  ferrite bead  (ref_prefix)

`Inductor_SMD:L_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (124.31, 120.291, 0.0deg)

- **north**: 1 /VPHY -> C6 C9 U1 | 2 +3V3 -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 J4 R18 R23 R6 U1 U11 U2 U4 U5 U6

- partners by shared nets: U1 (2), U6 (1), U5 (1), U4 (1), U2 (1), U11 (1), R6 (1), R23 (1)

### FID1  --  fiducial  (part_class)

`Fiducial:Fiducial_1mm_Mask2mm`  --  body 2.5 x 2.5 mm from **courtyard**, 1 pad(s), side F, pose (125.0, 120.291, 0.0deg)

- **north**:  -

### FID2  --  fiducial  (part_class)

`Fiducial:Fiducial_1mm_Mask2mm`  --  body 2.5 x 2.5 mm from **courtyard**, 1 pad(s), side F, pose (125.69, 120.291, 0.0deg)

- **north**:  -

### FID3  --  fiducial  (part_class)

`Fiducial:Fiducial_1mm_Mask2mm`  --  body 2.5 x 2.5 mm from **courtyard**, 1 pad(s), side F, pose (126.381, 120.291, 0.0deg)

- **north**:  -

### H1  --  mount hole  (part_class)

`MountingHole:MountingHole_3.2mm_M3`  --  body 6.9 x 6.9 mm from **courtyard**, 1 pad(s), side F, pose (127.071, 120.291, 0.0deg)

- **interior**:  -

### H2  --  mount hole  (part_class)

`MountingHole:MountingHole_3.2mm_M3`  --  body 6.9 x 6.9 mm from **courtyard**, 1 pad(s), side F, pose (127.761, 120.291, 0.0deg)

- **interior**:  -

### H3  --  mount hole  (part_class)

`MountingHole:MountingHole_3.2mm_M3`  --  body 6.9 x 6.9 mm from **courtyard**, 1 pad(s), side F, pose (122.239, 120.904, 0.0deg)

- **interior**:  -

### H4  --  mount hole  (part_class)

`MountingHole:MountingHole_3.2mm_M3`  --  body 6.9 x 6.9 mm from **courtyard**, 1 pad(s), side F, pose (122.929, 120.904, 0.0deg)

- **interior**:  -

### J1  --  edge receptacle  (part_class)

`Connector_USB:USB_C_Receptacle_GCT_USB4085`  --  body 10.55 x 10.17 mm from **courtyard**, 20 pad(s), side F, pose (123.619, 120.904, 0.0deg)

- **east**: S1 GND (SHIELD) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | S1 GND (SHIELD) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1
- **north**: A1 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | A4 VBUS (VBUS) -> FB1 U3 | A5 /USB_CC1 (CC1) -> R2 U3 | A6 /USB_DP (D+) -> U1 U3 | A7 /USB_DM (D-) -> U1 U3 | A8 unconnected-(J1-PadA8) (SBU1) | A9 VBUS (VBUS) -> FB1 U3 | A12 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1
- **south**: B1 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | B4 VBUS (VBUS) -> FB1 U3 | B5 /USB_CC2 (CC2) -> R1 U3 | B6 /USB_DP (D+) -> U1 U3 | B7 /USB_DM (D-) -> U1 U3 | B8 unconnected-(J1-PadB8) (SBU2) | B9 VBUS (VBUS) -> FB1 U3 | B12 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | S1 GND (SHIELD) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1
- **west**: S1 GND (SHIELD) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U3 (6), U1 (3), R2 (2), R1 (2), Y1 (1), U9 (1), U8 (1), U7 (1)

### J2  --  pin header  (footprint)

`Connector_PinHeader_1.27mm:PinHeader_2x07_P1.27mm_Vertical_SMD`  --  body 8.6 x 9.9 mm from **courtyard**, 14 pad(s), side F, pose (124.31, 120.904, 0.0deg)

- **east**: 4 /TMS_TRGT (JTMS/SWDIO) -> J4 R14 | 6 /TCK_TRGT (JCLK/SWCLK) -> J4 R13 | 8 /TDO_TRGT (JTDO/SWO) -> J4 R15 | 10 /TDI_TRGT (JTDI/NC) -> J4 R16 | 12 /SRST_N_TRGT (~{RST}) -> J4 R12 | 14 /RXD_TRGT (VCP_TX) -> J4 R20
- **north**: 1 unconnected-(J2-Pad1) (NC) | 2 unconnected-(J2-Pad2) (NC)
- **south**: 13 /TXD_TRGT (VCP_RX) -> J4 R19
- **west**: 3 /VDRIVE_TRGT (VCC) -> J4 R11 | 5 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 7 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 9 unconnected-(J2-Pad9) (JRCLK/NC) | 11 GND (GNDDetect) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: J4 (9), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1), U4 (1)

### J4  --  pin header  (footprint)

`Connector_PinHeader_2.54mm:PinHeader_1x16_P2.54mm_Vertical`  --  body 3.6 x 41.7 mm from **courtyard**, 16 pad(s), side F, pose (125.0, 120.904, 0.0deg)

- **east**: 2 /VDRIVE_TRGT (Pin_2) -> J2 R11 | 3 GND (Pin_3) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 4 /TCK_TRGT (Pin_4) -> J2 R13 | 5 /TDI_TRGT (Pin_5) -> J2 R16 | 6 /TDO_TRGT (Pin_6) -> J2 R15 | 7 /TMS_TRGT (Pin_7) -> J2 R14 | 8 /SRST_N_TRGT (Pin_8) -> J2 R12 | 9 GND (Pin_9) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 10 /TXD_TRGT (Pin_10) -> J2 R19 | 11 /RXD_TRGT (Pin_11) -> J2 R20 | 12 /GPIO_A (Pin_12) -> U1 | 13 /GPIO_B (Pin_13) -> U1 | 14 /GPIO_C (Pin_14) -> U1 | 15 /GPIO_D (Pin_15) -> U1 | 16 GND (Pin_16) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1
- **north**: 1 +3V3 (Pin_1) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 R18 R23 R6 U1 U11 U2 U4 U5 U6

- partners by shared nets: J2 (9), U1 (6), U6 (2), U5 (2), U4 (2), U2 (2), U11 (2), C22 (2)

### Q1  --  npn/pnp transistor  (footprint)

`Package_TO_SOT_SMD:SOT-23`  --  body 3.4 x 3.5 mm from **courtyard**, 3 pad(s), side F, pose (125.69, 120.904, 0.0deg)

- **east**: 3 /SRST_N_R (D) -> R12 R17 SW2
- **north**: 1 /SRST (G) -> R24 U1
- **south**: 2 GND (S) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U1 (2), SW2 (2), R24 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1)

### R1  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (126.381, 120.904, 0.0deg)

- **north**: 1 /USB_CC2 -> J1 U3 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U3 (2), J1 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1)

### R10  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.071, 120.904, 0.0deg)

- **north**: 1 /USB_LED_K -> D4 | 2 /USB_LED_N -> U1

- partners by shared nets: U1 (1), D4 (1)

### R11  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.761, 120.904, 0.0deg)

- **north**: 1 /VDRIVE_TRGT -> J2 J4 | 2 Vdrive -> C17 C19 C20 C21 R17 R25 U10 U12 U7 U8 U9

- partners by shared nets: U9 (1), U8 (1), U7 (1), U12 (1), U10 (1), R25 (1), R17 (1), J4 (1)

### R12  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.239, 121.518, 0.0deg)

- **north**: 1 /SRST_N_TRGT -> J2 J4 | 2 /SRST_N_R -> Q1 R17 SW2

- partners by shared nets: SW2 (1), R17 (1), Q1 (1), J4 (1), J2 (1)

### R13  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.929, 121.518, 0.0deg)

- **north**: 1 /TCK_TRGT -> J2 J4 | 2 /TCK_R -> U7

- partners by shared nets: U7 (1), J4 (1), J2 (1)

### R14  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (123.619, 121.518, 0.0deg)

- **north**: 1 /TMS_TRGT -> J2 J4 | 2 /TMS_R -> U10 U6 U9

- partners by shared nets: U9 (1), U6 (1), U10 (1), J4 (1), J2 (1)

### R15  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (124.31, 121.518, 0.0deg)

- **north**: 1 /TDO_TRGT -> J2 J4 | 2 /TDO_R -> SW1 U5

- partners by shared nets: U5 (1), SW1 (1), J4 (1), J2 (1)

### R16  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (125.0, 121.518, 0.0deg)

- **north**: 1 /TDI_TRGT -> J2 J4 | 2 /TDI_R -> U8

- partners by shared nets: U8 (1), J4 (1), J2 (1)

### R17  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (125.69, 121.518, 0.0deg)

- **north**: 1 /SRST_N_R -> Q1 R12 SW2 | 2 Vdrive -> C17 C19 C20 C21 R11 R25 U10 U12 U7 U8 U9

- partners by shared nets: U9 (1), U8 (1), U7 (1), U12 (1), U10 (1), SW2 (1), R25 (1), R12 (1)

### R18  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (126.381, 121.518, 0.0deg)

- **north**: 1 +3V3 -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R23 R6 U1 U11 U2 U4 U5 U6 | 2 /PWR_LED_A -> D5

- partners by shared nets: U6 (1), U5 (1), U4 (1), U2 (1), U11 (1), U1 (1), R6 (1), R23 (1)

### R19  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.071, 121.518, 0.0deg)

- **north**: 1 /TXD_TRGT -> J2 J4 | 2 /TXD_R -> U12

- partners by shared nets: U12 (1), J4 (1), J2 (1)

### R2  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.761, 121.518, 0.0deg)

- **north**: 1 /USB_CC1 -> J1 U3 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U3 (2), J1 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1)

### R20  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.239, 122.132, 0.0deg)

- **north**: 1 /RXD_R -> SW1 | 2 /RXD_TRGT -> J2 J4

- partners by shared nets: SW1 (1), J4 (1), J2 (1)

### R21  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.929, 122.132, 0.0deg)

- **north**: 1 /SWD_EN_LED -> D6 | 2 /SWD_EN -> R22 U1 U5 U6 U8 U9

- partners by shared nets: U9 (1), U8 (1), U6 (1), U5 (1), U1 (1), R22 (1), D6 (1)

### R22  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (123.619, 122.132, 0.0deg)

- **north**: 1 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 2 /SWD_EN -> R21 U1 U5 U6 U8 U9

- partners by shared nets: U9 (2), U8 (2), U6 (2), U5 (2), U1 (2), Y1 (1), U7 (1), U4 (1)

### R23  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (124.31, 122.132, 0.0deg)

- **north**: 1 /SWDIO_OE_N -> U1 U10 | 2 +3V3 -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R6 U1 U11 U2 U4 U5 U6

- partners by shared nets: U1 (2), U6 (1), U5 (1), U4 (1), U2 (1), U11 (1), U10 (1), R6 (1)

### R24  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (125.0, 122.132, 0.0deg)

- **north**: 1 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 2 /SRST -> Q1 U1

- partners by shared nets: U1 (2), Q1 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1)

### R25  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (125.69, 122.132, 0.0deg)

- **north**: 1 /RXD_IN -> SW1 U11 | 2 Vdrive -> C17 C19 C20 C21 R11 R17 U10 U12 U7 U8 U9

- partners by shared nets: U9 (1), U8 (1), U7 (1), U12 (1), U11 (1), U10 (1), SW1 (1), R17 (1)

### R3  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (126.381, 122.132, 0.0deg)

- **north**: 1 /EE_CS -> U1 U4 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U4 (2), U1 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1)

### R4  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.071, 122.132, 0.0deg)

- **north**: 1 /REF -> U1 | 2 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: U1 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1), U4 (1)

### R5  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (127.761, 122.132, 0.0deg)

- **north**: 1 /EE_DO -> U4 | 2 /EE_DATA -> U1 U4

- partners by shared nets: U4 (2), U1 (1)

### R6  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.239, 122.745, 0.0deg)

- **north**: 1 /RESET_N -> U1 | 2 +3V3 -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 U1 U11 U2 U4 U5 U6

- partners by shared nets: U1 (2), U6 (1), U5 (1), U4 (1), U2 (1), U11 (1), R23 (1), R18 (1)

### R7  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (122.929, 122.745, 0.0deg)

- **north**: 1 /ACT_LED_N -> U1 | 2 /ACT_LED_K -> D1

- partners by shared nets: U1 (1), D1 (1)

### R8  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (123.619, 122.745, 0.0deg)

- **north**: 1 /RX_LED_K -> D2 | 2 /RX_LED_N -> U1

- partners by shared nets: U1 (1), D2 (1)

### R9  --  resistor  (ref_prefix)

`Resistor_SMD:R_0603_1608Metric`  --  body 2.96 x 1.46 mm from **courtyard**, 2 pad(s), side F, pose (124.31, 122.745, 0.0deg)

- **north**: 1 /TX_LED_K -> D3 | 2 /TX_LED_N -> U1

- partners by shared nets: U1 (1), D3 (1)

### SW1  --  edge actuator  (part_class)

`Button_Switch_SMD:SW_SPDT_PCM12`  --  body 8.8 x 5.85 mm from **courtyard**, 9 pad(s), side F, pose (125.0, 122.745, 0.0deg)

- **east**:  - |  -
- **interior**:  - |  -
- **north**: 1 /TDO_R (A) -> R15 U5 | 2 /RXD_IN (B) -> R25 U11 | 3 /RXD_R (C) -> R20
- **south**:  -
- **west**:  -

- partners by shared nets: U5 (1), U11 (1), R25 (1), R20 (1), R15 (1)

### SW2  --  edge actuator  (part_class)

`Button_Switch_SMD:SW_Push_1P1T_NO_E-Switch_TL3301NxxxxxG`  --  body 11.7 x 6.5 mm from **courtyard**, 4 pad(s), side F, pose (125.69, 122.745, 0.0deg)

- **east**: 2 GND (2) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1
- **north**: 1 /SRST_N_R (1) -> Q1 R12 R17 | 1 /SRST_N_R (1) -> Q1 R12 R17
- **south**: 2 GND (2) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: Q1 (2), Y1 (1), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1), U4 (1)

### TP1  --  testpoint  (part_class)

`TestPoint:TestPoint_Pad_D1.0mm`  --  body 2.0 x 2.0 mm from **courtyard**, 1 pad(s), side F, pose (126.381, 122.745, 0.0deg)

- **north**: 1 /RTS_N (1) -> U1

- partners by shared nets: U1 (1)

### TP2  --  testpoint  (part_class)

`TestPoint:TestPoint_Pad_D1.0mm`  --  body 2.0 x 2.0 mm from **courtyard**, 1 pad(s), side F, pose (127.071, 122.745, 0.0deg)

- **north**: 1 /CTS_N (1) -> U1

- partners by shared nets: U1 (1)

### U1  --  integrated circuit  (ref_prefix)

`Package_QFP:LQFP-64_10x10mm_P0.5mm`  --  body 13.4 x 13.4 mm from **courtyard**, 64 pad(s), side F, pose (127.761, 122.745, 0.0deg)

- **east**: 33 /GPIO_D (ACBUS6) -> J4 | 34 unconnected-(U1-Pad34) (ACBUS7) | 35 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 36 unconnected-(U1-Pad36) (~{SUSPEND}) | 37 +1V8 (VCORE) -> C10 C11 C12 C7 | 38 /TXD (BDBUS0) -> U12 | 39 /RXD (BDBUS1) -> U11 | 40 /RTS_N (BDBUS2) -> TP1 | 41 /CTS_N (BDBUS3) -> TP2 | 42 +3V3 (VCCIO) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U11 U2 U4 U5 U6 | 43 unconnected-(U1-Pad43) (BDBUS4) | 44 unconnected-(U1-Pad44) (BDBUS5) | 45 unconnected-(U1-Pad45) (BDBUS6) | 46 unconnected-(U1-Pad46) (BDBUS7) | 47 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 48 unconnected-(U1-Pad48) (BCBUS0)
- **north**: 49 +1V8 (VREGOUT) -> C10 C11 C12 C7 | 50 +3V3 (VREGIN) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U11 U2 U4 U5 U6 | 51 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 52 unconnected-(U1-Pad52) (BCBUS1) | 53 unconnected-(U1-Pad53) (BCBUS2) | 54 /RX_LED_N (BCBUS3) -> R8 | 55 /TX_LED_N (BCBUS4) -> R9 | 56 +3V3 (VCCIO) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U11 U2 U4 U5 U6 | 57 unconnected-(U1-Pad57) (BCBUS5) | 58 unconnected-(U1-Pad58) (BCBUS6) | 59 unconnected-(U1-Pad59) (BCBUS7) | 60 /USB_LED_N (~{PWREN}) -> R10 | 61 /EE_DATA (EEDATA) -> R5 U4 | 62 /EE_CLK (EECLK) -> U4 | 63 /EE_CS (EECS) -> R3 U4 | 64 +1V8 (VCORE) -> C10 C11 C12 C7
- **south**: 17 /TDI (ADBUS1) -> U10 U8 | 18 /TDO (ADBUS2) -> U5 U6 | 19 /TMS (ADBUS3) -> U9 | 20 +3V3 (VCCIO) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U11 U2 U4 U5 U6 | 21 /ACT_LED_N (ADBUS4) -> R7 | 22 /SWD_EN (ADBUS5) -> R21 R22 U5 U6 U8 U9 | 23 /SWDIO_OE_N (ADBUS6) -> R23 U10 | 24 /SRST (ADBUS7) -> Q1 R24 | 25 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 26 unconnected-(U1-Pad26) (ACBUS0) | 27 /GPIO_A (ACBUS1) -> J4 | 28 /GPIO_B (ACBUS2) -> J4 | 29 unconnected-(U1-Pad29) (ACBUS3) | 30 unconnected-(U1-Pad30) (ACBUS4) | 31 +3V3 (VCCIO) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U11 U2 U4 U5 U6 | 32 /GPIO_C (ACBUS5) -> J4
- **west**: 1 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 2 /OSCI (OSCI) -> C3 Y1 | 3 /OSCO (OSCO) -> C4 Y1 | 4 /VPHY (VPHY) -> C6 C9 FB3 | 5 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 6 /REF (REF) -> R4 | 7 /USB_DM (DM) -> J1 U3 | 8 /USB_DP (DP) -> J1 U3 | 9 /VPLL (VPLL) -> C5 C8 FB2 | 10 GND (AGND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 11 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 12 +1V8 (VCORE) -> C10 C11 C12 C7 | 13 GND (TEST) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 14 /RESET_N (~{RESET}) -> R6 | 15 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 16 /TCK (ADBUS0) -> U7

- partners by shared nets: J4 (6), U4 (5), U6 (4), U5 (4), Y1 (3), U9 (3), U8 (3), U3 (3)

### U10  --  integrated circuit  (ref_prefix)

`Package_TO_SOT_SMD:SOT-353_SC-70-5`  --  body 3.2 x 2.8 mm from **courtyard**, 5 pad(s), side F, pose (122.239, 123.359, 0.0deg)

- **east**: 4 /TMS_R -> R14 U6 U9
- **north**: 1 /SWDIO_OE_N -> R23 U1 | 5 Vdrive (VCC) -> C17 C19 C20 C21 R11 R17 R25 U12 U7 U8 U9
- **south**: 3 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1
- **west**: 2 /TDI -> U1 U8

- partners by shared nets: U9 (3), U8 (3), U1 (3), U7 (2), U6 (2), U12 (2), C21 (2), C20 (2)

### U11  --  integrated circuit  (ref_prefix)

`Package_TO_SOT_SMD:SOT-353_SC-70-5`  --  body 3.2 x 2.8 mm from **courtyard**, 5 pad(s), side F, pose (122.929, 123.359, 0.0deg)

- **east**: 4 /RXD -> U1
- **north**: 1 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 5 +3V3 (VCC) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U2 U4 U5 U6
- **south**: 3 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U12 U2 U3 U4 U5 U6 U7 U8 U9 Y1
- **west**: 2 /RXD_IN -> R25 SW1

- partners by shared nets: U1 (3), U6 (2), U5 (2), U4 (2), U2 (2), J4 (2), C22 (2), C2 (2)

### U12  --  integrated circuit  (ref_prefix)

`Package_TO_SOT_SMD:SOT-353_SC-70-5`  --  body 3.2 x 2.8 mm from **courtyard**, 5 pad(s), side F, pose (123.619, 123.359, 0.0deg)

- **east**: 4 /TXD_R -> R19
- **north**: 1 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U2 U3 U4 U5 U6 U7 U8 U9 Y1 | 5 Vdrive (VCC) -> C17 C19 C20 C21 R11 R17 R25 U10 U7 U8 U9
- **south**: 3 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U2 U3 U4 U5 U6 U7 U8 U9 Y1
- **west**: 2 /TXD -> U1

- partners by shared nets: U9 (2), U8 (2), U7 (2), U10 (2), U1 (2), C21 (2), C20 (2), C19 (2)

### U2  --  regulator  (footprint)

`Package_TO_SOT_SMD:SOT-23`  --  body 3.4 x 3.5 mm from **courtyard**, 3 pad(s), side F, pose (124.31, 123.359, 0.0deg)

- **east**: 3 +5V (VI) -> C1 FB1
- **north**: 1 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U3 U4 U5 U6 U7 U8 U9 Y1
- **south**: 2 +3V3 (VO) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U4 U5 U6

- partners by shared nets: U6 (2), U5 (2), U4 (2), U11 (2), U1 (2), J4 (2), C22 (2), C2 (2)

### U3  --  integrated circuit  (ref_prefix)

`Package_TO_SOT_SMD:SOT-23-6`  --  body 3.8 x 3.6 mm from **courtyard**, 6 pad(s), side F, pose (125.0, 123.359, 0.0deg)

- **east**: 4 /USB_CC1 (IO3) -> J1 R2 | 5 VBUS (VP) -> FB1 J1
- **north**: 1 /USB_DP (IO1) -> J1 U1 | 6 /USB_DM (IO4) -> J1 U1
- **south**: 3 /USB_CC2 (IO2) -> J1 R1
- **west**: 2 GND (VN) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U4 U5 U6 U7 U8 U9 Y1

- partners by shared nets: J1 (6), U1 (3), R2 (2), R1 (2), Y1 (1), U9 (1), U8 (1), U7 (1)

### U4  --  integrated circuit  (ref_prefix)

`Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`  --  body 7.46 x 5.4 mm from **courtyard**, 8 pad(s), side F, pose (125.69, 123.359, 0.0deg)

- **east**: 5 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U5 U6 U7 U8 U9 Y1 | 6 unconnected-(U4-Pad6) (NC) | 7 unconnected-(U4-Pad7) (NC)
- **north**: 1 /EE_CS (CS) -> R3 U1 | 8 +3V3 (VCC) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U5 U6
- **south**: 4 /EE_DO (DO) -> R5
- **west**: 2 /EE_CLK (SCLK) -> U1 | 3 /EE_DATA (DI) -> R5 U1

- partners by shared nets: U1 (5), U6 (2), U5 (2), U2 (2), U11 (2), R5 (2), R3 (2), J4 (2)

### U5  --  integrated circuit  (ref_prefix)

`Package_TO_SOT_SMD:SOT-353_SC-70-5`  --  body 3.2 x 2.8 mm from **courtyard**, 5 pad(s), side F, pose (126.381, 123.359, 0.0deg)

- **east**: 4 /TDO -> U1 U6
- **north**: 1 /SWD_EN -> R21 R22 U1 U6 U8 U9 | 5 +3V3 (VCC) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U6
- **south**: 3 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U6 U7 U8 U9 Y1
- **west**: 2 /TDO_R -> R15 SW1

- partners by shared nets: U6 (4), U1 (4), U9 (2), U8 (2), U4 (2), U2 (2), U11 (2), R22 (2)

### U6  --  integrated circuit  (ref_prefix)

`Package_TO_SOT_SMD:SOT-353_SC-70-5`  --  body 3.2 x 2.8 mm from **courtyard**, 5 pad(s), side F, pose (127.071, 123.359, 0.0deg)

- **east**: 4 /TDO -> U1 U5
- **north**: 1 /SWD_EN -> R21 R22 U1 U5 U8 U9 | 5 +3V3 (VCC) -> C13 C14 C15 C16 C18 C2 C22 D1 D2 D3 D4 FB2 FB3 J4 R18 R23 R6 U1 U11 U2 U4 U5
- **south**: 3 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U7 U8 U9 Y1
- **west**: 2 /TMS_R -> R14 U10 U9

- partners by shared nets: U5 (4), U1 (4), U9 (3), U8 (2), U4 (2), U2 (2), U11 (2), U10 (2)

### U7  --  integrated circuit  (ref_prefix)

`Package_TO_SOT_SMD:SOT-353_SC-70-5`  --  body 3.2 x 2.8 mm from **courtyard**, 5 pad(s), side F, pose (127.761, 123.359, 0.0deg)

- **east**: 4 /TCK_R -> R13
- **north**: 1 GND -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U8 U9 Y1 | 5 Vdrive (VCC) -> C17 C19 C20 C21 R11 R17 R25 U10 U12 U8 U9
- **south**: 3 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U8 U9 Y1
- **west**: 2 /TCK -> U1

- partners by shared nets: U9 (2), U8 (2), U12 (2), U10 (2), U1 (2), C21 (2), C20 (2), C19 (2)

### U8  --  integrated circuit  (ref_prefix)

`Package_TO_SOT_SMD:SOT-353_SC-70-5`  --  body 3.2 x 2.8 mm from **courtyard**, 5 pad(s), side F, pose (122.239, 123.973, 0.0deg)

- **east**: 4 /TDI_R -> R16
- **north**: 1 /SWD_EN -> R21 R22 U1 U5 U6 U9 | 5 Vdrive (VCC) -> C17 C19 C20 C21 R11 R17 R25 U10 U12 U7 U9
- **south**: 3 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U9 Y1
- **west**: 2 /TDI -> U1 U10

- partners by shared nets: U9 (3), U10 (3), U1 (3), U7 (2), U6 (2), U5 (2), U12 (2), R22 (2)

### U9  --  integrated circuit  (ref_prefix)

`Package_TO_SOT_SMD:SOT-353_SC-70-5`  --  body 3.2 x 2.8 mm from **courtyard**, 5 pad(s), side F, pose (122.929, 123.973, 0.0deg)

- **east**: 4 /TMS_R -> R14 U10 U6
- **north**: 1 /SWD_EN -> R21 R22 U1 U5 U6 U8 | 5 Vdrive (VCC) -> C17 C19 C20 C21 R11 R17 R25 U10 U12 U7 U8
- **south**: 3 GND (GND) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 Y1
- **west**: 2 /TMS -> U1

- partners by shared nets: U8 (3), U6 (3), U10 (3), U1 (3), U7 (2), U5 (2), U12 (2), R22 (2)

### Y1  --  crystal  (footprint)

`Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm`  --  body 4.2 x 3.4 mm from **courtyard**, 4 pad(s), side F, pose (123.619, 123.973, 0.0deg)

- **east**: 2 GND (2) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9
- **north**: 3 /OSCO (3) -> C4 U1 | 4 GND (4) -> C1 C10 C11 C12 C13 C14 C15 C16 C17 C18 C19 C2 C20 C21 C22 C3 C4 C5 C6 C7 C8 C9 D5 D6 J1 J2 J4 Q1 R1 R2 R22 R24 R3 R4 SW2 U1 U10 U11 U12 U2 U3 U4 U5 U6 U7 U8 U9
- **south**: 1 /OSCI (1) -> C3 U1

- partners by shared nets: U1 (3), C4 (2), C3 (2), U9 (1), U8 (1), U7 (1), U6 (1), U5 (1)

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


Evidence-backed follow-up, 2026-09-13. [Public research bundle](https://github.com/edgehero/KiCadRoutingTools/tree/research/astra-placement-evidence-20260913/wk/astra-evidence) — scripts, measured results, controls, and limitations. Production code under test: `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`.

### Evidence update: the geometry basis must be explicit before constraining placement

Reproduced on upstream `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`, Windows / KiCad 10.0.0 / Python 3.11.5 / NumPy 2.4.2, using real `kicad_files/esp_prog.kicad_pcb` geometry. Input SHA256: `165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`.

The board's outline bounds are `(114.0,91.0,145.75,105.5)`. Original USB1 has its **drawn fab body flush with the west edge**, while the rect consumed by the overhang rule is `(115.6,95.8,121.62,104.2)`: a pad-box fallback, 1.60 mm inboard. I translated this actual footprint, preserving its geometry, and ran the real `floorplan.grade` with explicit edge intent. This is a controlled geometry test, not a recommendation to place the connector at the bad poses.

| USB1 translation X | Pad-box west gap | Drawn fab-body west overhang | Rule amount, margin .25 | Rule amount, margin .55 |
|---|---:|---:|---:|---:|
| 0 mm (control) | +1.60 mm | 0.00 mm | 0.00 mm | 0.00 mm |
| −1.45 mm | +0.15 mm | 1.45 mm | **0.10 mm** | **0.40 mm** |
| −2.10 mm | −0.50 mm | 2.10 mm | **0.75 mm** | **1.05 mm** |

The **same** `−1.45` board satisfies an explicit `overhang_mm: {min:0.05,max:0.20}` clause at margin .25 and violates it at margin .55. This stronger positive-minimum control avoids relying only on a band starting at zero: the verdict changes with clearance while physical geometry stays identical. Its original `{min:0,max:0.65}` clause also produces no overhang violation despite 1.45 mm of drawn-body overhang.

On the `−1.45` variant, `check_drc --check-pad-edge --board-edge-clearance 0.25 --clearance-margin 0` independently reports **two USB1 pad-board-edge violations, each 0.100 mm**. It also reports five pad-pad violations introduced by this controlled translation; this is not a claim that the variant is otherwise clean. The unchanged control has no DRC violations under the same command. The lower-level pad-legality aggregate counts **one footprint** with edge violation, not two pads; those units should remain explicit.

### Two important refinements to the original diagnosis/fix

1. **Passing `board_edge_clearance=0` to the floorplan grader does not remove the margin.** `QuenchState` uses `max(clearance,board_edge_clearance)`, so the test still had effective margin .25 with clearance .25. A directly constructed zero-margin `BoardOutlineGate` reads 0.00 for the +.15-mm pad gap and .50 for the .50-mm pad overhang, confirming the intended minimal arithmetic control. Log requested **and effective** margins.
2. **Zero margin fixes the currency only for the rect actually measured; it does not fix the body/pad mismatch.** On this real footprint, pad copper and mating body differ by 1.60 mm. A zero-margin pad-box measurement would still report zero when the body overhangs 1.45 mm. For nonrectangular outlines the current `rect_outside_amount` also sums several boundary-violation terms, so it should not be renamed to physical overhang without a defined geometry contract.

Relevant current code: [the overhang conjunct](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_placer/placement/floorplan.py#L2640), [the subsequent body-based seating conjunct](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_placer/placement/floorplan.py#L2660), [the effective-margin clamp](https://github.com/drandyhaas/KiCadRoutingTools/blob/5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3/py_placer/placement/quench.py#L788).

### Placement interface that enhances model decisions

Expose independent measurements with their bases and requirement sources:

```json
{
  "ref": "USB1",
  "edge": "west",
  "body_overhang_mm": 1.45,
  "body_overhang_basis": "F.Fab",
  "body_setback_mm": 0.0,
  "pad_copper_edge_gap_mm": 0.15,
  "required_copper_edge_gap_mm": 0.25,
  "copper_edge_shortfall_mm": 0.10
}
```

This is a proposed output contract; current `edge_seating` does not emit those overhang fields. Report signed position relative to the declared mating edge, or clearly distinguish nonnegative overhang from setback. A zero minimum in a nonnegative overhang band is naturally nonbinding; a requirement that a body actually reach the edge belongs in explicit setback/seat intent.

Astra should choose the pose that meets the actual mechanical brief while these instruments report whether it does. Do not invent a universal connector-centering or no-body-overhang requirement: some edge connectors intentionally cross the outline. Conversely, legitimate body overhang does not waive copper clearance. The two channels need independently correct measurements, **not identical pass/fail results**.

### Expanded acceptance

1. The table above is a regression fixture: body overhang does not change when copper/edge-clearance knobs change.
2. Physical body overhang, mating-face setback and copper edge shortfall each carry a basis, units, measured value, declared limit and disposition, on passes as well as failures.
3. An explicit positive minimum overhang fires on a fully inboard body; a zero minimum does not masquerade as a seating requirement.
4. F.Fab, supported F.Silk fallback, missing body geometry, rotated connectors, concave outlines and cutouts are explicit cases. Missing/ambiguous body or mating-edge geometry returns unmeasured rather than using an undisclosed pad box.
5. A declared legal body overhang is allowed while off-board copper or insufficient copper clearance is reported independently. Candidate exploration can retain the measurements without promoting an invalid final board.
6. Apply the same geometry contract to `oob_exempt()` and intent emitters, so correction of the grader does not leave a mismatched exemption or prefilled band behind.

Evidence artifacts: `pose_geometry/reproduce.py`, `run-20260913-222129/results.json`, the three USB board variants and their DRC JSON/logs. No production edits; input preserved. The simple rectangular fixture establishes the bug and currency mismatch, not correctness for arbitrary connector mechanics or all board outlines.

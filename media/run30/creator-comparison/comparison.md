# Run 30 versus the actual OLIMEX ESP-PROG Rev. C

The creator's routing is more economical and is the stronger production starting point. Run 30 improves selected placement targets and current-tool checks, but is not an overall improvement or a demonstrated drop-in replacement.

## Correct reference

[Original OLIMEX source](https://github.com/OLIMEX/ESP-PROG/blob/8dfb3bb217bd9967871e181cad9a7f7fb1343ac5/HARDWARE/ESP-PROG-Rev.C/ESP-PROG_Rev.C.kicad_pcb), commit `8dfb3bb217bd9967871e181cad9a7f7fb1343ac5`, downloaded without changes; SHA-256 `5bf2ac43c912bfe089efb79cd9c2a15c45c6c2723aead188453499424030fc12`. The earlier run-folder reference has identical footprint poses and pad/net memberships, but zero routed tracks, a simplified rectangular outline, and none of the original's 20 board-level text objects. It was only a placement reference. The genuine source has 204 tracks and 19 vias.

The legacy KiCad 5 file was upgraded on a separate copy using KiCad 10. The KRT parser falsely reads the raw legacy file as empty, so its raw-file scores were discarded. Native KiCad reads the raw source with zero opens; native metrics below use the converted copy. Neither the downloaded source nor our final PCB was modified.

## Measurements

| Measure | OLIMEX original | Run 30 | Interpretation |
|---|---:|---:|---|
| Native unconnected items | 0 | 0 | Both connect the nets |
| Vias | 19 | 39 | Original has 20 fewer |
| Signal vias, excluding GND/3V3/VBUS | 6 | 21 | Original needs fewer layer changes |
| Track length, all nets | 299.265 mm | 375.863 mm | Ours is 25.6% longer |
| Signal-only track length, excluding GND/3V3/VBUS | 179.269 mm | 173.072 mm | Ours is 3.5% shorter |
| Ground track length | 44.852 mm | 99.064 mm | Much of the extra length is ground interconnect; neither figure counts plane area |
| VBUS track length | 23.944 mm | 46.202 mm | Original has a substantially shorter supply route |
| USB D+ / D- track length | 9.276 / 10.130 mm | 8.365 / 8.669 mm | Ours is shorter and better matched geometrically |
| USB pair vias | 0 | 4 | Original keeps the pair on one layer |
| USB length difference | 0.854 mm | 0.304 mm | No impedance or matching target was certified |
| Two crystal-net total track length | 15.686 mm | 12.886 mm | Ours is 17.9% shorter; both have zero crystal vias |
| Minimum track width | 0.2032 mm | 0.127 mm | Original has more etching margin |
| Via drill range | 0.6096 mm | 0.20-0.30 mm | Original uses larger, easier-to-drill holes |
| Worst declared crystal pad-edge gap | 4.7425 mm | 2.4668 mm | Ours meets the newly supplied 2.5 mm target |
| Input cap C1 to U2 pad-edge gap | 4.4111 mm | 1.9946 mm | Ours meets the newly supplied 2 mm target |
| Output cap C3 to U2 pad-edge gap | 1.1220 mm | 1.4403 mm | Original is closer; both meet 2 mm |

The original has 0.8/0.6096 mm vias with only 0.0952 mm annular ring on four vias; its larger holes therefore do not imply better annular-ring margin. Our smallest via is 0.45/0.20 mm, with 0.125 mm ring. Placement distances are geometry proxies, not measured signal integrity or regulator stability.

## Why the original is better in several practical respects

The original routes the USB pair entirely on F.Cu with 0.2032 mm tracks. Our rotation of U1 shortens its straight-line distance to USB but introduces a four-via crossover. The modest length/matching improvement does not establish superior USB performance; the original's simpler path is preferable on this evidence. Our total signal copper is slightly shorter, but the original needs far fewer signal transitions, and its power distribution is more direct. Ground meshes differ, so total trace length alone is not a complete electrical-quality metric.

The original retains connector pin legends, board identity and revision. Our prepared input had already lost those board-level text objects. The original has 36 silk-over-copper and 17 silk-overlap warnings, versus our 55 and 19: our silkscreen is not an improvement. Our tight 0.290 mm U1/Y1 seam remains a rework limitation. The original's apparent R1/U2 overlap comes from mixed fab/silk envelopes and is insufficient evidence of a real body collision.

## Why ours is better on specific requirements

Our USB centering offset is -0.70 mm versus the original's +1.75 mm, so ours satisfies the new +/-1 mm centering requirement. Its crystal and regulator input-cap geometry meet the supplied proximity targets; its crystal net total length is smaller. These are worthwhile layout gains, but were not the original creator's documented acceptance criteria. All six quality claims pass on ours; some individual original gaps, such as C3/U2, remain smaller.

Our U2 tab has an explicit VBUS pad association. This eliminates legacy netless-artwork DRC ambiguity and passes native DRC with the current project. We did not demonstrate functional superiority through hardware tests, impedance simulation, EMI testing, or production yield.

## Mechanical and cable differences

Although both have 31.75 x 14.5 mm outer bounds, the original perimeter has eight edges with a 1 mm recess at USB; the supplied run input and our output have four rectangular edges. We preserved the supplied outline, not the exact manufacturer's perimeter. CON1 and CON2 are each rotated 180 degrees relative to the creator's board. Logical pad/net assignments are preserved, but physical pin-1 and ribbon exit/orientation differ. Cable and mechanical compatibility need checking before treating ours as a replacement.

## DRC comparison and its limits

With the same global project settings copied onto separate analysis boards, KiCad 10 reports original **14 errors / 100 warnings / 0 opens** and ours **0 errors / 105 warnings / 0 opens**. Original local pad/zone settings remain in place. The 14 errors are five netless U2-tab contacts, two related mask bridges, four undersized annular rings, two DTR/tab gaps of 0.1381 mm against 0.15 mm, and one saved-fill clearance of 0.3025 mm against the zone's 0.3048 mm setting. The tab contacts are representation defects, not proof of five functional shorts. Legacy fill conversion was approximate and no refill was performed for the source measurement.

The unmodified source opened with KiCad defaults reports 33 errors: 19 extra edge-clearance findings come from a 0.5 mm modern default, and disappear with our 0.25 mm global edge rule. That larger count is not used to rank boards. The project's KRT check finds four original issues; two are the DTR/tab clearance, one a tab contact, and one a same-net soft-joint classification despite native zero opens. Neither modern-import counts nor the new intent score establish that the shipped OLIMEX product is faulty.

Recommendation: use the creator's compact, wider-trace, low-via routing as the baseline; carry over our explicit tab-net representation and useful crystal/input-cap placement improvements, while preserving or deliberately revalidating connector orientation, USB recess and readable pin legends. Run 30 demonstrates successful intent-driven construction from a pile, not that the automation beat the original designer overall.

Evidence: `native_metrics.json`, `original_native_drc.json`, `same_rules/creator_native.json`, `same_rules/ours_native.json`, `original_converted_score.json`, `original_krt_drc.json`, and the native front/back preview.

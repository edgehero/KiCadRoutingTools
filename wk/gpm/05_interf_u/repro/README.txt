Repro inputs for TOOL_GAPS.md (run every command from the WT root, ~/Documents/git/krt-gpm).
- vcc_finger_walled.kicad_pcb (+ .kicad_pro): a routed board (arm C, via cost 600, + 2 iterations) whose only open
  is VCC at BUS1 pad 3 (the B.Cu +5V edge finger, 164.47,138.43), walled on B.Cu by /PC-RST's track at y=134.2.
- interf_u_pile.kicad_pcb (+ .kicad_pro): the input pile, for the analyze_power_paths repro (power_double_count.py).
- placed_seed1.kicad_pcb (+ .kicad_pro): the kept placement (final.kicad_pcb), for the escalation-default and judge repros.
- placed_seed11.kicad_pcb (+ .kicad_pro): pass-1 seed 11, for the judge-vs-full-route repro.

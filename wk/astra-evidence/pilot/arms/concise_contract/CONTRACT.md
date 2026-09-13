Use the repository as a tool library. Choose
the arrangement yourself; use py_tools/board_context.py to inspect component
roles, pad functions and partners. py_placer/place_pose.py accepts set/rotate
verbs, including several parts in a single arrangement; --near enables bounded
legalization. Read its --help. Apply exact poses with that sanctioned tool.
Inspect renders using py_tools/render_placement.py and image viewing. Check
py_router/check_drc.py and py_tools/check_assembly.py, supplying the original
arm board as assembly baseline. Use py_tools/check_floorplan.py to compile and
grade the explicit design brief. Carry the brief to each candidate. Measurements
propose/validate changes; choose your own sequence. An inherited defect is not
proof that every candidate is invalid, and a no-worse tool verdict is not proof
that the final board is clean. Keep failed proposals as logged experiments;
never promote one that breaks a declared requirement. Report coverage gaps.
Do not load the three plan-pcb-* SKILL.md files or their drivers in this arm.

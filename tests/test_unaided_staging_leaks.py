#!/usr/bin/env python3
"""What `--kind pile` hands over, and what the fence can see of it.

`perturb.py:368-382` says of the pile kind: "This kind exists to produce the
place-from-scratch task, and that needs the whole board." It hands over the
whole board and a third of the answer:

  * every free part keeps its ORIGINAL ROTATION (`:389-391` writes
    `'new_rotation': state.parts[r].rot`), and
  * every part that is not "free" -- `portfolio.free_refs` skips pad-less
    footprints and every `(locked yes)` ref -- keeps its true x, y AND
    rotation.

And `fence_audit` cannot see any of it. `pose_match` counts a ref only when
position AND rotation are both inside tolerance, so on a pile every position
is off by tens of millimetres, `match_frac` is ~0, and the verdict is CLEAN
while 100% of the rotations are correct. Run 19's fence exited CLEAN, 0.

This file pins BOTH halves: what the staging leaks, and that the leak
detector is blind to it. `stage_unaided` is the answer, and the assertions
at the bottom hold it to a higher bar than `--kind pile` on the same board --
so if anyone ever "simplifies" the unaided stager back onto the pile kind,
this fails.
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO,):
    if p not in sys.path:
        sys.path.insert(0, p)
        sys.path.insert(0, os.path.join(p, 'py_router'))
        sys.path.insert(0, os.path.join(p, 'py_tools'))
        sys.path.insert(0, os.path.join(p, 'py_placer'))
        sys.path.insert(0, os.path.join(p, 'tests', 'stress'))

BOARD = os.path.join(REPO, 'kicad_files', 'splitflap_driver.kicad_pcb')

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")


if not os.path.isfile(BOARD):
    print("SKIP: fixture missing")
    sys.exit(0)

from kicad_parser import parse_kicad_pcb
from placement import perturb as P

orig = parse_kicad_pcb(BOARD)
orig_pose = {r: (round(f.x, 4), round(f.y, 4), round(f.rotation or 0.0, 4))
             for r, f in orig.footprints.items()}


def same_angle(a, b):
    """Rotations are equal MODULO 360. The writer normalises -90 to 270, and
    comparing raw floats reports seven of this board's parts as "changed"
    when nothing about their orientation moved -- which understates the leak
    from 100% to 89%."""
    return abs(((a - b) + 180.0) % 360.0 - 180.0) < 1e-6


def stage(fn, **kw):
    d = tempfile.mkdtemp()
    out = os.path.join(d, 'staged.kicad_pcb')
    fn(out, **kw)
    st = parse_kicad_pcb(out)
    return out, {r: (round(f.x, 4), round(f.y, 4), round(f.rotation or 0.0, 4))
                 for r, f in st.footprints.items()}


# --------------------------------------------------------------------------
# What --kind pile leaks
# --------------------------------------------------------------------------
def _pile(out):
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        P.perturb(BOARD, out, kind='pile', dose_mm=40.0, seed=7,
                  control_out=os.path.join(os.path.dirname(out), 'ctl.kicad_pcb'))


pile_path, pile = stage(_pile)

same_rot = [r for r in pile
            if r in orig_pose and same_angle(pile[r][2], orig_pose[r][2])]
check("--kind pile preserves EVERY part's rotation",
      len(same_rot) == len(pile),
      f"{len(same_rot)} of {len(pile)} kept their original angle")

# A part at rotation 0 leaks nothing by keeping it. The informative subset is
# the parts whose angle was a DECISION.
informative = [r for r in same_rot if orig_pose[r][2] % 360.0 != 0.0]
check("and for many of them that angle was a decision, not a default",
      len(informative) > 0,
      f"{len(informative)} of {len(pile)} parts kept a NON-ZERO angle: "
      f"{sorted(informative)[:6]}")

# Pad-less and (locked yes) refs are not piled at all -- portfolio.free_refs
# skips them -- so they keep x, y AND rotation. This board has none, which is
# why the count is reported rather than asserted: the leak is real on boards
# that do (run 19's urchin), and a fixture without one must not manufacture
# a pass OR a failure.
same_all = [r for r in pile if r in orig_pose and pile[r] == orig_pose[r]]
print(f"       NOTE {len(same_all)} part(s) keep their FULL pose on this "
      f"fixture (pad-less / locked refs are never piled); urchin has "
      f"several")

# --------------------------------------------------------------------------
# ...and the fence cannot see it
# --------------------------------------------------------------------------
import fence_audit as FA

frac, shared, worst = FA.pose_match(pile, orig_pose)
check("fence_audit's pose_match scores the pile at ~0", frac < 0.02,
      f"match_frac {frac:.4f} over {shared} shared refs")
check("so a pile is CLEAN to the fence while every rotation is correct",
      frac < FA.MATCH_FRAC and len(same_rot) == len(pile),
      f"match_frac {frac:.4f} < MATCH_FRAC {FA.MATCH_FRAC}, "
      f"rotations preserved {len(same_rot)}/{len(pile)}")

# The rotation-only match rate is the number the fence never computes.
rot_frac = len(same_rot) / max(1, len(pile))
check("the rotation-only match rate is the blind spot, and it is 100%",
      rot_frac > 0.99, f"{rot_frac:.2%}")
check("nothing in fence_audit computes that rate",
      not any('rot' in n and 'frac' in n.lower()
              for n in dir(FA)),
      "if a rotation-only measure appears, this blind spot is closed")

# --------------------------------------------------------------------------
# stage_unaided must do strictly better on both counts
# --------------------------------------------------------------------------
try:
    import stage_unaided as SU
except ImportError as e:
    check("stage_unaided exists", False, str(e))
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


def _unaided(out):
    SU.stage(BOARD, out, truth_dir=os.path.join(os.path.dirname(out),
                                                '_truth'))


un_path, un = stage(_unaided)
mech = SU.read_mechanical(os.path.join(os.path.dirname(un_path),
                                       'mechanical.json'))
exempt = set(mech.get('refs') or {})

leaked_rot = [r for r in un
              if r not in exempt and r in orig_pose
              and same_angle(un[r][2], orig_pose[r][2])
              and orig_pose[r][2] % 360.0 != 0.0]
check("stage_unaided leaks NO rotation except where declared",
      not leaked_rot,
      f"{len(leaked_rot)} undeclared part(s) kept their angle: "
      f"{sorted(leaked_rot)[:6]}")

leaked_pose = [r for r in un
               if r not in exempt and r in orig_pose and un[r] == orig_pose[r]]
check("and no undeclared part keeps its full pose", not leaked_pose,
      f"{sorted(leaked_pose)[:6]}")

check("every exemption is DECLARED, per ref, with its pose",
      exempt and all(len(v) == 3 for v in (mech.get('refs') or {}).values()),
      f"{len(exempt)} declared: {sorted(exempt)[:6]}")
check("the declaration says WHY each ref is exempt",
      all(r in (mech.get('reasons') or {}) for r in exempt),
      str(sorted(set(exempt) - set(mech.get('reasons') or {}))[:6]))

# The whole point: strictly better than the kind it replaces.
check("stage_unaided leaks strictly less rotation than --kind pile",
      len(leaked_rot) < len(informative),
      f"unaided {len(leaked_rot)} vs pile {len(informative)} informative")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)

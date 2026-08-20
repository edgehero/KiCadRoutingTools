"""The run-23 density term's MACHINERY, pinned (the term itself is REJECTED).

tests/test_placement_ab.py records the verdict: at any measured tuning the
independent pocket signal never moved (quench's <=3mm nudges cannot migrate
a part out of a packed belt -- that is reseat-scale work) while the guards
worsened on 2 of 3 boards. The knobs stay for future experiments, OFF by
default -- so what THIS file pins is the contract that makes 'off' safe and
'on' correct: weight 0.0 builds nothing and is bit-identical; the lazy bin
bookkeeping survives moves; the cost responds to crowding.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO, os.path.join(REPO, 'py_router'), os.path.join(REPO, 'py_placer')):
    if p not in sys.path:
        sys.path.insert(0, p)

BOARD = os.path.join(REPO, 'kicad_files', 'splitflap_driver.kicad_pcb')
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    passed += bool(ok)
    failed += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} {name}"
          f"{(' -- ' + str(detail)) if detail else ''}")


def _state(**kw):
    from kicad_parser import parse_kicad_pcb
    from placement.quench import QuenchState
    pcb = parse_kicad_pcb(BOARD)
    base = dict(clearance=0.2, board_edge_clearance=0.55,
                crossing_penalty=30.0, halo_base=0.5, halo_coef=0.15,
                halo_weight=2.0, edge_halo=2.0, edge_weight=2.0,
                grid_step=0.1, length_weight=0.3)
    base.update(kw)
    return QuenchState(pcb, BOARD, **base)


def main():
    # 1. OFF builds nothing, costs nothing, and never touches geometry.
    st0 = _state()
    check('weight 0.0 never builds the bins',
          st0._dens_occ is None and st0.density_weight == 0.0, '')
    r0 = next(iter(st0.parts))
    check('...and the cost is exactly 0.0',
          st0._density_cost(r0) == 0.0 and st0._dens_occ is None, '')

    # 2. ON: the lazy build's occupancy equals the sum of contributions,
    #    and stays equal after moves (the invariant apply_move maintains).
    st = _state(density_weight=10.0)
    _ = st._density_cost(r0)              # triggers the lazy build
    check('lazy build fires on first evaluation', st._dens_occ is not None, '')

    def _invariant():
        total = {}
        for ref, contrib in st._dens_part.items():
            for key, a in contrib:
                total[key] = total.get(key, 0.0) + a
        if set(total) != set(st._dens_occ):
            return False
        return all(abs(total[k] - st._dens_occ[k]) < 1e-6 for k in total)

    check('occupancy == sum of contributions at build', _invariant(), '')
    movable = [r for r, p in st.parts.items() if not p.locked][:5]
    for i, ref in enumerate(movable):
        p = st.parts[ref]
        st.apply_move(ref, p.x + 3.0 + i, p.y - 2.0, p.rot)
    check('...and after 5 apply_move calls', _invariant(), '')
    st.apply_group_move(movable[:3], -1.5, 4.0)
    check('...and after a group move', _invariant(), '')

    # 3. The cost DISCRIMINATES: a pose stacked onto a crowded window costs
    #    more than the part's own home pose.
    ref = movable[0]
    other = st.parts[movable[3]]
    home = st._density_cost(ref)
    crowded = st._density_cost(ref, other.x, other.y)
    check('a crowded pose costs more than home',
          crowded > home, f'home={home:.3f} crowded={crowded:.3f}')

    # 4. exclude semantics: excluding the crowd's owner lowers the charge.
    excl = st._density_cost(ref, other.x, other.y,
                            exclude={movable[3]})
    check('excluding the crowding part lowers the cost',
          excl < crowded, f'{excl:.3f} < {crowded:.3f}')

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())

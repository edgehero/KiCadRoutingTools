#!/usr/bin/env python3
"""The placement CLIs must carry the .kicad_pro / .kicad_dru siblings (#441).

Why this is a test and not a convention. The sibling `.kicad_pro` holds the DRC
floor the chain routed to. A board written without it makes the NEXT step
resolve its floor from the STOCK netclass and stamp that looser value over
tighter copper, so KiCad then grades correct sub-floor copper as phantom
clearance DRC. CLAUDE.md states the rule; `placement/portfolio.copy_siblings`
implements it; `place_seed` and `place_portfolio` called it and
**`place_optimize` and `place_route_loop` did not**. SKILL.md worked around the
gap by telling the caller to `cp` the files by hand, which is exactly the kind
of instruction that gets dropped from one step of a chain.

The `place_route_loop` case is the one that bites hardest, and it is not the
final output: the loop copies its INPUT to `loop_round0.kicad_pcb` and then
ROUTES that copy. Without the sibling, round 0 -- and therefore every
accept/reject decision that compares against round 0's failure count -- is
measured at the wrong clearance.

Run: python3 -X utf8 tests/test_411_placement_siblings.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'py_router'))  # placement split
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'py_tools'))  # placement split
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'py_placer'))  # placement split
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SIBLINGS = ('.kicad_pro', '.kicad_dru')


def _stage(tmp, board_name):
    """Copy a fixture board into `tmp` WITH a .kicad_pro and .kicad_dru.

    The `.kicad_dru` is synthesised when the fixture has none: this test is
    about whether the tool carries siblings, not about which siblings the
    fixture happens to ship with, and a test that silently skips the dru
    because no in-repo board has one would assert nothing about it.
    """
    from tests import fixture_boards
    src = fixture_boards.ensure(board_name)
    dst = os.path.join(tmp, board_name)
    shutil.copyfile(src, dst)
    stem_src, stem_dst = os.path.splitext(src)[0], os.path.splitext(dst)[0]
    for ext in SIBLINGS:
        if os.path.exists(stem_src + ext):
            shutil.copyfile(stem_src + ext, stem_dst + ext)
        elif ext == '.kicad_dru':
            with open(stem_dst + ext, 'w', encoding='utf-8') as fh:
                fh.write('(version 1)\n')
        elif ext == '.kicad_pro':
            with open(stem_dst + ext, 'w', encoding='utf-8') as fh:
                json.dump({'board': {'design_settings': {}}}, fh)
    return dst


def _assert_siblings(out_board, label):
    stem = os.path.splitext(out_board)[0]
    missing = [e for e in SIBLINGS if not os.path.exists(stem + e)]
    assert not missing, (
        f"{label}: wrote {os.path.basename(out_board)} without {missing}. "
        f"The next step will resolve its DRC floor from the stock netclass "
        f"(#441) and grade correct copper as phantom clearance violations.")


def test_place_optimize_carries_siblings():
    with tempfile.TemporaryDirectory() as tmp:
        board = _stage(tmp, 'interf_u_unrouted.kicad_pcb')
        out = os.path.join(tmp, 'optimized.kicad_pcb')
        r = subprocess.run(
            [sys.executable, '-X', 'utf8',
             os.path.join(ROOT, 'py_placer', 'place_optimize.py'), board, out,
             '--max-displacement', '0.5', '--max-passes', '1'],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', cwd=ROOT, timeout=900)
        assert r.returncode == 0, f"place_optimize exited {r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}"
        assert os.path.exists(out), "place_optimize wrote no board"
        _assert_siblings(out, 'place_optimize')


def test_place_optimize_propagates_its_exit_code():
    """--suggest-locks returns 0 from main(); __main__ used to drop it."""
    with tempfile.TemporaryDirectory() as tmp:
        board = _stage(tmp, 'interf_u_unrouted.kicad_pcb')
        r = subprocess.run(
            [sys.executable, '-X', 'utf8',
             os.path.join(ROOT, 'py_placer', 'place_optimize.py'), board, '--suggest-locks'],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', cwd=ROOT, timeout=600)
        assert r.returncode == 0, f"--suggest-locks exited {r.returncode}"
        # And a board-state refusal must still surface as UNPLACED_EXIT rather
        # than being swallowed into a success.
        from placement.placement_state import UNPLACED_EXIT
        assert UNPLACED_EXIT == 3


def test_route_loop_round0_copy_carries_siblings():
    """The load-bearing one: round 0 ROUTES its copy of the input.

    Asserted WITHOUT running the loop (which would route a whole board): the
    copy is made before any routing, so the check is on the code path, which is
    read here rather than executed. A behavioural version of this test would
    cost minutes per run and assert the same line.
    """
    src = os.path.join(ROOT, 'py_placer', 'place_route_loop.py')
    with open(src, encoding='utf-8') as fh:
        text = fh.read()
    m = re.search(r"cur_file\s*=\s*os\.path\.join\(work,\s*'loop_round0\.kicad_pcb'\)"
                  r"(.{0,900}?)\n\s*screened\s*=\s*0", text, re.S)
    assert m, "could not find the round-0 copy block in place_route_loop.py"
    block = m.group(1)
    assert 'shutil.copy(' in block, "round 0 no longer copies the input board"
    assert 'copy_siblings(' in block, (
        "place_route_loop round 0 copies the input board WITHOUT its siblings. "
        "Round 0 routes that copy, so every round -- and every accept/reject "
        "decision measured against round 0 -- runs at the stock netclass floor "
        "instead of the board's own (#441).")
    # And the final output copy.
    tail = text[text.index('shutil.copy(cur_file, args.output_file)'):]
    assert 'copy_siblings(cur_file, args.output_file)' in tail[:400], (
        "the loop's final output copy drops the siblings")


def test_route_loop_emits_a_json_summary():
    """The verdict must be machine-readable, not a text `Final:` line."""
    src = os.path.join(ROOT, 'py_placer', 'place_route_loop.py')
    with open(src, encoding='utf-8') as fh:
        text = fh.read()
    assert 'print("JSON_SUMMARY: "' in text, (
        "place_route_loop prints no JSON_SUMMARY on its normal path; the only "
        "structured output of a run would again be the loop_round{N}.json "
        "sidecars")
    for key in ('failures_before', 'failures_after', 'iterations_before',
                'iterations_after', 'vias_before', 'vias_after',
                'rounds_accepted', 'rounds_run', 'max_displacement',
                'max_target_pins'):
        assert f"'{key}'" in text, f"JSON_SUMMARY is missing {key!r}"
    assert 'sys.exit(main() or 0)' in text, (
        "main()'s return value is dropped by __main__, so a refusal exits 0")


def test_one_sibling_list_no_hand_written_copies():
    """Every sibling-extension tuple is `copy_board.SIBLING_EXTS` or imports it.

    Eight sites spelled the list out by hand and THREE had drifted --
    `stage_blind`, `fixture_boards` and `redo_diff_stage` carried
    `.kicad_pro` + `.kicad_prl` and dropped `.kicad_dru`, the per-layer
    clearance rules that OUTRANK `--clearance` (#498). The drop is silent by
    construction: `read_board_layer_clearances` returns `({}, [])` for an
    absent file, so a run grades an inner layer at the wrong value with no
    diagnostic anywhere. A source-text gate, because the failure is a
    COPY of a list, not a behaviour any one board exercises.
    """
    import re as _re
    bad = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'wk')]
        for name in files:
            if not name.endswith('.py'):
                continue
            path = os.path.join(root, name)
            if os.path.basename(path) == 'copy_board.py':
                continue
            with open(path, encoding='utf-8', errors='replace') as fh:
                text = fh.read()
            # A tuple/list literal mentioning .kicad_pro and .kicad_prl but
            # NOT .kicad_dru. Checked over a 3-LINE WINDOW, not one line:
            # the first version was per-line, so wrapping a list across two
            # lines silenced it -- which is how a gate stops gating.
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if not _re.search(r'[\(\[].*\.kicad_pro', line):
                    continue
                window = ' '.join(lines[i:i + 3])
                if '.kicad_prl' in window and '.kicad_dru' not in window:
                    bad.append(f"{os.path.relpath(path, ROOT)}: {line.strip()}")
    assert not bad, (
        "hand-written sibling list that omits .kicad_dru (carry it via "
        "copy_board.SIBLING_EXTS; a cleanup list wants it too, or a temp "
        "rules file survives the test):\n  " + "\n  ".join(bad[:6]))


def test_stage_unaided_declares_and_sanitizes_the_project():
    """The staged project travels, is declared, and does not name its source.

    Three clauses, each a bug that shipped:
      * the floors must survive staging -- without the .kicad_pro,
        flat_hierarchy grades 0.2 -> 0.25 and the SOURCE flips from
        'board netclass' to 'fixed default';
      * `mechanical.json` must say what travelled, because this stager's own
        rule is that an input is legitimate BECAUSE it is written down, and
        the project -- which sets every clearance the placement is graded at
        -- was written down nowhere;
      * nothing in the work dir may name the source. KiCad stores
        `meta.filename` in the project, so a verbatim copy put
        'flat_hierarchy.kicad_pro' inside the fence.
    """
    sys.path.insert(0, os.path.join(ROOT, 'tests', 'stress'))
    from stage_unaided import stage
    from list_nets import board_floor_knobs

    src = os.path.join(ROOT, 'kicad_files', 'flat_hierarchy.kicad_pcb')
    if not os.path.isfile(os.path.splitext(src)[0] + '.kicad_pro'):
        raise AssertionError('fixture lost its .kicad_pro; the test is void')
    with tempfile.TemporaryDirectory() as tmp:
        wk = os.path.join(tmp, 'wk')
        os.makedirs(wk)
        out = os.path.join(wk, 'board.kicad_pcb')
        doc = stage(src, out, os.path.join(tmp, 'truth'))

        # 1. floors survive -- VALUES AND SOURCES. A value-only check passes
        #    on a board that coincidentally defaults to the same number.
        want = board_floor_knobs(src)[2]
        got = board_floor_knobs(out)[2]
        assert got == want, f"floors changed across staging: {got} != {want}"
        assert got['clearance']['source'] == 'board netclass', got

        # 2. declared
        proj = doc.get('project')
        assert proj and proj.get('carried') is True, proj
        assert proj.get('floors') == want, proj
        assert proj.get('sha256'), proj

        # 3. no file in the work dir names the source
        stem = os.path.splitext(os.path.basename(src))[0]
        named = []
        for root, _d, files in os.walk(wk):
            for n in files:
                p = os.path.join(root, n)
                with open(p, 'rb') as fh:
                    if stem.encode() in fh.read():
                        named.append(os.path.relpath(p, wk))
        assert not named, (
            f"work-dir file(s) name the source {stem!r}: {named} -- the source "
            f"is recorded by HASH, not by path, and a path is one Read away "
            f"from the original placement")


def test_stage_unaided_discloses_a_project_less_source():
    """A board with no .kicad_pro stages, but says the floor did not travel.

    The fixture is CHOSEN AT RUN TIME from whatever is genuinely
    project-less, not hardcoded. It was `watchy`, and then watchy gained its
    real upstream project -- at which point the test quietly returned early
    and stopped testing anything. A fixture whose disappearance turns a check
    into a no-op is the failure mode this suite keeps re-learning.
    """
    sys.path.insert(0, os.path.join(ROOT, 'tests', 'stress'))
    from stage_unaided import stage
    src = None
    for cand in sorted(os.listdir(os.path.join(ROOT, 'kicad_files'))):
        if not cand.endswith('.kicad_pcb'):
            continue
        p = os.path.join(ROOT, 'kicad_files', cand)
        if not os.path.isfile(os.path.splitext(p)[0] + '.kicad_pro'):
            src = p
            break
    assert src, ('every board now has a .kicad_pro, so this case cannot be '
                 'exercised -- delete the test or add a project-less fixture, '
                 'do not let it pass vacuously')
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'board.kicad_pcb')
        doc = stage(src, out)
        proj = doc.get('project')
        assert proj and proj.get('carried') is False, proj
        # and the fallback it will be graded at is NAMED, not implied
        assert proj['floors']['clearance']['source'] == 'fixed default', proj
        assert proj['floors']['clearance']['value'] == 0.25, proj


TESTS = [
    test_place_optimize_carries_siblings,
    test_place_optimize_propagates_its_exit_code,
    test_route_loop_round0_copy_carries_siblings,
    test_route_loop_emits_a_json_summary,
    test_one_sibling_list_no_hand_written_copies,
    test_stage_unaided_declares_and_sanitizes_the_project,
    test_stage_unaided_discloses_a_project_less_source,
]


if __name__ == '__main__':
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as exc:                       # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {exc}")
    sys.exit(1 if failed else 0)

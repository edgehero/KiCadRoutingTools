#!/usr/bin/env python3
"""What a board looks like to something that has to place it, in one artifact.

The placement toolchain already emits every number an author needs -- escape
lane deficits and who ate them, block displacement, net affinity, part classes,
groups, lock advice, the render checklist and the crop that frames each
finding. What it has never had is one place to READ them from, so an author
(human or model) reassembles the picture from a dozen commands every time, or
does not, and places from a guess.

THIS MODULE ASSEMBLES; IT DOES NOT COMPUTE. Every number comes from the
function that already owns it, and `sources` names that function per section,
so there is one source of truth per fact and the brief cannot drift away from
the graders. The one exception is `fit`, which is opt-in and says so: it
answers "where does a W x H part fit at all", the question
`wk/run19/urchin/probe_space.py` was hand-written to answer and whose output
became that run's X0 = 46.0.

Two rules inherited from the evidence map
(.claude/skills/plan-pcb-routing/references/evidence-map.md):

    never read a picture on its own -- every render is paired with a number
    that either confirms or contradicts it, and the number wins

    keys are literal; if a key is not in the output you are looking at, you
    are looking at the wrong artifact

so `renders` is folded in only as a reference to a real `render_placement
--json-out` document, never re-derived here.

A section that cannot run says WHY, in `skipped`, and is absent from the body.
A brief that silently omitted a measurement would read as "nothing to report".

    python3 board_brief.py board.kicad_pcb
    python3 board_brief.py board.kicad_pcb --json brief.json --fit 15.5x15.5
    python3 board_brief.py board.kicad_pcb --requirements "USB on the north
        edge; the two thumb clusters must stay reachable" --render-json r.json

Exit codes: 0 = a brief was written, 2 = usage/load error, 3 = no outline
(there is nothing to place against).
"""
import _path  # noqa: F401  (py_tools -> py_router/py_placer on sys.path)

import argparse
import json
import math
import os
import sys

SCHEMA = 1
DEFAULT_FIT_STEP_MM = 2.0
WORST_N = 10


def _safe(section, fn, skipped, *a, **kw):
    """Run an emitter; record WHY it did not run rather than dropping it."""
    try:
        return fn(*a, **kw)
    except Exception as e:                       # noqa: BLE001 - reported
        skipped[section] = f"{type(e).__name__}: {e}"
        return None


def board_section(pcb, pcb_file, skipped):
    from kicad_parser import parse_kicad_pcb  # noqa: F401  (documents origin)
    bi = pcb.board_info
    out = {
        'path': os.path.abspath(pcb_file),
        'bounds': list(bi.board_bounds) if bi.board_bounds else None,
        'copper_layers': list(getattr(bi, 'copper_layers', []) or []),
        'cutouts': len(getattr(bi, 'board_cutouts', []) or []),
        'outlines': len(getattr(bi, 'board_outlines', []) or []),
        # #505: an interior contour that is a milled edge, not a hole. A part
        # whose pads land inside one is unroutable, and it is invisible to a
        # bounding-box view of the board.
        'milled_contours': len(getattr(bi, 'board_edge_contours', []) or []),
        'stackup': [{'name': l.name, 'type': l.layer_type,
                     'thickness': l.thickness}
                    for l in (getattr(bi, 'stackup', []) or [])],
        'footprints': len(pcb.footprints),
        'nets': len(pcb.nets),
    }
    if out['bounds']:
        x0, y0, x1, y1 = out['bounds']
        out['size_mm'] = [round(x1 - x0, 3), round(y1 - y0, 3)]
        out['area_mm2'] = round((x1 - x0) * (y1 - y0), 2)
    floors = _safe('board.floors', _floors, skipped, pcb_file)
    if floors is not None:
        out['floors'] = floors
    return out


def _floors(pcb_file):
    """The board's own floors, with each value's SOURCE.

    `board_floor_knobs` returns `(clearance, board_edge_clearance, knobs)` --
    a triple, not a mapping. Only `knobs` belongs in the brief: it is the
    part that says whether a number came from the board's netclass, a board
    constraint, or a fixed default, and a reader who cannot tell those apart
    cannot tell a real floor from a guess.
    """
    from list_nets import board_floor_knobs
    return board_floor_knobs(pcb_file)[2]


def state_section(pcb, pcb_file, skipped):
    from placement.placement_state import assess_placement
    st = assess_placement(pcb, pcb_file)
    return {'unplaced': st.unplaced,
            'partially_unplaced': st.partially_unplaced,
            'has_copper': st.has_copper,
            'duplicate_fraction': round(st.duplicate_fraction, 4),
            'spread_ratio': round(st.spread_ratio, 4),
            'outside_fraction': round(st.outside_fraction, 4),
            'stacked_suspect_refs': list(st.stacked_suspect_refs),
            'segments': st.segments, 'vias': st.vias}


def parts_section(pcb, pcb_file, skipped):
    """Per part: what an author needs to decide where it goes.

    Size comes from the courtyard where the footprint has one and the pad
    bounding box where it does not -- and `courtyard` says which, because a
    pad bbox carries NO courtyard margin and treating the two alike is how a
    part gets seated tighter than its own footprint allows (the quench warns
    about this on every board that needs it).
    """
    from placement.parser import extract_courtyard_bboxes
    from placement.part_class import classify_part
    from placement.escape import lane_pitch  # noqa: F401 (documents origin)

    cy = _safe('parts.courtyards', extract_courtyard_bboxes, skipped,
               pcb_file) or {}
    out = {}
    for ref, fp in sorted(pcb.footprints.items()):
        pads = fp.pads or []
        box = cy.get(ref)
        if box:
            w, h = box[2] - box[0], box[3] - box[1]
            src = 'courtyard'
        elif pads:
            xs = [p.global_x for p in pads]
            ys = [p.global_y for p in pads]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            src = 'pad_bbox'
        else:
            w = h = 0.0
            src = 'none'
        cls = classify_part(fp, ref)
        row = {'extent_mm': [round(w, 3), round(h, 3)],
               'extent_source': src,
               'pads': len(pads),
               'side': getattr(fp, 'layer', None),
               'rotation': getattr(fp, 'rotation', None),
               'locked': bool(getattr(fp, 'locked', False)),
               'dnp': bool(getattr(fp, 'dnp', False)),
               'footprint': getattr(fp, 'footprint_name', None),
               'value': getattr(fp, 'value', None),
               'nets': sorted({p.net_name for p in pads
                               if p.net_id and p.net_name})}
        if cls is not None and getattr(cls, 'name', None):
            row['class'] = cls.name
            row['class_confidence'] = getattr(cls, 'confidence', None)
            row['class_evidence'] = list(getattr(cls, 'evidence', ()) or ())
        out[ref] = row
    return out


def structure_section(pcb, pcb_file, skipped):
    """The electrical structure a floorplan thinks in."""
    from placement.groups import AUTO_SOURCES, SOURCES, derive_groups, \
        decap_tethers
    out = {}
    by_source = {}
    for src in SOURCES:
        g = _safe(f'structure.groups.{src}', derive_groups, skipped, pcb,
                  (src,))
        if g:
            by_source[src] = {k: sorted(v) for k, v in sorted(g.items())}
    out['groups'] = by_source
    out['groups_auto_sources'] = list(AUTO_SOURCES)
    teth = _safe('structure.decap_tethers', decap_tethers, skipped, pcb)
    if teth is not None:
        out['decap_tethers'] = {a: [r for r, _d in sorted(v)]
                                for a, v in sorted(teth.items())}

    from list_nets import (find_differential_pairs, find_high_connection_nets,
                           find_power_nets)
    dp = _safe('structure.diff_pairs', find_differential_pairs, skipped, pcb)
    if dp is not None:
        out['diff_pairs'] = _jsonable(dp)
    pw = _safe('structure.power_nets', find_power_nets, skipped, pcb)
    if pw is not None:
        gnd, vcc, cand = pw
        out['power_nets'] = {'gnd': _jsonable(gnd), 'vcc': _jsonable(vcc),
                             'candidates': _jsonable(cand)}
    hi = _safe('structure.top_nets', find_high_connection_nets, skipped, pcb,
               top_n=15)
    if hi is not None:
        out['top_nets'] = _jsonable(hi)
    return out


def _jsonable(v):
    """Emitters return tuples/dataclasses; a brief has to be JSON."""
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [_jsonable(x) for x in (sorted(v) if isinstance(v, set) else v)]
    if hasattr(v, 'to_dict'):
        return _jsonable(v.to_dict())
    if hasattr(v, '_asdict'):
        return _jsonable(v._asdict())
    if isinstance(v, (int, float, str, bool)) or v is None:
        return v
    return str(v)


def measurements_section(pcb, pcb_file, skipped, clearance, edge):
    """The numbers that say a placement will fight the router.

    `escape` is the one that is a BINDING constraint rather than a
    preference: a face short of lanes cannot pass its own nets at any net
    ordering, and `blockers` names which neighbour ate the span -- that field
    is the difference between a signal and an action.
    """
    out = {}
    from placement.escape import escape_ledger
    led = _safe('measurements.escape', escape_ledger, skipped, pcb,
                pcb_file=pcb_file, clearance=clearance)
    if led is not None:
        # `PartEscape` exposes `worst` (a FaceLedger or None) and NO
        # `worst_deficit` attribute -- that name exists only as a key in its
        # to_dict(). A getattr(..., 'worst_deficit', 0) therefore always
        # returns the default, silently reporting every board as having no
        # face in deficit.
        from placement.options import deficit_totals
        tot = deficit_totals(led)
        out['escape'] = {'parts': len(led),
                         'worst': [_jsonable(p) for p in led[:WORST_N]],
                         'deficit_parts': tot['parts'],
                         'deficit_lanes': tot['lanes']}

    from placement.lock_advisor import advise_locks, to_json as lock_json
    adv = _safe('measurements.locks', advise_locks, skipped, pcb,
                pcb_file=pcb_file, conflict_clearance=clearance)
    if adv is not None:
        doc = lock_json(adv)
        # The advisor's own tally() keys, named explicitly. A
        # startswith('findings') filter also matches `findings` itself and
        # embeds the whole per-part findings list -- reasons, evidence and
        # all -- under a key called "tally".
        out['locks'] = {
            'tally': {k: doc[k] for k in
                      ('findings_high', 'findings_medium', 'findings_low',
                       'findings_covered', 'unlocked_high', 'locked_in_file',
                       'advisories') if k in doc},
            'lock_argv': doc.get('lock_argv', []),
            'high': [f['ref'] for f in doc.get('findings', [])
                     if f.get('confidence') == 'high'],
        }
    return out


def fit_section(pcb, pcb_file, extents, step, clearance, edge, skipped):
    """Where does a W x H part fit at all?

    Opt-in and COMPUTED here rather than assembled, which is why it is the
    one section that names its own method. It is the question
    `wk/run19/urchin/probe_space.py` was hand-written to answer, and whose
    answer became that run's X0 = 46.0 and "U1 at (28, 60)" -- authored as
    constants because nothing in the toolchain would say it.

    Reports the legal-centre BOUNDS and count per extent, not a bitmap: an
    author needs to know whether a 15.5mm part has anywhere to go and roughly
    where, and a 60x40 grid of booleans in a JSON brief is unreadable.
    """
    from placement.legality import BoardOutlineGate
    bi = pcb.board_info
    if bi.board_bounds is None:
        skipped['fit'] = 'the board has no outline to fit against'
        return None
    gate = BoardOutlineGate(bi, edge)
    x0, y0, x1, y1 = bi.board_bounds
    out = []
    for (w, h) in extents:
        hw, hh = w / 2.0, h / 2.0
        pts = []
        nx = max(1, int((x1 - x0) / step))
        ny = max(1, int((y1 - y0) / step))
        for i in range(nx + 1):
            for j in range(ny + 1):
                cx = round(x0 + i * step, 3)
                cy = round(y0 + j * step, 3)
                if gate.rect_outside_amount(
                        (cx - hw, cy - hh, cx + hw, cy + hh)) <= 1e-9:
                    pts.append((cx, cy))
        row = {'extent_mm': [w, h], 'step_mm': step, 'legal_cells': len(pts),
               'fits': bool(pts)}
        if pts:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            row['centre_bounds'] = [min(xs), min(ys), max(xs), max(ys)]
        out.append(row)
    return out


SOURCES_NOTE = {
    'board': 'kicad_parser.parse_kicad_pcb + list_nets.board_floor_knobs',
    'state': 'placement.placement_state.assess_placement',
    'parts': 'placement.parser.extract_courtyard_bboxes + '
             'placement.part_class.classify_part',
    'structure': 'placement.groups.derive_groups / decap_tethers + '
                 'list_nets.find_differential_pairs / find_power_nets / '
                 'find_high_connection_nets',
    'measurements': 'placement.escape.escape_ledger + '
                    'placement.lock_advisor.advise_locks',
    'fit': 'placement.legality.BoardOutlineGate.rect_outside_amount '
           '(COMPUTED here, not assembled)',
    'renders': 'py_tools/render_placement.py --json-out (folded in verbatim)',
}


def build_brief(pcb, pcb_file, *, clearance=None, board_edge_clearance=None,
                requirements=None, fit=(), fit_step=DEFAULT_FIT_STEP_MM,
                render_doc=None):
    skipped = {}
    # Board-first: an unset knob resolves from this board's own Default
    # netclass / min_copper_edge_clearance, and the returned `knobs` records
    # which source each came from. `board_floor_knobs` returns a TRIPLE.
    try:
        from list_nets import board_floor_knobs
        clr, edge, _knobs = board_floor_knobs(
            pcb_file, clearance=clearance,
            board_edge_clearance=board_edge_clearance)
    except Exception as e:                       # noqa: BLE001 - disclosed
        clr = 0.25 if clearance is None else clearance
        edge = 0.55 if board_edge_clearance is None else board_edge_clearance
        skipped['floors'] = f"{type(e).__name__}: {e}"

    brief = {'schema': SCHEMA, 'kind': 'board-brief',
             'clearance': clr, 'board_edge_clearance': edge}
    brief['board'] = board_section(pcb, pcb_file, skipped)
    brief['state'] = _safe('state', state_section, skipped, pcb, pcb_file,
                           skipped)
    brief['parts'] = _safe('parts', parts_section, skipped, pcb, pcb_file,
                           skipped)
    brief['structure'] = _safe('structure', structure_section, skipped, pcb,
                               pcb_file, skipped)
    brief['measurements'] = _safe('measurements', measurements_section,
                                  skipped, pcb, pcb_file, skipped, clr, edge)
    if fit:
        f = _safe('fit', fit_section, skipped, pcb, pcb_file, fit, fit_step,
                  clr, edge, skipped)
        if f is not None:
            brief['fit'] = f
    if render_doc is not None:
        # Verbatim, and only the keys the evidence map names -- a brief that
        # paraphrased a checklist would be a second source of truth for the
        # same finding.
        brief['renders'] = {
            'instrument': render_doc.get('instrument'),
            'checklist': render_doc.get('checklist'),
            'panels': render_doc.get('panels'),
            'describe': render_doc.get('describe'),
        }
    if requirements:
        # Verbatim. These are the constraints that live nowhere in the board
        # file -- enclosure fit, connector positions, thermal and EMI zoning,
        # datasheet layout intent -- and paraphrasing them here would be this
        # tool inventing mechanical geometry.
        brief['requirements'] = requirements
    brief['sources'] = SOURCES_NOTE
    brief['skipped'] = skipped
    return brief


def format_text(b):
    L = []
    bd = b.get('board') or {}
    L.append(f"BOARD {os.path.basename(bd.get('path', '?'))}: "
             f"{bd.get('footprints')} parts, {bd.get('nets')} nets, "
             f"{len(bd.get('copper_layers') or [])} copper layers")
    if bd.get('size_mm'):
        L.append(f"  outline {bd['size_mm'][0]} x {bd['size_mm'][1]} mm "
                 f"({bd.get('area_mm2')} mm2), cutouts {bd.get('cutouts')}, "
                 f"milled contours {bd.get('milled_contours')}")
    st = b.get('state') or {}
    if st:
        what = ('UNPLACED' if st.get('unplaced') else
                'partially unplaced' if st.get('partially_unplaced')
                else 'placed')
        copper = 'yes' if st.get('has_copper') else 'no'
        L.append(f"  state: {what}; copper {copper} "
                 f"({st.get('segments')} segs, {st.get('vias')} vias)")
    stx = b.get('structure') or {}
    for src, groups in (stx.get('groups') or {}).items():
        L.append(f"  groups[{src}]: {len(groups)} block(s) "
                 f"{sorted(groups)[:4]}{'...' if len(groups) > 4 else ''}")
    pw = (stx.get('power_nets') or {})
    if pw:
        L.append(f"  power: gnd {pw.get('gnd')}, vcc {pw.get('vcc')}")
    if stx.get('diff_pairs'):
        L.append(f"  diff pairs: {len(stx['diff_pairs'])}")
    ms = b.get('measurements') or {}
    esc = ms.get('escape') or {}
    if esc:
        L.append(f"  escape: {esc.get('parts')} fine-pitch part(s), "
                 f"{esc.get('deficit_parts')} in deficit")
        for row in (esc.get('worst') or [])[:3]:
            L.append(f"    {row.get('ref')}: worst face "
                     f"{row.get('worst_face')} deficit "
                     f"{row.get('worst_deficit')}")
    lk = ms.get('locks') or {}
    if lk:
        t = lk.get('tally') or {}
        L.append(f"  locks: {t.get('unlocked_high', 0)} high-confidence "
                 f"part(s) NOT locked; {t.get('locked_in_file', 0)} already "
                 f"locked in the file")
        if lk.get('lock_argv'):
            L.append(f"    {' '.join(lk['lock_argv'])}")
    for row in (b.get('fit') or []):
        w, h = row['extent_mm']
        if row['fits']:
            cb = row['centre_bounds']
            L.append(f"  fit {w}x{h}mm: {row['legal_cells']} legal centre(s) "
                     f"at {row['step_mm']}mm, x {cb[0]}..{cb[2]}, "
                     f"y {cb[1]}..{cb[3]}")
        else:
            L.append(f"  fit {w}x{h}mm: NOWHERE on this board at "
                     f"{row['step_mm']}mm")
    if b.get('requirements'):
        L.append(f"  requirements (verbatim): {b['requirements']}")
    if b.get('skipped'):
        L.append(f"  {len(b['skipped'])} section(s) did not run:")
        for k, why in sorted(b['skipped'].items()):
            L.append(f"    - {k}: {why}")
    return "\n".join(L)


def _parse_fit(values):
    out = []
    for v in values or ():
        try:
            w, h = v.lower().replace('*', 'x').split('x')
            out.append((float(w), float(h)))
        except ValueError:
            raise SystemExit(f"board_brief: --fit wants WxH in mm, got {v!r}")
    return out


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Assemble what a placement author needs to read.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("board")
    p.add_argument("--json", metavar="PATH", help="Write the full brief here")
    p.add_argument("--clearance", type=float, default=None)
    p.add_argument("--board-edge-clearance", type=float, default=None)
    p.add_argument("--requirements", default=None,
                   help="The constraints that live nowhere in the board file "
                        "(enclosure, connector edges, thermal, EMI). Carried "
                        "VERBATIM")
    p.add_argument("--requirements-file", default=None)
    p.add_argument("--fit", action="append", metavar="WxH",
                   help="Also report where a part of this extent fits at all "
                        "(repeatable)")
    p.add_argument("--fit-step", type=float, default=DEFAULT_FIT_STEP_MM,
                   metavar="MM")
    p.add_argument("--render-json", default=None, metavar="PATH",
                   help="A render_placement --json-out document to fold in")
    p.add_argument("-q", "--quiet", action="store_true")
    a = p.parse_args(argv)

    from kicad_parser import parse_kicad_pcb
    try:
        pcb = parse_kicad_pcb(a.board)
    except Exception as e:                       # noqa: BLE001
        print(f"board_brief: cannot read {a.board}: {e}", file=sys.stderr)
        return 2
    if pcb.board_info.board_bounds is None:
        print("board_brief: this board has no Edge.Cuts outline, so there is "
              "nothing to place against. The outline is spec-owned.",
              file=sys.stderr)
        return 3

    req = a.requirements
    if a.requirements_file:
        try:
            with open(a.requirements_file, encoding='utf-8') as f:
                req = f.read().strip()
        except OSError as e:
            print(f"board_brief: cannot read requirements: {e}",
                  file=sys.stderr)
            return 2

    render_doc = None
    if a.render_json:
        try:
            with open(a.render_json, encoding='utf-8') as f:
                render_doc = json.load(f)
        except (OSError, ValueError) as e:
            print(f"board_brief: cannot read the render doc: {e}",
                  file=sys.stderr)
            return 2

    brief = build_brief(pcb, a.board, clearance=a.clearance,
                        board_edge_clearance=a.board_edge_clearance,
                        requirements=req, fit=_parse_fit(a.fit),
                        fit_step=a.fit_step, render_doc=render_doc)
    if not a.quiet:
        print(format_text(brief))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(brief, f, indent=1, sort_keys=True, default=str)
        print(f"Wrote {a.json}")
    print("JSON_SUMMARY: " + json.dumps(
        {'board': a.board, 'parts': brief['board'].get('footprints'),
         'nets': brief['board'].get('nets'),
         'unplaced': (brief.get('state') or {}).get('unplaced'),
         'sections': sorted(k for k, v in brief.items()
                            if isinstance(v, (dict, list))
                            and k not in ('sources', 'skipped')),
         'skipped': sorted(brief.get('skipped') or {})}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""gp14: a 3D iso still of a board, with its component bodies.

    python3 -X utf8 wk/gpm/_staging/iso_render.py BOARD.kicad_pcb STEM -o OUT.png [render args...]

Renders through krt-film's `py_router/kicad_iso_render.py` (the branch removed
it), from a TEMP COPY of the board whose 3D model paths are rewritten so
kicad-cli finds them on this Mac. The board itself is never touched.

  * KiCad 10's macOS library ships only .step models, but the boards name
    .wrl ones: a `.wrl` whose file does not exist becomes `.step` when that
    file exists.
  * `${KIPRJMOD}` points at the board's own folder, which has no 3D models
    once a board is copied out of its project: it becomes the SOURCE
    project folder named for STEM in boards.tsv.

Prints how many model references resolve before and after.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
FILM_WT = os.path.abspath(os.path.join(ROOT, '..', 'krt-film'))
LIB = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels'
MODEL = re.compile(r'\(model\s+"([^"]+)"')
VARS = ('KISYS3DMOD', 'KICAD6_3DMODEL_DIR', 'KICAD7_3DMODEL_DIR', 'KICAD8_3DMODEL_DIR',
        'KICAD9_3DMODEL_DIR', 'KICAD10_3DMODEL_DIR')


def source_dir(stem):
    for line in open(os.path.join(HERE, 'boards.tsv'), encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if len(f) >= 3 and f[1] == stem:
            return os.path.dirname(os.path.join(ROOT, f[2]))
    raise SystemExit(f'iso_render: {stem} is not in boards.tsv')


_INDEX = None


def _lib_index():
    """{lower-case model file name: path} over KiCad's 3D library, built once."""
    global _INDEX
    if _INDEX is None:
        _INDEX = {}
        for root, _dirs, files in os.walk(LIB):
            for f in files:
                if f.lower().endswith(('.step', '.stp', '.wrl')):
                    _INDEX.setdefault(f.lower(), os.path.join(root, f))
    return _INDEX


def resolve(ref, prj):
    p = ref.replace('${KIPRJMOD}', prj)
    for v in VARS:
        p = p.replace('${%s}' % v, LIB)
    if not os.path.isfile(p):
        # a model under a variable this machine does not define (a vendor library such as
        # ${ANT3DMDL}): fall back to KiCad's own model of the same file name, .step before .wrl
        name = os.path.basename(p).lower()
        stem = os.path.splitext(name)[0]
        idx = _lib_index()
        hit = idx.get(stem + '.step') or idx.get(name) or idx.get(stem + '.wrl')
        if hit:
            return hit
    return p


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__.strip().splitlines()[2])
    board, stem, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    prj = source_dir(stem)
    text = open(board, encoding='utf-8', newline='').read()
    refs = MODEL.findall(text)
    before = sum(1 for r in refs if os.path.isfile(resolve(r, prj)))

    def fix(m):
        p = resolve(m.group(1), prj)
        if not os.path.isfile(p) and p.lower().endswith('.wrl'):
            alt = p[:-4] + '.step'
            if os.path.isfile(alt):
                p = alt
        return '(model "%s"' % p
    new = MODEL.sub(fix, text)
    after = sum(1 for r in MODEL.findall(new) if os.path.isfile(r))
    print(f'iso_render: {after}/{len(refs)} model reference(s) resolve '
          f'(before the rewrite: {before})')
    with tempfile.TemporaryDirectory() as td:
        b = os.path.splitext(os.path.basename(board))[0]
        for ext in ('.kicad_pro', '.kicad_dru'):
            s = os.path.splitext(board)[0] + ext
            if os.path.exists(s):
                shutil.copy2(s, os.path.join(td, b + ext))
        tmp = os.path.join(td, b + '.kicad_pcb')
        with open(tmp, 'w', encoding='utf-8', newline='') as f:
            f.write(new)
        r = subprocess.run([sys.executable, '-X', 'utf8',
                            os.path.join(FILM_WT, 'py_router', 'kicad_iso_render.py'), tmp] + rest)
    sys.exit(r.returncode)


if __name__ == '__main__':
    main()

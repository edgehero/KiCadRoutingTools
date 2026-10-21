"""B12/L01: classify every boxed part in each board's movie3d.log by cause.
iso = the campaign's iso_render.py resolution (KIPRJMOD -> source project, vars -> KiCad lib, .wrl->.step twin)."""
import os, re, sys
ROOT = '<krt-checkout>'
sys.path.insert(0, os.path.join(ROOT, 'movie3d'))
import models
cli, _ = models.resolve_cli()
LIB = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels'
VARS = ('KISYS3DMOD', 'KICAD6_3DMODEL_DIR', 'KICAD7_3DMODEL_DIR', 'KICAD8_3DMODEL_DIR',
        'KICAD9_3DMODEL_DIR', 'KICAD10_3DMODEL_DIR')
def iso_ok(p, prj):
    p = p.replace('${KIPRJMOD}', prj)
    for v in VARS: p = p.replace('${%s}' % v, LIB)
    if not os.path.isfile(p) and p.lower().endswith('.wrl') and os.path.isfile(p[:-4] + '.step'):
        return True
    return os.path.isfile(p)
src = {}
for line in open(os.path.join(ROOT, 'wk/gp14/_staging/boards.tsv'), encoding='utf-8'):
    f = line.rstrip('\n').split('\t')
    if len(f) >= 3 and f[0].isdigit(): src[f[1]] = (f[0], f[2])
def fp_blocks(text):
    for m in re.finditer(r'\n\s*\(footprint\s+"', text):
        s = m.start() + 1; d = 0; j = s
        while True:
            c = text[j]
            if c == '(': d += 1
            elif c == ')':
                d -= 1
                if d == 0: break
            elif c == '"':
                j += 1
                while text[j] != '"':
                    if text[j] == '\\': j += 1
                    j += 1
            j += 1
        yield text[s:j + 1]
tot = {}
for stem in sys.argv[1:]:
    num, srcpath = src[stem]
    cmp_dir = os.path.join(ROOT, 'wk/gp14/_cmp', stem)
    log = open(os.path.join(cmp_dir, 'movie3d.log'), encoding='utf-8').read()
    m = re.search(r'fell back to a box \(([^)]*)\)', log)
    boxed = set(m.group(1).split(', ')) if m else set()
    fl = open(os.path.join(cmp_dir, 'films.log'), encoding='utf-8').read()
    inp = re.search(r'input (\S+?\.kicad_pcb)', fl).group(1)
    text = open(os.path.join(ROOT, inp), encoding='utf-8').read()
    run_dir = os.path.dirname(os.path.join(ROOT, inp))
    prj = os.path.dirname(os.path.join(ROOT, srcpath))
    dr, dp = models.model_dirs(cli, run_dir), models.model_dirs(cli, prj)
    cls = {}
    for b in fp_blocks(text):
        r = re.search(r'\(property\s+"Reference"\s+"([^"]*)"', b)
        r = r.group(1) if r else None
        if r not in boxed: continue
        attr = ' '.join(re.findall(r'\(attr([^)]*)\)', b))
        ms = [(mm.group(1), '(hide yes)' in mm.group(2)) for mm in re.finditer(r'\(model\s+"([^"]+)"(.*?)\n\t\t\)', b, re.S)]
        vis = [p for p, h in ms if not h]
        def mv(p, d, bd):
            t, _, _ = models.stage_models(f'(model "{p}"', d, bd)
            return os.path.isfile(re.search(r'"([^"]+)"', t).group(1))
        if not ms: c = 'no model in footprint (iso draws nothing either)'
        elif 'dnp' in attr.split(): c = 'DNP (movie3d exports with --no-dnp)'
        elif any(mv(p, dr, run_dir) for p in vis): c = 'resolves in run dir yet boxed (?)'
        elif any(mv(p, dp, prj) for p in vis): c = 'KIPRJMOD/relative: resolves only from the source project'
        elif any(iso_ok(p, prj) for p in vis): c = 'iso resolves, movie3d does not (?)'
        else: c = 'unresolvable for both (3rd-party/absolute/foreign path or renamed lib model)'
        cls.setdefault(c, []).append(r)
    print(f'=== {num} {stem}: {len(boxed)} boxed')
    for c, rs in sorted(cls.items()):
        print(f'  {len(rs):3d}  {c}: {", ".join(sorted(rs))}')
        tot[c] = tot.get(c, 0) + len(rs)
print('=== TOTAL'); [print(f'  {n:3d}  {c}') for c, n in sorted(tot.items(), key=lambda x: -x[1])]

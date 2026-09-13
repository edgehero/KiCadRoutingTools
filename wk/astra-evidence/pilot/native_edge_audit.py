"""Read-only native KiCad edge geometry for both frozen pilot candidates."""
import hashlib
import json
from pathlib import Path
import pcbnew

HERE=Path(__file__).resolve().parent
rows=[]
for arm in ('current_skill','concise_contract'):
    path=HERE/'arms'/arm/'final.kicad_pcb'
    board=pcbnew.LoadBoard(str(path))
    ys=[pcbnew.ToMM(p.y) for d in board.GetDrawings()
        if d.GetLayer()==pcbnew.Edge_Cuts for p in (d.GetStart(),d.GetEnd())]
    bounds=[min(ys),max(ys)]
    pads=[]
    for f in board.GetFootprints():
        if f.GetReference()!='Y1': continue
        for p in f.Pads():
            box=p.GetBoundingBox()
            y0=pcbnew.ToMM(box.GetY()); y1=pcbnew.ToMM(box.GetBottom())
            gap=min(y0-bounds[0],bounds[1]-y1)
            pads.append({'pad':p.GetNumber(),'y_bounds_mm':[y0,y1],
                         'nearest_horizontal_edge_gap_mm':round(gap,6),
                         'shortfall_at_audit_055_mm':round(max(0,.55-gap),6)})
    rows.append({'arm':arm,'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                 'outline_y_centerlines_mm':bounds,'Y1_pads':pads})
print(json.dumps({'basis':'Native KiCad pad bounds and straight Edge.Cuts centrelines; no board mutation',
                  'edge_floor_origin':'Post-hoc common sensitivity check from displayed placement fallback, not a task or fabrication specification',
                  'rows':rows},indent=2))

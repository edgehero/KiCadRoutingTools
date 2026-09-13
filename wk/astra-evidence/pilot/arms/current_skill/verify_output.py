"""Read-only output checks for this bounded pilot arm."""
import json, sys
from pathlib import Path
import pcbnew

root = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(root / p) for p in ('py_router', 'py_tools', 'py_placer')]
from kicad_parser import parse_kicad_pcb
from placement.floorplan import grade, load_intent
arm = Path(__file__).resolve().parent
before = pcbnew.LoadBoard(str(arm / 'board.kicad_pcb'))
after = pcbnew.LoadBoard(str(arm / 'final.kicad_pcb'))
def xy(v): return [v.x, v.y]
def snapshot(b):
    result = {}
    for f in b.GetFootprints():
        pads = sorted([(p.GetNumber(), p.GetNetname(), xy(p.GetFPRelativePosition()), xy(p.GetSize()), xy(p.GetDrillSize()), int(p.GetShape()), int(p.GetAttribute()), tuple(p.GetLayerSet().Seq()), round((p.GetOrientationDegrees()-f.GetOrientationDegrees()) % 360, 5)) for p in f.Pads()], key=str)
        result[f.m_Uuid.AsString()] = dict(ref=f.GetReference(), value=f.GetValue(), position=xy(f.GetPosition()), rotation=f.GetOrientationDegrees(), layer=f.GetLayerName(), locked=f.IsLocked(), pads=pads)
    return result
a, b = snapshot(before), snapshot(after)
movable = {'U1','Y1','C2','C4'}
fixed_bad=[]; content_bad=[]; moved=[]
for key, old in a.items():
    new=b[key]
    if old['ref'] not in movable and old != new: fixed_bad.append(key)
    if old['ref'] in movable:
        if old['position'] != new['position'] or old['rotation'] != new['rotation']: moved.append(old['ref'])
        if any(old[k] != new[k] for k in ('ref','value','layer','locked','pads')): content_bad.append(old['ref'])
def drawings(board):
    return sorted([(d.GetClass(), d.GetLayerName(), xy(d.GetStart()), xy(d.GetEnd()), d.GetWidth()) for d in board.GetDrawings()], key=str)
result = grade(load_intent(str(arm/'intent.json')), parse_kicad_pcb(str(arm/'final.kicad_pcb')), str(arm/'final.kicad_pcb'), clearance=0.25, board_edge_clearance=0.55)
report = dict(fixed_footprints_checked=17, fixed_changes=fixed_bad, moved=sorted(moved), moved_pad_or_content_changes=content_bad, footprints_same=set(a)==set(b), board_drawings_same=drawings(before)==drawings(after), tracks_before=len(before.GetTracks()), tracks_after=len(after.GetTracks()), zones_before=len(before.Zones()), zones_after=len(after.Zones()), copper_layer_count_same=before.GetCopperLayerCount()==after.GetCopperLayerCount(), proximity=result.proximity_measured)
(arm/'output-checks.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))

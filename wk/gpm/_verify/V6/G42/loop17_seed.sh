cd ~/Documents/git/krt-gpm
export PATH="$HOME/.venvs/krt/bin:/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"
O=wk/gpm/_verify/V6/G42/r17
K="KICAD_GLOBAL_PLAN=1 KICAD_GLOBAL_PLAN_SEQ=1 KICAD_GLOBAL_PLAN_SEQ_COST=1.5 KICAD_GLOBAL_PLAN_VIA_COST=20 KICAD_GLOBAL_PLAN_ITERS=50000 KICAD_GLOBAL_PLAN_ATTRACT=1 KICAD_ATTRACT_POTENTIAL=65 KICAD_GLOBAL_PLAN_RIVER=1 KICAD_FINALIZE_REAUDIT=1 KICAD_PACK_INLINE=1"
for tag in 0a 0b 1 2 3; do
  seed=${tag%[ab]}
  env $K PYTHONHASHSEED=$seed python3 -X utf8 py_router/route.py $O/spread_in.kicad_pcb $O/seed_$tag.kicad_pcb --nets '*' --clearance-ceiling 0.15 --track-width 0.15 --via-size 0.5 --via-drill 0.2 --power-nets GND +3V3 +5V /VBUS 'Net-(U3-VDDA)' 'Net-(U3-VBAT)' GNDREF --power-nets-widths 0.7 0.7 0.7 0.7 0.3 0.3 0.3 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 3.0 3.0 1.0 --via-cost 300 --board-edge-clearance 0.22 > $O/seed_$tag.log 2>&1
  echo "seed $tag md5=$(grep -E '^\s*\((start|end|at) ' $O/seed_$tag.kicad_pcb | md5) n=$(grep -c -E '^\s*\((segment|via)' $O/seed_$tag.kicad_pcb) $(grep -o 'Region discovery from fill model: 1[0-9] region' $O/seed_$tag.log | tail -1)"
done

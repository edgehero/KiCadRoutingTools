cd ~/Documents/git/krt-gpm
export PATH="$HOME/.venvs/krt/bin:/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"
O=wk/gpm/_verify/V6/G42/r20
for k in a b c; do
  s=$(date +%s)
  python3 -X utf8 py_router/route.py $O/jitter_s6.kicad_pcb $O/jitter_$k.kicad_pcb --nets '*' --no-bga-zones --clearance-ceiling 0.1016 --track-width 0.1016 --via-size 0.45 --via-drill 0.3 --power-nets GND VDD-IO VDD_DDR VDD_CORE +1V0_LDO VIN VBUS --power-nets-widths 0.3 0.3 0.3 0.3 0.25 0.5 0.5 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0 --max-ripup 5 --ripped-route-avoidance-cost 3 --track-proximity-cost 2 --via-cost 1200 > $O/jitter_$k.log 2>&1
  e=$(date +%s)
  echo "run $k $((e-s))s md5=$(grep -E '^\s*\((start|end|at) ' $O/jitter_$k.kicad_pcb | md5) $(grep -h -o 'Zone SPLIT: [0-9]* island(s) ([0-9.]* mm^2)' $O/jitter_$k.log | head -1) vias=$(grep -c '^\s*(via' $O/jitter_$k.kicad_pcb)"
done

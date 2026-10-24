cd ~/Documents/git/krt-gpm
export PATH="$HOME/.venvs/krt/bin:/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"
O=wk/gpm/_verify/V6/G42/r20
A=(--nets '*' --no-bga-zones --clearance-ceiling 0.1016 --track-width 0.1016 --via-size 0.45 --via-drill 0.3 --power-nets GND VDD-IO VDD_DDR VDD_CORE +1V0_LDO VIN VBUS --power-nets-widths 0.3 0.3 0.3 0.3 0.25 0.5 0.5 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 2.5 1.0 --max-ripup 5 --ripped-route-avoidance-cost 3 --track-proximity-cost 2 --via-cost 1200)
for run in "plain 0" "plain 3" "sorted 0" "sorted 3"; do
  set -- $run; mode=$1; seed=$2
  if [ $mode = plain ]; then S=py_router/route.py; else S=wk/gpm/_verify/V6/G42/sorted_layers_run.py; fi
  PYTHONHASHSEED=$seed python3 -X utf8 $S $O/jitter_s6.kicad_pcb $O/s_${mode}_$seed.kicad_pcb "${A[@]}" > $O/s_${mode}_$seed.log 2>&1
  echo "$mode seed $seed md5=$(grep -E '^\s*\((start|end|at) ' $O/s_${mode}_$seed.kicad_pcb | md5) $(grep -h -o 'Zone SPLIT: [0-9]* island(s) ([0-9.]* mm^2)' $O/s_${mode}_$seed.log | head -1) vias=$(grep -c '^\s*(via' $O/s_${mode}_$seed.kicad_pcb)"
done

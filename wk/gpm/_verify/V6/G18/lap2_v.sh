cd ~/Documents/git/krt-gpm
export PATH="$HOME/.venvs/krt/bin:/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"
E=wk/gpm/_verify/V6/G18
FL=(--track-width 0.0889 --clearance-ceiling 0.1 --via-size 0.45 --via-drill 0.2 --grid-step 0.025 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 6.0 1.5 1.0 --power-nets GND +3V3 VBUS VDC 'Net-(D5-K)' +1V2 '/+1.2V_CORE' +1V1 '/VIO_BANK_2' '/+3V3_STDBY' 'Net-(D1-K)' '/VCC_PLL' --power-nets-widths 0.5 0.5 0.7 0.7 0.7 0.5 0.5 0.3 0.3 0.3 0.3 0.3)
python3 -X utf8 py_router/route.py $E/6_lap1.kicad_pcb $E/7_lap2.kicad_pcb --nets '/~{ICE_RST}' '+3V3' 'GND' --rip-existing-nets '/USB_N' '/USB_P' '/LED_R' '/ICE_DONE_ADC0' '/ADC2|PB' 'Net-(U3-GPIO25)' '/ADC3' '/QSPI_SD3' '/ICE_27' 'Net-(D2-BK)' "${FL[@]}" --json-out $E/7_lap2.json

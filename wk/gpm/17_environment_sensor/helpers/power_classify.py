"""helpers/power_classify.py BOARD -- the /analyze-power-nets session of this run, as a script.

Why a helper: the skill tells the agent to run its Steps 1-6 as inline Python
(there is no CLI); this file is that inline session saved so the TOOL_GAPS
repro of get_power_net_recommendations' widths can be re-run from WT:

    python3 -X utf8 wk/gpm/17_environment_sensor/helpers/power_classify.py \
        wk/gpm/17_environment_sensor/repro/fixed.kicad_pcb
"""
import sys

sys.path.insert(0, "py_tools")
sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component,  # noqa: E402
                                 trace_power_paths, get_power_net_recommendations,
                                 format_analysis_report, ComponentRole as R)

components, pcb_data = analyze_pcb(sys.argv[1])


def c(ref, role, ma=None, n=''):
    classify_component(components, ref, role, current_rating_ma=ma, notes=n)


c('J1', R.POWER_SOURCE, 500, 'USB-C receptacle, VBUS input; USB 2.0 default 500 mA (5k1 CC sink, no PD)')
c('U2', R.POWER_SOURCE, 300, 'AP7370-33 LDO +5V->+3V3; distributors list 300-500 mA (SOT23-3); 300 used')
c('U1', R.CURRENT_SINK, 15, 'FT232R USB-UART, 15 mA operating')
c('U3', R.CURRENT_SINK, 60, 'STM32G474 @170MHz: ESTIMATE ~30-40 mA run + I/O, 60 mA budget')
c('U4', R.CURRENT_SINK, 1, 'MB85RC1M FRAM, <1 mA (estimate)')
c('U5', R.CURRENT_SINK, 60, 'SHT45, heater up to ~60 mA at 3.3 V (estimate)')
c('U6', R.CURRENT_SINK, 1, 'BME280, <1 mA peak (estimate)')
for d in ('D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9'):
    c(d, R.SHUNT, None, 'ESD/TVS protection to GND')
c('LD1', R.CURRENT_SINK, 5, 'green 0603 LED via 470R on +5V (estimate)')
c('LD2', R.CURRENT_SINK, 5, 'green 0603 LED via 470R on PA5 (estimate)')
c('J2', R.CURRENT_SINK, 100, 'JST-SH I2C port: +3V3 out to external modules (estimate)')
c('J3', R.CURRENT_SINK, 100, 'JST-SH I2C port (back): +3V3 out (estimate)')
for r in ('MP1', 'MP2', 'MP3'):
    c(r, R.SHUNT, None, 'mounting hole, no net')
for r in ['TP%d' % i for i in range(1, 13)]:
    c(r, R.SHUNT, None, 'test point')
c('Y1', R.SHUNT, None, '32.768 kHz crystal')
c('Y2', R.SHUNT, None, '8 MHz crystal')
paths = trace_power_paths(pcb_data, components)
rec = get_power_net_recommendations(pcb_data, components, paths)
print(format_analysis_report(pcb_data, components, paths, rec))
print("REC", rec)

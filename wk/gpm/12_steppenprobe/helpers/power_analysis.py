# analyze-power-nets, followed by hand (gpm run): classifications from datasheet lookups.
import sys
sys.path.insert(0, "py_tools"); sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, classify_component, trace_power_paths,
    get_power_net_recommendations, format_analysis_report, ComponentRole as CR)
components, pcb_data = analyze_pcb(sys.argv[1])
C = lambda r, role, ma, n: classify_component(components, r, role, current_rating_ma=ma, notes=n)
C('J1', CR.POWER_SOURCE, 500, 'USB-C receptacle (GCT USB4085): VBUS input, USB 2.0 default 500 mA budget')
C('U2', CR.POWER_SOURCE, 200, 'XC6206P332MR LDO 5V->3.3V, 200 mA max output (Torex datasheet)')
C('U1', CR.CURRENT_SINK, 70, 'FT2232HL, ~70 mA operating supply current (distributor figure for FT2232H); its VREGOUT feeds its own VCORE')
C('J4', CR.CURRENT_SINK, 100, '1x16 breakout header: pin 1 exports +3V3 to the target; budget = LDO 200 mA minus the board\'s own ~90 mA')
C('J2', CR.SHUNT, None, 'Cortex debug 2x7 header: signals + VDRIVE_TRGT sense (target supplies Vdrive through R11 100R)')
for d in ('D1','D2','D3','D4','D5','D6'):
    C(d, CR.CURRENT_SINK, 2, '0603 indicator LED, ~1.3 mA through its 1k resistor')
C('Q1', CR.SHUNT, None, '2N7002 open-drain SRST driver (signal)')
for r in ('FID1','FID2','FID3','H1','H2','H3','H4','TP1','TP2','Y1'):
    C(r, CR.SHUNT, None, 'no power role')
for u in ('U5','U6','U7','U8','U9','U10','U11','U12'):
    C(u, CR.CURRENT_SINK, 5, '74LVC1G125/126 single buffer, a few mA dynamic')
C('U3', CR.SHUNT, None, 'SRV05-4 ESD array (shunt protection)')
C('U4', CR.CURRENT_SINK, 2, '93C46-class EEPROM, DNF')
paths = trace_power_paths(pcb_data, components)
rec = get_power_net_recommendations(pcb_data, components, paths)
print(format_analysis_report(pcb_data, components, paths, rec))
print('RECOMMENDATIONS', rec)

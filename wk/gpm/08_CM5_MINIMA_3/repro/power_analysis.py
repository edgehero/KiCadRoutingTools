import sys
sys.path.insert(0, "py_tools"); sys.path.insert(0, "py_router")
from analyze_power_paths import (analyze_pcb, get_components_needing_analysis, classify_component,
    trace_power_paths, get_power_net_recommendations, format_analysis_report, ComponentRole)
components, pcb_data = analyze_pcb("wk/gpm/08_CM5_MINIMA_3/repro/fixed.kicad_pcb")
unknown = get_components_needing_analysis(components)
print("UNKNOWN:", sorted(unknown.keys()) if isinstance(unknown, dict) else sorted(getattr(c,'reference',str(c)) for c in unknown))
C = ComponentRole
cl = {
 'J101': (C.POWER_SOURCE, 5000, "USB-C power input, +5V (CM5 5V/5A PD supply via CC to the module)"),
 'Module301': (C.CURRENT_SINK, 3000, "CM5 module GPIO connector: +5V input ~3 A (CM5 + downstream); sources +3V3_PI/+1V8 (<=300 mA, estimate)"),
 'Module302': (C.SHUNT, None, "CM5 HSS connector: signals only"),
 'U702': (C.POWER_SOURCE, 3000, "AP3441 3 A buck, +5V -> M2_3V3 (datasheet: 3 A max output)"),
 'U701': (C.PASS_THROUGH, 1500, "AP22653 USB power switch +5V -> VBUS_USB2.0 (current limit set by R701; estimate 1.5 A)"),
 'U405': (C.PASS_THROUGH, 500, "STMPS2151 500 mA power switch +5V -> HDMI_+5V"),
 'USB701': (C.CURRENT_SINK, 1500, "USB-C host port load on VBUS_USB2.0 (estimate 1.5 A)"),
 'J701': (C.CURRENT_SINK, 2500, "M.2 M-key NVMe 3.3 V load (estimate 2.5 A)"),
 'J501': (C.CURRENT_SINK, 55, "HDMI +5V to sink (spec 55 mA)"),
 'J601': (C.CURRENT_SINK, 200, "fan connector 5 V (estimate 200 mA)"),
 'J502': (C.CURRENT_SINK, 100, "Qwiic I2C 3V3 (estimate)"),
 'J503': (C.CURRENT_SINK, 100, "SPI display 3V3 (estimate)"),
 'J802': (C.CURRENT_SINK, 250, "camera FPC 3V3 (estimate 250 mA)"),
 'J1': (C.SHUNT, None, "RJ45: signals, LED anodes on +3V3"),
 'CN1': (C.SHUNT, None, "RTC battery connector (uA)"),
 'D101': (C.SHUNT, None, "ESD"), 'D701': (C.SHUNT, None, "ESD"), 'D502': (C.SHUNT, None, "ESD"),
 'D401': (C.SHUNT, None, "ESD"), 'D402': (C.SHUNT, None, "ESD"), 'D403': (C.SHUNT, None, "ESD"),
 'U401': (C.SHUNT, None, "ESD array"), 'U402': (C.SHUNT, None, "ESD array"),
 'U1': (C.CURRENT_SINK, 1, "LIS3DH accelerometer"), 'U602': (C.CURRENT_SINK, 1, "SN74LVC1G14"),
 'U703': (C.CURRENT_SINK, 1, "32.768 kHz oscillator"),
 'SW101': (C.SHUNT, None, "boot button (signal)"), 'SW501': (C.SHUNT, None, "power button (signal)"),
}
for ref,(role,ma,notes) in cl.items():
    kw = {'notes': notes}
    if ma is not None: kw['current_rating_ma'] = ma
    try:
        classify_component(components, ref, role, **kw)
    except Exception as e:
        print("classify fail", ref, e)
paths = trace_power_paths(pcb_data, components)
rec = get_power_net_recommendations(pcb_data, components, paths)
print(format_analysis_report(pcb_data, components, paths, rec))
print("REC", rec)

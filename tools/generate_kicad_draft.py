#!/usr/bin/env python3
"""Rebuild the KiCad 7 placement study. Requires KiCad's pcbnew Python module.

WARNING: regeneration replaces generated CAD files; preserve hand edits first.
All package assignments and board dimensions are provisional, not approved parts.
"""
import argparse
import json
import math
import re
import shutil
import uuid
from pathlib import Path

NAME = "UAV_Mini_RevA_Draft"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware" / "kicad" / NAME
NS = uuid.UUID("759b5d23-22d3-4202-ae0a-67f60e648a75")


def uid(key):
    return str(uuid.uuid5(NS, key))


def quote(value):
    return json.dumps(str(value), ensure_ascii=False)


def block(text, start):
    depth, string, escape = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                string = False
        elif ch == '"':
            string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("Unbalanced library symbol")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad-share", type=Path, default=Path("/usr/share/kicad"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / (NAME + ".kicad_pcb")).exists() and not args.overwrite:
        parser.error("CAD files exist. Commit/back up hand edits, then use --overwrite.")
    import pcbnew as pcb

    symbols = {}
    components = []
    items = []
    root_id = uid("sheet")
    seq = 0

    def get_symbol(lib_id):
        if lib_id in symbols:
            return symbols[lib_id]
        lib, name = lib_id.split(":")
        source = (args.kicad_share / "symbols" / (lib + ".kicad_sym")).read_text()
        begin = source.index('(symbol ' + quote(name) + ' ')
        raw = block(source, begin)
        if "(extends " in raw:
            raise ValueError("Inherited symbols are not supported")
        pins = []
        for match in re.finditer(r'\(pin (?:passive|input|output|bidirectional|power_in|power_out|no_connect) ', raw):
            part = block(raw, match.start())
            xyz = re.search(r'\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)', part)
            num = re.search(r'\(number "([^"]+)"', part).group(1)
            pins.append((num, *map(float, xyz.groups())))
        raw = raw.replace('(symbol ' + quote(name), '(symbol ' + quote(lib_id), 1)
        symbols[lib_id] = (raw, pins)
        return raw, pins

    def wire(a, b):
        nonlocal seq
        seq += 1
        items.append(f'(wire (pts (xy {a[0]:.3f} {a[1]:.3f}) (xy {b[0]:.3f} {b[1]:.3f})) '
                     f'(stroke (width 0) (type default)) (uuid {uid("wire" + str(seq))}))')

    def note(text, x, y, size=1.27):
        nonlocal seq
        seq += 1
        items.append(f'(text {quote(text)} (at {x} {y} 0) '
                     f'(effects (font (size {size} {size})) (justify left top)) '
                     f'(uuid {uid("text" + str(seq))}))')

    def add(ref, lib, val, fp, x, y, nets, px, py, rotation=0, board_rotation=0):
        _, pins = get_symbol(lib)
        cid = uid(ref)
        fields = []
        # Keep long provisional values readable and separate from the net labels.
        for key, value, fx, fy, hidden, size in [
            ("Reference", ref, x + 4, y - 3, False, 1.27),
            ("Value", val, x + 4, y - 1, False, .9),
            ("Footprint", fp, x, y, True, 1.27),
            ("Datasheet", "", x, y, True, 1.27),
        ]:
            if lib in ("Device:D_Schottky", "Jumper:SolderJumper_2_Open") or rotation:
                if key == "Reference":
                    fx, fy = x, y-6
                if key == "Value":
                    fx, fy = x, y-3.5
            fields.append(f'(property {quote(key)} {quote(value)} (at {fx} {fy} {rotation}) '
                          f'(effects (font (size {size} {size})) (justify left) {"hide" if hidden else ""}))')
        pin_fields = ' '.join(f'(pin {quote(p[0])} (uuid {uid(ref + "/" + p[0])}))' for p in pins)
        items.append(f'(symbol (lib_id {quote(lib)}) (at {x} {y} {rotation}) (unit 1) '
                     f'(in_bom yes) (on_board yes) (dnp no) (uuid {cid}) {" ".join(fields)} '
                     f'{pin_fields} (instances (project {quote(NAME)} '
                     f'(path "/{root_id}" (reference {quote(ref)}) (unit 1)))))')
        assert set(nets) == {p[0] for p in pins}, (ref, nets, pins)
        for pin, sx, sy, angle in pins:
            r = math.radians(rotation)
            ax = x + sx * math.cos(r) - sy * math.sin(r)
            ay = y - sx * math.sin(r) - sy * math.cos(r)
            net = nets[pin]
            if net is None:
                items.append(f'(no_connect (at {ax:.3f} {ay:.3f}) (uuid {uid(ref + "/NC/" + pin)}))')
                continue
            a = math.radians(angle + rotation)
            end = (ax - 10.16 * math.cos(a), ay + 10.16 * math.sin(a))
            wire((ax, ay), end)
            label_angle = 0 if abs(math.cos(a)) > .5 else 90
            items.append(f'(label {quote(net)} (at {end[0]:.3f} {end[1]:.3f} {label_angle}) '
                         f'(effects (font (size 1 1)) (justify left bottom)) (uuid {uid(ref + "/net/" + pin)}))')
        components.append(dict(ref=ref, symbol=lib, value=val, footprint=fp, pins=nets,
                               x=px, y=py, rotation=board_rotation, uuid=cid))

    def header(n, socket=False):
        lib = "Connector_PinSocket_2.54mm" if socket else "Connector_PinHeader_2.54mm"
        base = "PinSocket" if socket else "PinHeader"
        return f"{lib}:{base}_1x{n:02d}_P2.54mm_Vertical"

    resistor = "Resistor_SMD:R_0603_1608Metric"
    capacitor = "Capacitor_SMD:C_0603_1608Metric"
    note("UAV MINI / REV A / ELECTRICAL + PLACEMENT DRAFT", 15, 12, 2.2)
    note("NOT FOR FABRICATION OR POWER-UP. All footprints and connector pinouts require verification.", 15, 18)
    note("1. BATTERY + EXTERNAL BOOST INTERFACE", 15, 27, 1.5)
    add("J1", "Connector_Generic:Conn_01x02", "BAT_1S_TBD", header(2), 40, 40,
        {"1":"V_bat", "2":"GND"}, 118, 153)
    add("J11", "Connector_Generic:Conn_01x04", "BOOST_INTERFACE_TBD", header(4), 103, 40,
        {"1":"V_bat", "2":"GND", "3":"BOOST_5V", "4":"GND"}, 153, 125)
    add("C1", "Device:C_Polarized", "BULK_TBD", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm", 35, 72,
        {"1":"V_bat", "2":"GND"}, 124, 151)
    add("C2", "Device:C", "100nF_ASSUMED", capacitor, 80, 72,
        {"1":"V_bat", "2":"GND"}, 134, 151)
    note("BOOST_5V has NO connection to S3_5V.\nUSB isolation / source selection is NOT designed.\nNo charger, fuse or reverse-polarity stage fitted.", 15, 91, 1.05)
    note("2. S3 SOCKET CONTRACT (UNVERIFIED)", 138, 27, 1.5)
    add("J7", "Connector_Generic:Conn_01x09", "S3_LEFT_TBD", header(9, True), 170, 50,
        dict(zip(map(str, range(1,10)), [None,None,"VBAT_SENSE","FLOW_CS",None,"PWM_M0","PWM_M1","PWM_M2","PWM_M3"])),
        121.11, 120)
    add("J8", "Connector_Generic:Conn_01x09", "S3_RIGHT_TBD", header(9, True), 231, 50,
        dict(zip(map(str, range(1,10)), ["S3_5V","GND","S3_3V3","SPI_MISO","SPI_SCK","SPI_MOSI","IMU_CS","I2C_SCL","I2C_SDA"])),
        138.89, 120)
    note("GPIO4/5/6/7: M0/M1/M2/M3\nGPIO10/11/12/13: CS/MOSI/SCK/MISO\nGPIO8/9: SDA/SCL; GPIO2: FLOW_CS\nNo connection between 5 V and 3.3 V.", 138, 78, 1.05)
    note("3. OPTIONAL SENSOR MODULES", 267, 27, 1.5)
    add("J6", "Connector_Generic:Conn_01x04", "TOF_I2C_TBD", header(4), 300, 40,
        {"1":"S3_3V3","2":"GND","3":"I2C_SDA","4":"I2C_SCL"}, 115, 106, board_rotation=90)
    sensor = {"1":"S3_3V3","2":"GND","3":"SPI_SCK","4":"SPI_MOSI","5":"SPI_MISO"}
    add("J9", "Connector_Generic:Conn_01x06", "IMU_SPI_TBD", header(6), 300, 70,
        dict(sensor, **{"6":"IMU_CS"}), 130, 106, board_rotation=90)
    add("J10", "Connector_Generic:Conn_01x06", "FLOW_SPI_TBD", header(6), 376, 70,
        dict(sensor, **{"6":"FLOW_CS"}), 124, 144, board_rotation=90)
    note("Module connectors are a proposed contract,\nNOT raw sensor IC pinouts. Pull-ups/decoupling\nand module supply requirements remain TBD.", 337, 39, .95)
    note("4. FOUR BRUSHED MOTOR CHANNELS / LOW-SIDE SWITCHES", 15, 110, 1.5)
    positions = [(105,145),(155,145),(155,115),(105,115)]
    roles = ["M0_RL_CCW", "M1_RR_CW", "M2_FR_CCW", "M3_FL_CW"]
    for i, (px, py) in enumerate(positions):
        sx = 45 + 95*i
        dnet, gnet, pwm = f"M{i}_NEG", f"GATE_M{i}", f"PWM_M{i}"
        note(roles[i], sx-25, 120, 1.35)
        add(f"J{i+2}", "Connector_Generic:Conn_01x02", roles[i], header(2), sx, 132,
            {"1":"V_bat","2":dnet}, px, py)
        add(f"D{i+1}", "Device:D_Schottky", "SCHOTTKY_TBD", "Diode_SMD:D_SOD-123", sx+12, 151,
            {"1":"V_bat","2":dnet}, px+(-3 if px>130 else 3), py-(6 if i<2 else 4))
        add(f"Q{i+1}", "Device:Q_NMOS_GSD", "NMOS_TBD_G1_S2_D3", "Package_TO_SOT_SMD:SOT-23", sx+5, 180,
            {"1":gnet,"2":"GND","3":dnet}, px+(-6 if px>130 else 6), py+(-1 if i<2 else 1))
        add(f"R{2*i+1}", "Device:R", "100R_ASSUMED", resistor, sx-12, 168,
            {"1":pwm,"2":gnet}, px+(-11 if px>130 else 11), py-(5 if i<2 else 3), rotation=90)
        add(f"R{2*i+2}", "Device:R", "10k_ASSUMED", resistor, sx-22, 203,
            {"1":gnet,"2":"GND"}, px+(-11 if px>130 else 11), py+(0 if i<2 else 2))
    note("5. BATTERY ADC / DEFAULT OPEN LINK", 15, 228, 1.5)
    add("R9", "Device:R", "10k_ASSUMED", resistor, 40, 253,
        {"1":"V_bat","2":"VBAT_DIV"}, 126, 136)
    add("R10", "Device:R", "10k_ASSUMED", resistor, 85, 253,
        {"1":"VBAT_DIV","2":"GND"}, 130, 136)
    add("C3", "Device:C", "100nF_ASSUMED", capacitor, 130, 253,
        {"1":"VBAT_DIV","2":"GND"}, 134, 136)
    add("JP1", "Jumper:SolderJumper_2_Open", "ADC_LINK_OPEN", "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm", 177, 253,
        {"1":"VBAT_DIV","2":"VBAT_SENSE"}, 130, 140)
    note("JP1 stays OPEN until ADC power-off injection is checked.\nQ1-Q4: pin 1=G, 2=S, 3=D (different from old GDS tutorial).\nD1-D4: pin 1=K to V_bat; pin 2=A to motor negative.\nNo selected MOSFET/diode/regulator part numbers.\nBoard: 60 x 60 mm placement study, 2 layers, UNROUTED.", 220, 234, 1.15)
    title = '(title_block (title "UAV Mini Rev A - NOT FOR FABRICATION") (date "2026-11-03") (rev "DRAFT-0") (company "UAV Mini"))'
    text = f'(kicad_sch (version 20230121) (generator uav_mini_draft) (uuid {root_id}) (paper "A3") {title}\n'
    text += '(lib_symbols\n' + '\n'.join(s[0] for s in symbols.values()) + ')\n'
    text += '\n'.join(items) + '\n(sheet_instances (path "/" (page "1")))\n)\n'
    (OUT / (NAME + ".kicad_sch")).write_text(text)
    (OUT / (NAME + ".kicad_pro")).write_text(json.dumps({"meta":{"filename":NAME+".kicad_pro","version":1}}, indent=2)+"\n")

    board = pcb.BOARD()
    board.SetCopperLayerCount(2)
    netnames = sorted({n for c in components for n in c["pins"].values() if n})
    nets = {}
    for name in netnames:
        net = pcb.NETINFO_ITEM(board, name)
        board.Add(net)
        nets[name] = net
    footprint_libraries = set()
    for c in components:
        lib, part = c["footprint"].split(":")
        local_lib = OUT / "footprints" / (lib + ".pretty")
        local_lib.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.kicad_share / "footprints" / (lib + ".pretty") / (part + ".kicad_mod"), local_lib)
        footprint_libraries.add(lib)
        fp = pcb.FootprintLoad(str(args.kicad_share / "footprints" / (lib + ".pretty")), part)
        if fp is None:
            raise ValueError("Missing footprint " + c["footprint"])
        fp.SetFPID(pcb.LIB_ID(lib, part))
        fp.SetReference(c["ref"])
        fp.SetValue(c["value"])
        fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(c["x"]), pcb.FromMM(c["y"])))
        fp.SetOrientationDegrees(c["rotation"])
        path = pcb.KIID_PATH()
        path.push_back(pcb.KIID(root_id))
        path.push_back(pcb.KIID(c["uuid"]))
        fp.SetPath(path)
        fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(.8),pcb.FromMM(.8)))
        fp.Reference().SetTextThickness(pcb.FromMM(.12))
        if c["rotation"] == 90:
            fp.Reference().SetTextAngle(pcb.EDA_ANGLE(0, pcb.DEGREES_T))
            fp.Reference().SetPosition(pcb.VECTOR2I(pcb.FromMM(c["x"]+5),pcb.FromMM(c["y"]+3)))
        for pad in fp.Pads():
            n = c["pins"].get(pad.GetNumber())
            if n:
                pad.SetNet(nets[n])
        board.Add(fp)
    corners = [(100,100),(160,100),(160,160),(100,160)]
    for a,b in zip(corners, corners[1:]+corners[:1]):
        edge = pcb.PCB_SHAPE()
        edge.SetShape(pcb.SHAPE_T_SEGMENT)
        edge.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]),pcb.FromMM(a[1])))
        edge.SetEnd(pcb.VECTOR2I(pcb.FromMM(b[0]),pcb.FromMM(b[1])))
        edge.SetLayer(pcb.Edge_Cuts)
        edge.SetWidth(pcb.FromMM(.05))
        board.Add(edge)
    def board_text(text,x,y,size,layer):
        t = pcb.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)))
        t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size),pcb.FromMM(size)))
        t.SetTextThickness(pcb.FromMM(.15))
        t.SetLayer(layer)
        board.Add(t)
    board_text("UAV MINI / DRAFT-0",130,103.5,1.3,pcb.F_SilkS)
    board_text("FRONT",130,112,1,pcb.F_SilkS)
    board_text("NOT FOR FABRICATION",130,157.5,1.3,pcb.F_SilkS)
    board_text("S3 OUTLINE\nANTENNA TBD",130,128,.8,pcb.Dwgs_User)
    board_text("UNROUTED - 60x60 mm ASSUMED",130,164,1.3,pcb.Dwgs_User)
    pcb.SaveBoard(str(OUT / (NAME + ".kicad_pcb")), board)
    table = ['(fp_lib_table (version 7)']
    for lib in sorted(footprint_libraries):
        table.append(f'(lib (name {quote(lib)}) (type KiCad) (uri "${{KIPRJMOD}}/footprints/{lib}.pretty") (options "") (descr "Unmodified KiCad 7 library subset; provisional use"))')
    (OUT / "fp-lib-table").write_text('\n'.join(table)+')\n')
    manifest = {"status":"DRAFT_NOT_FOR_FABRICATION", "kicad":pcb.Version(),
                "board_mm":[60,60], "tracks":0, "zones":0, "source_selection":"NOT_IMPLEMENTED",
                "components":components, "nets":netnames}
    (OUT / "design_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(f"Generated {len(components)} symbols/footprints, {len(netnames)} named nets at {OUT}")


if __name__ == "__main__":
    main()

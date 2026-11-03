#!/usr/bin/env python3
"""Check CAD consistency with native KiCad 7. This is NOT manufacturing approval.

Run using the Python interpreter that can import pcbnew. Requires kicad-cli.
Outputs an independently exported netlist, DRC report and validation summary.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", default="kicad-cli")
    args = parser.parse_args()
    import pcbnew

    name = "UAV_Mini_RevA_Draft"
    folder = Path(__file__).resolve().parents[1] / "hardware" / "kicad" / name
    sch = folder / (name + ".kicad_sch")
    pcb = folder / (name + ".kicad_pcb")
    netfile = folder / "design.net.xml"
    subprocess.run([args.cli, "sch", "export", "netlist", str(sch), "--format", "kicadxml", "-o", str(netfile)], check=True)
    tree = ET.parse(netfile)
    schematic = {(n.attrib["ref"], n.attrib["pin"]): net.attrib["name"].lstrip("/")
                 for net in tree.findall(".//nets/net") for n in net.findall("node")}
    manifest = json.loads((folder / "design_manifest.json").read_text())
    expected = {(c["ref"], pin): net for c in manifest["components"] for pin, net in c["pins"].items()}
    for key, net in expected.items():
        if net:
            assert schematic.get(key) == net, ("Schematic net mismatch", key, net, schematic.get(key))
        else:
            assert schematic.get(key, "").startswith("unconnected-"), ("NC pin is connected", key)
    board = pcbnew.LoadBoard(str(pcb))
    pads = {(fp.GetReference(), p.GetNumber()): p.GetNetname() for fp in board.GetFootprints() for p in fp.Pads()}
    assert set(pads) == set(expected), "PCB/schematic pad sets differ"
    assert {fp.GetReference() for fp in board.GetFootprints()} == {c["ref"] for c in manifest["components"]}
    for key, net in expected.items():
        assert pads[key] == (net or ""), ("PCB net mismatch", key, pads[key], net)
    # Check the topology independently of the generator's component table.
    for i in range(4):
        assert schematic[(f"Q{i+1}","1")] == f"GATE_M{i}"
        assert schematic[(f"Q{i+1}","2")] == "GND"
        assert schematic[(f"Q{i+1}","3")] == f"M{i}_NEG"
        assert schematic[(f"D{i+1}","1")] == "V_bat"
        assert schematic[(f"D{i+1}","2")] == f"M{i}_NEG"
    assert schematic[("J11","3")] != schematic[("J8","1")] != schematic[("J8","3")]
    assert schematic[("JP1","1")] == "VBAT_DIV" and schematic[("JP1","2")] == "VBAT_SENSE"
    assert len(board.GetTracks()) == 0 and len(board.Zones()) == 0, "Draft status must be revised after routing"
    drc = folder / "drc-draft.txt"
    assert pcbnew.WriteDRCReport(board, str(drc), pcbnew.EDA_UNITS_MILLIMETRES, True)
    findings = Counter(line[1:line.index("]")] for line in drc.read_text().splitlines() if line.startswith("["))
    assert findings.get("unconnected_items", 0) > 0, "Unrouted draft should have missing connections"
    assert set(findings) == {"unconnected_items"}, f"Unexpected placement DRC findings: {findings}"
    summary = {
        "status": "DRAFT_NOT_FOR_FABRICATION",
        "kicad_version": pcbnew.Version(),
        "schematic_native_export": "PASS",
        "schematic_manifest_and_pcb_named_nets": "PASS",
        "motor_gate_source_drain_and_diode_polarity": "PASS_TO_PROPOSED_CONTRACT_ONLY",
        "symbols": len(manifest["components"]),
        "footprints": len(board.GetFootprints()),
        "pad_count": len(pads),
        "named_nets": len(manifest["nets"]),
        "tracks": 0, "zones": 0,
        "drc_findings": dict(findings),
        "full_drc_pass": False,
        "erc": "NOT_RUN",
        "hardware_validation": "NOT_RUN",
        "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (sch,pcb)},
    }
    (folder / "validation.json").write_text(json.dumps(summary, indent=2)+"\n")
    # Avoid making exported netlists depend on the build machine's absolute path.
    source = tree.find("./design/source")
    source.text = sch.name
    tree.write(netfile, encoding="utf-8", xml_declaration=True)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

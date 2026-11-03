#!/usr/bin/env python3
"""Prepare an ignored local Flix checkout; never edit or vendor the source repo."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args], text=True).strip()


def replace_once(text, old, new, description):
    if text.count(old) != 1:
        raise ValueError(f"Upstream hook mismatch: {description}")
    return text.replace(old, new, 1)


def prepare(source, output):
    lock = json.loads((ROOT / "firmware/upstream.lock.json").read_text())
    source, output = Path(source).resolve(), Path(output).resolve()
    if git(source, "rev-parse", "HEAD") != lock["commit"]:
        raise ValueError("Upstream commit differs from lock; refuse to patch")
    if git(source, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Upstream must be clean (including untracked files)")
    if output.exists():
        raise ValueError("Output exists; use a new --output path to preserve prior work")
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("Output must not overlap upstream")
    # Prepare all mutations in memory first, before creating output.
    files = {p.name: p.read_text() for p in (source / "flix").iterdir()
             if p.suffix in (".ino", ".h")}
    files["config.h"] = replace_once(files["config.h"], "\t// Set defaults here",
        '\t#include "uavmini_defaults.h"', "defaults")
    files["parameters.ino"] = replace_once(files["parameters.ino"],
        'storage.begin("flix");', 'storage.begin("uavmini_bench");', "NVS namespace")
    files["flix.ino"] = replace_once(files["flix.ino"], "void setup() {",
        "void setup() {\n\tuavMiniHoldMotorPinsLow();", "early motor inhibit")
    brownout = "\tREG_CLR_BIT(RTC_CNTL_BROWN_OUT_REG, RTC_CNTL_BROWN_OUT_ENA); // disable reset on low voltage"
    files["power.ino"] = replace_once(files["power.ino"], brownout,
        "\t// UAV Mini: retain the platform brownout detector.", "brownout")
    files["motors.ino"] = (ROOT / "firmware/bench_motors.ino").read_text()
    files["uavmini_defaults.h"] = (ROOT / "firmware/profiles/s3_bench.h").read_text()
    # SuperMini LED pin/revision is unknown. Do not drive arbitrary GPIO/flow CS.
    files["led.ino"] = "void setupLED() {}\nvoid setLED(bool) {}\nvoid blinkLED() {}\n"
    output.mkdir(parents=True)
    sketch = output / "flix"
    sketch.mkdir()
    for name, text in files.items():
        (sketch / name).write_text(text, encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(lock, indent=2) + "\n")
    return sketch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, default=ROOT / "external/flix")
    parser.add_argument("--output", type=Path, default=ROOT / "build/bench")
    args = parser.parse_args()
    lock = json.loads((ROOT / "firmware/upstream.lock.json").read_text())
    if not args.upstream.exists():
        args.upstream.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--no-checkout", lock["repository"], str(args.upstream)], check=True)
        subprocess.run(["git", "-C", str(args.upstream), "checkout", "--detach", lock["commit"]], check=True)
    try:
        print(prepare(args.upstream, args.output))
    except (ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Preparation failed: {exc}\n")


if __name__ == "__main__":
    main()

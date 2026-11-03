#!/usr/bin/env python3
"""Install pinned dependencies and compile bench firmware. Never uploads a device."""
import argparse
import json
import subprocess
from pathlib import Path
from prepare_firmware import ROOT, prepare

INDEX = "https://espressif.github.io/arduino-esp32/package_esp32_index.json"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cli", default="arduino-cli")
    p.add_argument("--install", action="store_true")
    p.add_argument("--upstream", type=Path, default=ROOT / "external/flix")
    p.add_argument("--output", type=Path, default=ROOT / "build/bench")
    args = p.parse_args()
    lock = json.loads((ROOT / "firmware/upstream.lock.json").read_text())
    def run(*command):
        subprocess.run([args.cli, *command], check=True)
    if args.install:
        run("core", "update-index", "--additional-urls", INDEX)
        run("core", "install", lock["arduino_core"], "--additional-urls", INDEX)
        run("lib", "update-index")
        run("lib", "install", *lock["libraries"])
    # Always regenerate from the verified clean checkout. Existing output is refused.
    sketch = prepare(args.upstream, args.output)
    run("compile", str(sketch), "--fqbn", lock["fqbn"], "--build-property",
        "build.core_debug_level=1", "--output-dir", str(args.output / "binary"))


if __name__ == "__main__":
    main()

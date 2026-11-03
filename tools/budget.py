#!/usr/bin/env python3
"""Summarize design allocations, not researched retail prices."""
import json
from pathlib import Path

data = json.loads((Path(__file__).resolve().parents[1] / "hardware/budget_targets.json").read_text())
core = sum(x["quantity"] * x["unit_target"] for x in data["items"] if x["tier"] == "core")
research = sum(x["quantity"] * x["unit_target"] for x in data["items"])
print(data["basis"])
for name, amount in (("Core", core), ("Research (includes Core)", research)):
    print(f"{name}: {amount:,.0f} VND; incl. contingency: {amount * (1 + data['contingency_fraction']):,.0f} VND")
print("Excluded: " + ", ".join(data["excluded"]))

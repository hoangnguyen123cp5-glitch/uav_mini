#!/usr/bin/env python3
"""Analyze Flix CSV logs (radians); does not command a drone or judge airworthiness."""
import argparse
import csv
import json
import math
import statistics


def analyze(path):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = ["t"] + [f"{kind}.{axis}" for kind in ("attitude", "attitudeTarget") for axis in "xyz"]
        if not reader.fieldnames or not set(fields).issubset(reader.fieldnames):
            raise ValueError("Missing time or attitude/attitudeTarget columns")
        rows = []
        for index, row in enumerate(reader, 2):
            try:
                values = {key: float(row[key]) for key in fields}
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid numeric data on line {index}") from exc
            if not all(math.isfinite(value) for value in values.values()):
                raise ValueError(f"Non-finite data on line {index}")
            rows.append(values)
    if len(rows) < 2:
        raise ValueError("At least two samples required")
    times = [r["t"] for r in rows]
    reordered = times != sorted(times)
    rows.sort(key=lambda r: r["t"])
    intervals = [b["t"] - a["t"] for a, b in zip(rows, rows[1:])]
    if min(intervals) <= 0:
        raise ValueError("Duplicate timestamps: use one continuous recording")
    dt = statistics.median(intervals)
    result = {"samples": len(rows), "duration_s": rows[-1]["t"] - rows[0]["t"],
              "median_log_rate_hz": 1 / dt, "max_sample_gap_s": max(intervals),
              "gaps_over_1_5_median": sum(x > 1.5 * dt for x in intervals),
              "reordered_ring_buffer": reordered, "tracking_error_deg": {}}
    for axis, name in zip("xyz", ("roll", "pitch", "yaw")):
        errors = [math.degrees(math.atan2(math.sin(r[f"attitude.{axis}"] - r[f"attitudeTarget.{axis}"]),
                                         math.cos(r[f"attitude.{axis}"] - r[f"attitudeTarget.{axis}"]))) for r in rows]
        result["tracking_error_deg"][name] = {
            "rmse": math.sqrt(statistics.mean(e * e for e in errors)),
            "max_abs": max(abs(e) for e in errors)}
    result["note"] = "Sample-based Euler tracking metrics; log rate is not control-loop rate. Not a flight pass/fail result."
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv_path")
    args = p.parse_args()
    try:
        print(json.dumps(analyze(args.csv_path), indent=2, allow_nan=False))
    except ValueError as exc:
        p.exit(1, f"Invalid log: {exc}\n")

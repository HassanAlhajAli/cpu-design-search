#!/usr/bin/env python3
"""Run and check the complete four-case MSHR pilot.

Requires a pinned gem5 build and a workload built by build_workload.sh.
Raw simulator files are kept even if a check fails; failed runs never enter
summary.json as successful measurements.
"""

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


PINNED_GEM5_COMMIT = "c8222cc67a399bfc01e8658dd14b30d5bfd634f9"
REPO = Path(__file__).resolve().parents[1]
RESULT_RE = re.compile(r"^RESULT (.+)$", re.MULTILINE)
EXIT_RE = re.compile(r"^GEM5_EXIT cause=(.+) tick=(\d+)$", re.MULTILINE)
STAT_BEGIN = "---------- Begin Simulation Statistics ----------"
STAT_END = "---------- End Simulation Statistics   ----------"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command, **kwargs):
    return subprocess.run(command, text=True, check=True, **kwargs)


def parse_result(output):
    matches = RESULT_RE.findall(output)
    if len(matches) != 1:
        raise ValueError(f"expected one RESULT line, found {len(matches)}")
    fields = dict(item.split("=", 1) for item in matches[0].split())
    if fields.get("loads") != "65536" or fields.get("passes") != "2":
        raise ValueError(f"unexpected work count: {fields}")
    return fields


def parse_roi_stats(path):
    text = path.read_text()
    if text.count(STAT_BEGIN) < 2:
        raise ValueError("missing measured-region dump or final statistics block")
    roi = text.split(STAT_BEGIN, 1)[1].split(STAT_END, 1)[0]
    stats = {}
    for line in roi.splitlines():
        pieces = line.split("#", 1)[0].split()
        if len(pieces) >= 2:
            stats[pieces[0]] = pieces[1]
    if "simTicks" not in stats or "system.cpu.numCycles" not in stats:
        raise ValueError("measured region lacks simTicks or CPU cycles")
    return stats


def read_config(path):
    data = json.loads(path.read_text())
    root = data.get("root", data)
    system = root.get("system", data.get("system"))
    if not isinstance(system, dict) or "l1d" not in system:
        raise ValueError("cannot find L1 data cache in resolved config.json")
    l1d = system["l1d"]
    if isinstance(l1d, list):
        l1d = l1d[0]
    return data, l1d


def one_value(stats, names):
    for name in names:
        if name in stats:
            return int(float(stats[name]))
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gem5-root", type=Path, default=os.environ.get("GEM5_ROOT"))
    parser.add_argument("--outdir", type=Path, default=REPO / "runs" / "mshr-pilot")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    if args.gem5_root is None:
        parser.error("set GEM5_ROOT or pass --gem5-root")
    gem5_root = args.gem5_root.resolve()
    gem5 = gem5_root / "build/RISCV/gem5.opt"
    binary = REPO / "build/mshr_chains_riscv"
    native = REPO / "build/mshr_chains_native"
    config_script = REPO / "configs/mshr_pilot.py"
    for path in (gem5, binary, native, config_script):
        if not path.is_file():
            parser.error(f"missing {path}; build gem5 and run build_workload.sh")
    revision = run_command(
        ["git", "-C", str(gem5_root), "rev-parse", "HEAD"], capture_output=True
    ).stdout.strip()
    if revision != PINNED_GEM5_COMMIT:
        parser.error(f"gem5 revision {revision} does not match pinned commit")
    if args.outdir.exists():
        parser.error(f"output directory already exists: {args.outdir}")
    args.outdir.mkdir(parents=True)

    native_results = {}
    for mode in ("dependent", "independent"):
        reference = run_command([str(native), mode], capture_output=True)
        native_results[mode] = parse_result(reference.stdout)
        if native_results[mode]["mode"] != mode:
            raise ValueError("native mode mismatch")
    (args.outdir / "native_reference.json").write_text(
        json.dumps(native_results, indent=2) + "\n"
    )

    summary = {
        "gem5_commit": revision,
        "gem5_binary_sha256": sha256(gem5),
        "workload_binary_sha256": sha256(binary),
        "config_script_sha256": sha256(config_script),
        "native_reference": native_results,
        "runs": [],
    }
    configs = {}
    for mode in ("dependent", "independent"):
        for mshrs in (2, 8):
            name = f"{mode}-mshrs{mshrs}"
            outdir = args.outdir / name
            outdir.mkdir()
            timing = outdir / "wall_time.txt"
            command = [
                "/usr/bin/time", "-f", "elapsed_seconds=%e\nmax_rss_kb=%M",
                "-o", str(timing), str(gem5), f"--outdir={outdir}",
                str(config_script), "--binary", str(binary),
                "--mode", mode, "--l1d-mshrs", str(mshrs),
            ]
            (outdir / "command.json").write_text(json.dumps(command, indent=2) + "\n")
            print(f"Running {name}", flush=True)
            try:
                process = subprocess.run(
                    command, cwd=REPO, text=True, capture_output=True,
                    timeout=args.timeout,
                )
            except subprocess.TimeoutExpired as error:
                (outdir / "failure.txt").write_text(f"timeout after {args.timeout}s\n")
                raise RuntimeError(f"{name} timed out") from error
            (outdir / "gem5_stdout.txt").write_text(process.stdout)
            (outdir / "gem5_stderr.txt").write_text(process.stderr)
            if process.returncode != 0:
                raise RuntimeError(f"{name} exited {process.returncode}; see raw output")
            result = parse_result(process.stdout)
            if result != native_results[mode]:
                raise ValueError(f"{name} differs from native reference: {result}")
            exits = EXIT_RE.findall(process.stdout)
            if len(exits) != 1 or "last active thread context" not in exits[0][0]:
                raise ValueError(f"{name} has unexpected gem5 exit: {exits}")
            stats = parse_roi_stats(outdir / "stats.txt")
            resolved, l1d = read_config(outdir / "config.json")
            if int(l1d["mshrs"]) != mshrs:
                raise ValueError(f"{name} resolved the wrong MSHR count")
            if l1d.get("prefetcher") not in (None, "Null"):
                raise ValueError(f"{name} unexpectedly enabled an L1 prefetcher")
            configs[(mode, mshrs)] = resolved
            cycles = int(float(stats["system.cpu.numCycles"]))
            sim_ticks = int(float(stats["simTicks"]))
            if cycles <= 0 or sim_ticks <= 0 or sim_ticks >= int(exits[0][1]):
                raise ValueError(f"{name} has invalid measured-region duration")
            l1_misses = one_value(stats, (
                "system.l1d.overallMisses::total",
                "system.l1d.demandMisses::total",
            ))
            l2_misses = one_value(stats, (
                "system.l2.overallMisses::total",
                "system.l2.demandMisses::total",
            ))
            if l1_misses is None or l2_misses is None:
                raise ValueError(f"{name} lacks cache miss counts")
            times = dict(line.split("=", 1) for line in timing.read_text().splitlines())
            row = {
                "name": name, "mode": mode, "l1d_mshrs": mshrs,
                "cycles": cycles, "sim_ticks": sim_ticks,
                "l1d_misses": l1_misses, "l2_misses": l2_misses,
                "l1d_mshr_stats": {
                    key: value for key, value in stats.items()
                    if key.startswith("system.l1d.") and "mshr" in key.lower()
                },
                "elapsed_seconds": float(times["elapsed_seconds"]),
                "max_rss_kb": int(times["max_rss_kb"]),
                "result": result,
            }
            summary["runs"].append(row)
            (args.outdir / "summary.partial.json").write_text(
                json.dumps(summary, indent=2) + "\n"
            )

        low = copy.deepcopy(configs[(mode, 2)])
        high = copy.deepcopy(configs[(mode, 8)])
        for data in (low, high):
            _, cache = read_config_dict(data)
            del cache["mshrs"]
        if low != high:
            raise ValueError(f"other resolved hardware settings changed for {mode}")

    (args.outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("All four runs passed correctness, statistics and configuration checks.")
    for row in summary["runs"]:
        print(f"{row['name']}: cycles={row['cycles']} "
              f"L1_misses={row['l1d_misses']} L2_misses={row['l2_misses']} "
              f"wall={row['elapsed_seconds']:.2f}s")


def read_config_dict(data):
    root = data.get("root", data)
    system = root.get("system", data.get("system"))
    l1d = system["l1d"]
    return data, l1d[0] if isinstance(l1d, list) else l1d


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"PILOT FAILED: {error}", file=sys.stderr)
        sys.exit(1)

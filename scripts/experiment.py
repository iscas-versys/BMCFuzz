#!/usr/bin/env python3
"""
Module-level BMCFuzz Experiment Runner

Supported projects : rocket_dcache, rocket_fpu
Supported methods  : fuzz, hypfuzz, bmcfuzz, allbmc
Supported cover    : toggle (12 h), line (6 h), mux (6 h)

Usage
-----
# Run a single method
python3 scripts/experiment.py -p rocket_dcache -c toggle --fuzz
python3 scripts/experiment.py -p rocket_dcache -c toggle --hypfuzz
python3 scripts/experiment.py -p rocket_dcache -c toggle --bmcfuzz
python3 scripts/experiment.py -p rocket_dcache -c toggle --allbmc

# Run multiple methods sequentially
python3 scripts/experiment.py -p rocket_dcache -c toggle --fuzz --hypfuzz --bmcfuzz --allbmc

# Generate comparison graph (reads saved logs)
python3 scripts/experiment.py -p rocket_dcache -c toggle --graph
python3 scripts/experiment.py -p rocket_dcache -c toggle --graph --fuzz --bmcfuzz
"""

import argparse
import os
import re
import signal
import subprocess
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ═══════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════

BMCFUZZ_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BMCFUZZ_PY = os.path.join(BMCFUZZ_HOME, "BMCFuzz.py")

PROJECTS = {"rocket_dcache", "rocket_fpu"}

COVER_TIMEOUTS = {
    "toggle": 12 * 3600,
    "line":    6 * 3600,
    "mux":     6 * 3600,
}

NOOP_HOME_SUFFIX = os.path.join("rtl", "rocket-modules")

METHODS = ("fuzz", "hypfuzz", "bmcfuzz", "allbmc")
METHOD_COLORS = {
    "fuzz":    "red",
    "hypfuzz": "blue",
    "bmcfuzz": "purple",
    "allbmc":  "green",
}

POLL_INTERVAL = 30  # seconds between coverage polls

# ═══════════════════════════════════════════════════════════════════
# Path helpers
# ═══════════════════════════════════════════════════════════════════

def _noop_home():
    return os.path.join(BMCFUZZ_HOME, NOOP_HOME_SUFFIX)


def _coverage_csv():
    """$NOOP_HOME/tmp/fuzz_coverage.csv"""
    return os.path.join(_noop_home(), "tmp", "fuzz_coverage.csv")


def _exp_dir(project, cover_type):
    d = os.path.join(BMCFUZZ_HOME, "experiment", project, cover_type)
    os.makedirs(d, exist_ok=True)
    return d


# ═══════════════════════════════════════════════════════════════════
# Command builders
# ═══════════════════════════════════════════════════════════════════

def _build_command(method, project, cover_type):
    """Build the BMCFuzz.py command string for *method*."""
    base = f"python3 {BMCFUZZ_PY} -p {project} -c {cover_type}"
    if method == "fuzz":
        return f"{base} --only-fuzz"
    if method == "hypfuzz":
        return base
    if method == "bmcfuzz":
        return f"{base} --snapshot"
    if method == "allbmc":
        return f"{base} --only-bmc"
    raise ValueError(f"Unknown method: {method}")


# ═══════════════════════════════════════════════════════════════════
# Coverage CSV reader
# ═══════════════════════════════════════════════════════════════════

def _read_coverage(csv_path):
    """Return coverage percentage from *csv_path*, or ``None``."""
    if not os.path.exists(csv_path):
        return None
    try:
        total = covered = 0
        with open(csv_path, "r") as f:
            for i, line in enumerate(f):
                if i == 0:
                    continue
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    total += 1
                    if parts[1].strip() == "1":
                        covered += 1
        return (covered / total * 100) if total else None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# Formatting helpers
# ═══════════════════════════════════════════════════════════════════

def _fmt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:>3}h{m:>3}m{s:>3}s"


def _kill_tree(pid):
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except ProcessLookupError:
        pass
    except Exception as exc:
        print(f"[EXP] Warning: kill_tree failed: {exc}")


# ═══════════════════════════════════════════════════════════════════
# Run experiment
# ═══════════════════════════════════════════════════════════════════

def run_experiment(method, project, cover_type, timeout, poll_interval):
    cmd = _build_command(method, project, cover_type)
    out_dir = _exp_dir(project, cover_type)
    log_path = os.path.join(out_dir, f"{method}.log")
    csv_path = _coverage_csv()

    print(f"[EXP] ─── {method} | {project} / {cover_type} ───")
    print(f"[EXP] Command : {cmd}")
    print(f"[EXP] Timeout : {_fmt_time(timeout)}")
    print(f"[EXP] Log     : {log_path}")

    # Remove old coverage so we track from scratch
    if os.path.exists(csv_path):
        os.remove(csv_path)

    process = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )

    records = []       # (elapsed_seconds, coverage_pct)
    last_cov = None
    start = time.time()

    try:
        while True:
            elapsed = time.time() - start
            if elapsed >= timeout:
                print(f"[EXP] Timeout reached ({_fmt_time(timeout)}), terminating")
                _kill_tree(process.pid)
                break

            ret = process.poll()
            if ret is not None:
                print(f"[EXP] Process exited with code {ret}")
                break

            cov = _read_coverage(csv_path)
            if cov is not None and cov != last_cov:
                records.append((elapsed, cov))
                last_cov = cov
                print(f"[EXP] {_fmt_time(elapsed)}  Coverage: {cov:.2f}%")

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\n[EXP] Interrupted, terminating")
        _kill_tree(process.pid)

    # Final coverage sample
    cov = _read_coverage(csv_path)
    if cov is not None:
        elapsed = time.time() - start
        if not records or records[-1][1] != cov:
            records.append((elapsed, cov))

    # Persist log
    with open(log_path, "w") as f:
        f.write("  0h  0m  0s Coverage:  0.00%\n")
        for t, c in records:
            f.write(f"{_fmt_time(t)} Coverage: {c:.2f}%\n")
        # End-line at timeout
        end_str = _fmt_time(timeout)
        final_cov = records[-1][1] if records else 0.0
        f.write(f"{end_str} Coverage: {final_cov:.2f}%\n")

    print(f"[EXP] {method} done — {len(records)} samples → {log_path}")


# ═══════════════════════════════════════════════════════════════════
# Graph generation
# ═══════════════════════════════════════════════════════════════════

def _parse_log(path):
    """Return list of (time_in_hours, coverage_pct)."""
    pattern = re.compile(r"(.*?)\s+Coverage:\s*([\d.]+)%")
    data = []
    with open(path, "r") as f:
        for line in f:
            m = pattern.match(line)
            if not m:
                continue
            time_str = m.group(1).strip()
            cov = float(m.group(2))
            hours = minutes = seconds = 0
            for part in time_str.split():
                if "h" in part:
                    hours = int(part.replace("h", ""))
                elif "m" in part:
                    minutes = int(part.replace("m", ""))
                elif "s" in part:
                    seconds = int(part.replace("s", ""))
            t = hours + minutes / 60 + seconds / 3600
            data.append((t, cov))
    return data


def generate_graph(project, cover_type, methods_to_plot):
    out_dir = _exp_dir(project, cover_type)

    plt.figure(figsize=(10, 6))
    min_cov, max_cov = 100.0, 0.0
    any_data = False

    for method in methods_to_plot:
        log_path = os.path.join(out_dir, f"{method}.log")
        if not os.path.exists(log_path):
            print(f"[GRAPH] Skipping {method}: {log_path} not found")
            continue
        data = _parse_log(log_path)
        if not data:
            continue
        any_data = True
        times, covs = zip(*data)
        plt.plot(times, covs, label=method,
                 color=METHOD_COLORS.get(method, "black"))
        for c in covs:
            if c > 0:
                min_cov = min(min_cov, c)
                max_cov = max(max_cov, c)

    if not any_data:
        print("[GRAPH] No data to plot")
        plt.close()
        return

    plt.title(f"{project} / {cover_type} — Coverage over time", fontsize=14)
    plt.xlabel("Time (hours)", fontsize=12)
    plt.ylabel("Coverage (%)", fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    full_path = os.path.join(out_dir, "coverage_full.png")
    plt.savefig(full_path, dpi=150)
    print(f"[GRAPH] Saved: {full_path}")

    if max_cov > min_cov:
        margin = max(1, (max_cov - min_cov) * 0.1)
        plt.ylim(max(0, min_cov - margin), min(100, max_cov + margin))
        zoom_path = os.path.join(out_dir, "coverage_zoom.png")
        plt.savefig(zoom_path, dpi=150)
        print(f"[GRAPH] Saved: {zoom_path}")

    plt.close()


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Module-level BMCFuzz Experiment Runner",
    )
    parser.add_argument(
        "-p", "--project", required=True,
        choices=sorted(PROJECTS),
        help="Project name",
    )
    parser.add_argument(
        "-c", "--cover-type", required=True,
        choices=sorted(COVER_TIMEOUTS.keys()),
        help="Coverage type (toggle=12h, line=6h, mux=6h)",
    )

    # Method flags
    parser.add_argument("--fuzz",    action="store_true", help="Run / plot fuzz baseline")
    parser.add_argument("--hypfuzz", action="store_true", help="Run / plot hypfuzz (BMC+fuzz)")
    parser.add_argument("--bmcfuzz", action="store_true", help="Run / plot bmcfuzz (BMC+fuzz+snapshot)")
    parser.add_argument("--allbmc",  action="store_true", help="Run / plot allbmc (pure BMC)")

    # Actions
    parser.add_argument("--graph", action="store_true",
                        help="Generate comparison graph from saved logs")

    # Overrides
    parser.add_argument("--poll-interval", type=int, default=POLL_INTERVAL,
                        help=f"Coverage poll interval in seconds (default: {POLL_INTERVAL})")
    parser.add_argument("--timeout", type=int, default=None,
                        help="Override default timeout (seconds)")

    args = parser.parse_args()

    # Collect requested methods
    requested = []
    if args.fuzz:    requested.append("fuzz")
    if args.hypfuzz: requested.append("hypfuzz")
    if args.bmcfuzz: requested.append("bmcfuzz")
    if args.allbmc:  requested.append("allbmc")

    timeout = args.timeout if args.timeout else COVER_TIMEOUTS[args.cover_type]

    if args.graph:
        methods_for_graph = requested if requested else list(METHODS)
        generate_graph(args.project, args.cover_type, methods_for_graph)
    elif requested:
        for method in requested:
            run_experiment(
                method, args.project, args.cover_type,
                timeout, args.poll_interval,
            )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Module-level BMCFuzz Experiment Runner

Supported projects : rocket_dcache, rocket_fpu
Supported methods  : fuzz, hypfuzz, bmcfuzz, allbmc
Supported cover    : toggle (2 h), line (1 h), mux (1 h)

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
import queue
import re
import signal
import subprocess
import sys
import threading
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ═══════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════

BMCFUZZ_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BMCFUZZ_PY = os.path.join(BMCFUZZ_HOME, "BMCFuzz.py")

PROJECTS = {"rocket_dcache", "rocket_fpu", "rocket_frontend"}

COVER_TIMEOUTS = {
    "toggle":  2 * 3600,
    "line":    1 * 3600,
    "mux":     1 * 3600,
}

NOOP_HOME_SUFFIX = os.path.join("rtl", "rocket-modules")

METHODS = ("fuzz", "hypfuzz", "bmcfuzz", "allbmc")
METHOD_COLORS = {
    "fuzz":    "red",
    "hypfuzz": "blue",
    "bmcfuzz": "purple",
    "allbmc":  "green",
}

POLL_INTERVAL = 30  # seconds between coverage polls (fuzz CSV mode)

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
# Coverage CSV reader (for fuzz method)
# ═══════════════════════════════════════════════════════════════════

def _read_coverage_csv(csv_path):
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
# Formatting / process helpers
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


def _stderr_reader(pipe, q):
    """Read lines from *pipe* and push them into *q*. Sentinel ``None``."""
    try:
        for line in iter(pipe.readline, ""):
            q.put(line)
    except ValueError:
        pass
    finally:
        q.put(None)


# ═══════════════════════════════════════════════════════════════════
# Regex patterns for output parsing
# ═══════════════════════════════════════════════════════════════════

# bmcfuzz / hypfuzz: "Coverage: 3097/3309 (93.59%)"
_RE_HYBRID_COV = re.compile(r"Coverage:\s*(\d+)/(\d+)\s*\(([\d.]+)%\)")

# allbmc: "Point 3121 successfully verified"
_RE_BMC_POINT = re.compile(r"Point\s+(\d+)\s+successfully verified")

# allbmc: "total points: 3309"
_RE_TOTAL_POINTS = re.compile(r"total points:\s*(\d+)", re.IGNORECASE)

# fuzz (if capturing fuzzer stdout): "Total Coverage:       21.275%"
_RE_FUZZ_COV = re.compile(r"Total Coverage:\s*([\d.]+)%")


# ═══════════════════════════════════════════════════════════════════
# Tick helpers
# ═══════════════════════════════════════════════════════════════════

def _flush_ticks(records, start, next_tick, current_cov, poll_interval):
    """Emit scheduled tick records up to *now*. Returns updated next_tick."""
    now = time.time()
    while next_tick <= now:
        tick_elapsed = next_tick - start
        records.append((tick_elapsed, current_cov))
        print(f"[EXP] {_fmt_time(tick_elapsed)}  Coverage: {current_cov:.2f}%")
        next_tick += poll_interval
    return next_tick


# ═══════════════════════════════════════════════════════════════════
# Run experiment — fuzz (CSV poll)
# ═══════════════════════════════════════════════════════════════════

def _run_fuzz(cmd, timeout, poll_interval, log_path):
    """Run fuzz baseline, monitoring coverage via CSV file.

    Records a sample at every *poll_interval* tick (even if unchanged).
    CSV updates between ticks are recorded as supplementary entries.
    """
    csv_path = _coverage_csv()
    if os.path.exists(csv_path):
        os.remove(csv_path)

    process = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )

    records = []
    current_cov = 0.0
    start = time.time()
    next_tick = start + poll_interval

    try:
        while True:
            now = time.time()
            elapsed = now - start
            if elapsed >= timeout:
                print(f"[EXP] Timeout reached ({_fmt_time(timeout)}), terminating")
                _kill_tree(process.pid)
                break
            if process.poll() is not None:
                print(f"[EXP] Process exited with code {process.returncode}")
                break

            # Read CSV — supplementary record on change
            cov = _read_coverage_csv(csv_path)
            if cov is not None and cov != current_cov:
                current_cov = cov
                records.append((elapsed, current_cov))
                print(f"[EXP] {_fmt_time(elapsed)}  * Coverage: {current_cov:.2f}%")

            # Scheduled ticks
            next_tick = _flush_ticks(records, start, next_tick,
                                     current_cov, poll_interval)

            sleep_dur = max(0.5, min(next_tick - time.time(), poll_interval))
            time.sleep(sleep_dur)
    except KeyboardInterrupt:
        print("\n[EXP] Interrupted, terminating")
        _kill_tree(process.pid)

    _save_log(log_path, records, timeout)


# ═══════════════════════════════════════════════════════════════════
# Run experiment — bmcfuzz / hypfuzz (capture "Coverage: N/M (X%)")
# ═══════════════════════════════════════════════════════════════════

def _run_hybrid(cmd, timeout, poll_interval, log_path):
    """Run bmcfuzz or hypfuzz, capturing Coverage lines from stderr.

    Scheduled tick records every *poll_interval*; coverage updates
    from stderr are recorded as supplementary entries.
    """
    process = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True, bufsize=1,
        preexec_fn=os.setsid,
    )

    q = queue.Queue()
    reader = threading.Thread(target=_stderr_reader, args=(process.stderr, q))
    reader.daemon = True
    reader.start()

    records = []
    current_cov = 0.0
    start = time.time()
    next_tick = start + poll_interval

    try:
        while True:
            now = time.time()
            elapsed = now - start
            if elapsed >= timeout:
                print(f"[EXP] Timeout reached ({_fmt_time(timeout)}), terminating")
                _kill_tree(process.pid)
                break

            # Flush scheduled ticks
            next_tick = _flush_ticks(records, start, next_tick,
                                     current_cov, poll_interval)

            # Read stderr with short timeout
            wait = max(0.1, min(1.0, next_tick - time.time()))
            try:
                line = q.get(timeout=wait)
            except queue.Empty:
                continue

            if line is None:
                print(f"[EXP] Process exited with code {process.wait()}")
                break

            # Supplementary record on coverage change
            m = _RE_HYBRID_COV.search(line)
            if m:
                cov = float(m.group(3))
                if cov != current_cov:
                    current_cov = cov
                    elapsed = time.time() - start
                    records.append((elapsed, current_cov))
                    print(f"[EXP] {_fmt_time(elapsed)}  * Coverage: "
                          f"{m.group(1)}/{m.group(2)} ({cov:.2f}%)")

    except KeyboardInterrupt:
        print("\n[EXP] Interrupted, terminating")
        _kill_tree(process.pid)

    _save_log(log_path, records, timeout)


# ═══════════════════════════════════════════════════════════════════
# Run experiment — allbmc (count "Point N successfully verified")
# ═══════════════════════════════════════════════════════════════════

def _run_allbmc(cmd, timeout, poll_interval, log_path):
    """Run pure BMC, counting successfully verified points from stderr.

    Scheduled tick records every *poll_interval*; each newly verified
    point is recorded as a supplementary entry.
    """
    process = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True, bufsize=1,
        preexec_fn=os.setsid,
    )

    q = queue.Queue()
    reader = threading.Thread(target=_stderr_reader, args=(process.stderr, q))
    reader.daemon = True
    reader.start()

    records = []
    current_cov = 0.0
    total_points = 0
    verified = set()
    start = time.time()
    next_tick = start + poll_interval

    try:
        while True:
            now = time.time()
            elapsed = now - start
            if elapsed >= timeout:
                print(f"[EXP] Timeout reached ({_fmt_time(timeout)}), terminating")
                _kill_tree(process.pid)
                break

            # Flush scheduled ticks
            next_tick = _flush_ticks(records, start, next_tick,
                                     current_cov, poll_interval)

            # Read stderr with short timeout
            wait = max(0.1, min(1.0, next_tick - time.time()))
            try:
                line = q.get(timeout=wait)
            except queue.Empty:
                continue

            if line is None:
                print(f"[EXP] Process exited with code {process.wait()}")
                break

            # Capture total points count
            if total_points == 0:
                tm = _RE_TOTAL_POINTS.search(line)
                if tm:
                    total_points = int(tm.group(1))
                    print(f"[EXP] Total points: {total_points}")

            # Supplementary record on newly verified point
            pm = _RE_BMC_POINT.search(line)
            if pm and total_points > 0:
                point_id = int(pm.group(1))
                if point_id not in verified:
                    verified.add(point_id)
                    current_cov = len(verified) / total_points * 100
                    elapsed = time.time() - start
                    records.append((elapsed, current_cov))
                    print(f"[EXP] {_fmt_time(elapsed)}  * Verified: "
                          f"{len(verified)}/{total_points} ({current_cov:.2f}%)")

    except KeyboardInterrupt:
        print("\n[EXP] Interrupted, terminating")
        _kill_tree(process.pid)

    _save_log(log_path, records, timeout)


# ═══════════════════════════════════════════════════════════════════
# Log persistence
# ═══════════════════════════════════════════════════════════════════

def _save_log(log_path, records, timeout):
    """Write time-coverage records to *log_path*, deduplicating identical points."""
    with open(log_path, "w") as f:
        f.write("  0h  0m  0s Coverage:  0.00%\n")
        prev_t = ""
        prev_cov = 0.0
        written = 0
        for t, c in records:
            if prev_t == _fmt_time(t) and c == prev_cov:
                continue
            f.write(f"{_fmt_time(t)} Coverage: {c:.2f}%\n")
            prev_t = _fmt_time(t)
            prev_cov = c
            written += 1
        end_str = _fmt_time(timeout)
        final_cov = records[-1][1] if records else 0.0
        f.write(f"{end_str} Coverage: {final_cov:.2f}%\n")
    print(f"[EXP] {written} unique samples (from {len(records)}) saved → {log_path}")


# ═══════════════════════════════════════════════════════════════════
# Top-level run dispatcher
# ═══════════════════════════════════════════════════════════════════

def run_experiment(method, project, cover_type, timeout, poll_interval):
    cmd = _build_command(method, project, cover_type)
    out_dir = _exp_dir(project, cover_type)
    log_path = os.path.join(out_dir, f"{method}.log")

    print(f"[EXP] ─── {method} | {project} / {cover_type} ───")
    print(f"[EXP] Command : {cmd}")
    print(f"[EXP] Timeout : {_fmt_time(timeout)}")
    print(f"[EXP] Log     : {log_path}")

    if method == "fuzz":
        _run_fuzz(cmd, timeout, poll_interval, log_path)
    elif method in ("hypfuzz", "bmcfuzz"):
        _run_hybrid(cmd, timeout, poll_interval, log_path)
    elif method == "allbmc":
        _run_allbmc(cmd, timeout, poll_interval, log_path)
    else:
        raise ValueError(f"Unknown method: {method}")

    print(f"[EXP] ─── {method} done ───\n")


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
        help="Coverage type (toggle=2h, line=1h, mux=1h)",
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

"""
BMCFuzz - Bounded Model Checking with Coverage-Guided Fuzzing

Modes:
  (default)     BMC-CGF hybrid loop
  --snapshot    BMC-CGF with snapshot-driven two-level loop
  --only-fuzz   Pure fuzzing baseline (no BMC)
  --only-bmc    Pure BMC baseline (no fuzzer)
"""

import argparse

from utils.logger import log_init, clear_logs
from core.scheduler import Scheduler
from core.config import Config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BMCFuzz")
    parser.add_argument(
        "-p", "--project", required=True,
        help="Project name (e.g. nutshell, rocket, rocket_dcache, rocket_fpu)",
    )
    parser.add_argument(
        "-c", "--cover-type", default="toggle",
        help="Coverage type (default: toggle)",
    )
    parser.add_argument(
        "-s", "--solver", default="sat",
        help="Solver mode (default: sat)",
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--snapshot", action="store_true",
        help="Enable snapshot loop (two-level loop mode)",
    )
    mode_group.add_argument(
        "--only-fuzz", action="store_true",
        help="Pure fuzzing — skip BMC entirely",
    )
    mode_group.add_argument(
        "--only-bmc", action="store_true",
        help="Pure BMC — skip fuzzer entirely",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # clear_logs(log_dir=Config.BMCFUZZ_HOME)
    log_init(prefix=f"bmcfuzz_{args.project}")

    scheduler = Scheduler(
        project_name=args.project,
        cover_type=args.cover_type,
        solver_mode=args.solver,
        run_snapshot=args.snapshot,
        only_fuzz=args.only_fuzz,
        only_bmc=args.only_bmc,
    )

    scheduler.run()


if __name__ == "__main__":
    main()

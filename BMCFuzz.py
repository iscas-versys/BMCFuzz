"""
BMCFuzz - Bounded Model Checking with Coverage-Guided Fuzzing
"""

import argparse

from utils.logger import log_init, clear_logs
from core.scheduler import Scheduler
from core.config import Config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BMCFuzz")
    parser.add_argument(
        "-p", "--project", required=True,
        help="Project name (e.g. nutshell, rocket, boom)",
    )
    parser.add_argument(
        "-c", "--cover-type", default="toggle",
        help="Coverage type (default: toggle)",
    )
    parser.add_argument(
        "-s", "--solver", default="smt",
        help="Solver mode (default: smt)",
    )
    parser.add_argument(
        "--snapshot", action="store_true",
        help="Enable snapshot loop (two-level loop mode)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    clear_logs(log_dir=Config.BMCFUZZ_HOME)
    log_init(prefix=f"bmcfuzz_{args.project}")


    scheduler = Scheduler(project_name=args.project, cover_type=args.cover_type, solver_mode=args.solver, run_snapshot=args.snapshot)

    scheduler.run()


if __name__ == "__main__":
    main()

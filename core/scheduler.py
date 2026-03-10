"""
BMCFuzz Scheduler with Two-Level Loops

This module implements the formal verification scheduler with two-level loops:
1. Snapshot Loop: Selects snapshots based on scoring and initializes RTL
2. BMC-CGF Loop: Runs BMC (Bounded Model Checking) with CGF (Cover-Guided Fuzzing)
"""

import os
import shutil
from typing import List, Optional, Dict, Tuple
from pathlib import Path

from core.config import Config
from core.coverage import CoverageManager

from formal.executor import FormalExecutor
from formal.point_selector import PointSelector
from formal.seed_generator import SeedGenerator

from utils.logger import BMCFuzzLogger

from initialization.snapshot_loader import SnapshotLoader
from initialization.snapshot_manager import SnapshotManager

from rtl.rtl_init import get_rtl_manager, initialize_rtl

class Scheduler:
    """
    BMCFuzz Scheduler with two-level loops
    
    Level 1 - Snapshot Loop:
        1. Select best snapshot based on scoring
        2. Load snapshot and initialize RTL
        3. Run BMC-CGF loop
    
    Level 2 - BMC-CGF Loop:
        1. Run BMC (formal verification) using FormalExecutor
        2. Run CGF (cover-guided fuzzing)
        3. Update coverage
        4. Repeat until no more points or max iterations
    """
    
    def __init__(self, project_name: str, cover_type: str = "toggle",
                 solver_mode: str = "smt", run_snapshot: bool = True,
                 only_fuzz: bool = False, only_bmc: bool = False):
        self.logger = BMCFuzzLogger.get_logger("Scheduler")

        # Configuration
        self.project_name = project_name
        self.cover_type = cover_type
        self.solver_mode = solver_mode
        self.run_snapshot = run_snapshot
        self.only_fuzz = only_fuzz
        self.only_bmc = only_bmc
        
        # Formal components
        self.executor: Optional[FormalExecutor] = None
        self.point_selector: Optional[PointSelector] = None
        
        # Initialization components
        self.snapshot_loader: Optional[SnapshotLoader] = None
        self.snapshot_manager: Optional[SnapshotManager] = None
        self.current_snapshot_id: Optional[int] = None

        # State tracking
        self.coverage: Optional[CoverageManager] = None
        self.total_points = 0
        self.cover_points: List[Tuple] = []

        # RTL file paths (set by init_formal)
        self.formal_rtl_file: Optional[str] = None
        self.fuzzer_rtl_file: Optional[str] = None

    def run(self) -> None:
        """
        Main entry point: initialize all components and run the full loop.

        Flow depends on mode:
          --only-fuzz : build RTL + fuzzer, run fuzzer only
          --only-bmc  : build RTL + formal, run BMC only
          --snapshot  : full two-level snapshot loop
          (default)   : BMC-CGF hybrid loop
        """
        self.logger.info(
            f"BMCFuzz starting: project={self.project_name}, "
            f"cover_type={self.cover_type}, solver={self.solver_mode}, "
            f"snapshot={self.run_snapshot}, "
            f"only_fuzz={self.only_fuzz}, only_bmc={self.only_bmc}"
        )

        # 1. Initialize global RTL manager
        initialize_rtl(self.project_name, self.cover_type)
        rtl_init = get_rtl_manager()

        # ── Fuzz-only mode ────────────────────────────────────────────
        if self.only_fuzz:
            if not rtl_init.build_rtl(cover_type=self.cover_type):
                self.logger.error("RTL build failed, aborting")
                return
            if not rtl_init.build_fuzzer():
                self.logger.error("Fuzzer build failed, aborting")
                return
            self.run_fuzz_only()
            self.logger.info("BMCFuzz (fuzz-only) finished")
            return

        # ── BMC-only mode ─────────────────────────────────────────────
        if self.only_bmc:
            if not self.init_formal():
                self.logger.error("Formal initialization failed, aborting")
                return
            self.run_bmc_only()
            self.logger.info("BMCFuzz (bmc-only) finished")
            return

        # ── Normal hybrid modes ───────────────────────────────────────
        # 2. Initialize formal verification components
        if not self.init_formal():
            self.logger.error("Formal initialization failed, aborting")
            return

        # 3. Build fuzzer
        if not rtl_init.build_fuzzer():
            self.logger.error("Fuzzer build failed, aborting")
            return

        # 4. Run the appropriate loop
        if self.run_snapshot:
            if not self.init_initialization():
                self.logger.error("Snapshot initialization failed, aborting")
                return
            self.run_snapshot_loop()
        else:
            self.run_bmc_cgf()

        self.logger.info("BMCFuzz finished")

    def init_formal(self) -> bool:
        """
        Initialize formal verification components

        Builds RTL, prepares formal RTL directory, initializes coverage,
        point selector, and executor. Cover point metadata is obtained from
        rtl_init; cover/assert statements are then injected into the RTL.

        Args:
            rtl_init: RTLInit instance

        Returns:
            True if initialization succeeded, False otherwise
        """
        self.logger.info("Initializing formal verification")

        # 1. Build RTL source
        rtl_init = get_rtl_manager()
        shutil.rmtree(Config.FORMAL_RUN_DIR, ignore_errors=True)
        os.makedirs(Config.FORMAL_RUN_DIR, exist_ok=True)
        if not rtl_init.build_rtl(cover_type=self.cover_type, run_snapshot=self.run_snapshot):
            self.logger.error("RTL build failed")
            return False

        # 2. Copy and prepare formal RTL directory
        self.formal_rtl_file = rtl_init.prepare_formal_rtl()
        self.fuzzer_rtl_file = rtl_init.get_rtl_info()["rtl_file"]

        # 3. Collect cover point metadata
        cover_points_name: List[Tuple[str, str]] = rtl_init.get_cover_points_name()
        self.cover_points = cover_points_name
        self.total_points = len(cover_points_name)
        self.logger.info(f"Total cover points: {self.total_points}")

        # 4. Build module index mapping for PointSelector
        module_name_to_idx: Dict[str, int] = {}
        point2module: List[int] = []
        for module_name, _ in cover_points_name:
            if module_name not in module_name_to_idx:
                module_name_to_idx[module_name] = len(module_name_to_idx)
            point2module.append(module_name_to_idx[module_name])
        module_num = len(module_name_to_idx)

        # 5. Initialize state tracking components
        self.coverage = CoverageManager(self.total_points)

        self.point_selector = PointSelector()
        self.point_selector.init(module_num, point2module)

        # 6. Initialize executor
        self.executor = FormalExecutor()
        self.executor.configure(
            project_name=self.project_name,
            mode=self.solver_mode,
            cover_type=self.cover_type,
        )

        # 7. Wire up seed generator as executor callback
        seed_gen = SeedGenerator()
        seed_gen.configure(project_name=self.project_name, mode=self.solver_mode)
        self.executor.set_seed_generator(seed_gen)

        # 8a. Convert RTL assert -> assume (debug: prevents SAT traces
        #     from violating RTL invariants when replayed in the fuzzer)
        # self.executor.convert_assert_to_assume(self.formal_rtl_file)

        # 8b. Inject cover/assert statements into formal RTL
        if not self.executor.add_cover_statements(self.formal_rtl_file):
            self.logger.error("Failed to add cover statements to RTL")
            return False

        # 9. If no snapshot mode, insert initial assume statements for registers
        if not self.run_snapshot:
            self.executor.add_reg_initial_statements(self.formal_rtl_file)

        self.logger.info("Formal initialization completed successfully")
        return True

    def do_bmc(self) -> List[int]:
        """
        Run the BMC verification loop

        Repeatedly selects uncovered points via point_selector and submits
        them to the executor for bounded model checking. The loop exits when:
          - point_selector has no remaining points to select, OR
          - the executor covers at least one point (seeds ready for fuzzer)

        Coverage is updated before returning.

        Returns:
            List of newly covered point IDs (empty if none were covered)
        """
        self.logger.info("Starting BMC")

        while True:
            # Clean up formal_run dir
            self.executor.cleanup()
            
            # Exit if all points have been selected already
            if self.point_selector.uncovered_points_num == 0:
                self.logger.info("No remaining uncovered points; exiting BMC loop")
                return []

            # Select a batch of points to verify
            selected_points = self.point_selector.generate_cover_points()
            if not selected_points:
                self.logger.info("Point selector returned no points; exiting BMC loop")
                return []

            formal_log_file = os.path.join(Config.LOG_DIR, f"formal_{self.project_name}.log")
            with open(formal_log_file, "w") as f:
                f.write("Selected points for BMC:\n")
                for idx in selected_points:
                    point_name = self.cover_points[idx]
                    f.write(f"  - {idx}: {point_name}\n")
                f.write("\nUnselected points remaining:\n")
                unselected_points = self.point_selector.get_unselected_points()
                for idx in unselected_points:
                    point_name = self.cover_points[idx]
                    f.write(f"  - {idx}: {point_name}\n")

            # Generate sby files and run BMC
            self.executor.generate_sby_files(selected_points)
            result = self.executor.execute(selected_points)
            # result = {"covered_points": [], "execution_time": 0}
            covered_points: List[int] = result["covered_points"]

            if covered_points:
                # Update coverage and exit - seeds have been generated for the fuzzer
                # self.coverage.update_formal(covered_points)
                self.coverage.generate_cover_file()
                self.coverage.update_formal_cover_rate(
                    len(covered_points), result["execution_time"]
                )
                self.logger.info(
                    f"BMC covered {len(covered_points)} point(s); exiting loop"
                )
                return covered_points

    def do_fuzz(self) -> List[int]:
        """
        Run one CGF (Cover-Guided Fuzzing) iteration using BMC-generated seeds

        Uses the corpus produced by the seed generator (stored in the executor's
        corpus directory) and the current formal coverage rate to guide the fuzzer.
        After fuzzing, updates coverage and notifies the point selector so that
        any newly covered points are removed from the uncovered set.

        Returns:
            List of newly covered point IDs discovered by the fuzzer
        """
        rtl_init = get_rtl_manager()
        corpus_dir = Config.CORPUS_DIR
        formal_cover_rate = self.coverage.get_formal_cover_rate()

        self.logger.info(
            f"Starting fuzzer with corpus={corpus_dir}, "
            f"formal_cover_rate={formal_cover_rate:.4f}"
        )

        rtl_init.cleanup()

        rtl_init.run_fuzzer(
            corpus_dir=corpus_dir,
            formal_cover_rate=formal_cover_rate,
            snapshot_id=self.current_snapshot_id if self.run_snapshot else None,
            run_snapshot=self.run_snapshot,
        )

        # Retrieve per-point coverage status from the fuzzer run
        fuzzer_result = rtl_init.get_fuzzer_results()
        fuzz_coverage = fuzzer_result["coverage"]
        fuzz_points: List[int] = fuzz_coverage.get("points", [])

        # Update global coverage; get back the IDs of newly covered points
        new_covered = self.coverage.update_fuzz(fuzz_points)
        self.logger.info(f"Fuzzer new covered points: {new_covered}")
        self.coverage.display_coverage()

        if new_covered:
            self.logger.info(f"Fuzzer covered {len(new_covered)} new point(s)")
            # Sync point selector: remove any now-covered unselected points
            self.point_selector.update(self.coverage.cover_points)
        else:
            self.logger.warning("Fuzzer covered no new points this round")

        # Collect new snapshots for the snapshot manager
        if self.snapshot_manager is not None:
            snapshots = fuzzer_result.get("snapshots", [])
            if snapshots:
                added = self.snapshot_manager.add_snapshots(snapshots)
                self.logger.info(f"Added {added} snapshot(s) to manager")

        return new_covered

    # =========================================================================
    # Standalone modes (fuzz-only / bmc-only)
    # =========================================================================

    def run_fuzz_only(self) -> None:
        """
        Run fuzzer continuously without BMC.

        Uses the initial corpus and runs with no max_runs limit.
        Coverage is tracked by the fuzzer binary itself
        (written to $NOOP_HOME/tmp/fuzz_coverage.csv).
        """
        self.logger.info("Starting fuzz-only mode")

        rtl_init = get_rtl_manager()
        rtl_init.run_fuzzer(
            corpus_dir=Config.INIT_CORPUS_DIR,
            max_runs=0,
            dump_snapshot=False,
            only_fuzz=True
        )

        self.logger.info("Fuzz-only mode finished")

    def run_bmc_only(self) -> None:
        """
        Run pure BMC verification on all cover points without fuzzing.

        Iterates over all point batches via the point selector. For each
        batch, runs formal verification and records covered points. The
        loop exits when all points have been tried.
        """
        self.logger.info("Starting BMC-only mode")

        while True:
            self.executor.cleanup()

            if self.point_selector.uncovered_points_num == 0:
                self.logger.info("All points processed; exiting BMC-only loop")
                break

            # selected_points = self.point_selector.generate_cover_points()
            selected_points = list(range(self.total_points))
            if not selected_points:
                self.logger.info("No more points to select; exiting BMC-only loop")
                break

            self.executor.generate_sby_files(selected_points)
            result = self.executor.execute(selected_points)
            covered_points: List[int] = result["covered_points"]

            if covered_points:
                self.coverage.generate_cover_file()
                self.coverage.update_formal_cover_rate(
                    len(covered_points), result["execution_time"]
                )
                self.logger.info(
                    f"BMC covered {len(covered_points)} point(s): "
                    f"{sorted(covered_points)}"
                )
                self.coverage.display_coverage()

        self.logger.info(
            f"BMC-only finished. Coverage: "
            f"{self.coverage.get_covered_num()}/{self.total_points}"
        )

    def run_bmc_cgf(self) -> None:
        """
        Run the BMC-CGF outer loop until no uncovered points remain

        Each iteration:
          1. BMC phase  - select uncovered points and run formal verification;
                          exit the outer loop if the selector is exhausted.
          2. CGF phase  - run the fuzzer using BMC-generated seeds and update
                          coverage / point selector state.

        The loop repeats until do_bmc signals that there are no more points to
        select (returns an empty list).
        """
        self.logger.info("Starting BMC-CGF loop")

        while True:
            bmc_covered = self.do_bmc()
            self.logger.info(
                f"BMC phase covered {len(bmc_covered)} point(s):{sorted(bmc_covered)}" 
            )

            if not bmc_covered:
                self.logger.info(
                    "BMC-CGF loop complete: point selector exhausted"
                )
                break

            self.do_fuzz()

            # exit(0)  # --- TEMP EXIT ---

        self.logger.info(
            f"BMC-CGF finished. Total coverage: "
            f"{self.coverage.get_covered_num()}/{self.total_points}"
        )

        # reset uncovered points
        self.point_selector.reset_uncovered_points(self.coverage.get_uncovered_points())

    # =========================================================================
    # Initialization (Snapshot Loader + Manager)
    # =========================================================================

    def init_initialization(self) -> bool:
        """
        Initialize snapshot_loader and snapshot_manager.

        Must be called after init_formal() so that formal_rtl_file and
        fuzzer_rtl_file are available.

        - snapshot_loader: registered with both formal and fuzzer SV files,
          then calls prepare_rtl() to generate template initial-block copies.
        - snapshot_manager: created with project_name to auto-select the
          appropriate scorer (CSRScorer for nutshell/rocket/boom).

        Returns:
            True on success, False on failure.
        """
        self.logger.info("Initializing snapshot components")

        if not self.formal_rtl_file or not self.fuzzer_rtl_file:
            self.logger.error(
                "RTL file paths not set — call init_formal() first"
            )
            return False

        # 1. Create SnapshotLoader with both SV files
        self.snapshot_loader = SnapshotLoader(
            sv_files={
                "formal": self.formal_rtl_file,
                "fuzzer": self.fuzzer_rtl_file,
            },
            project_name=self.project_name,
        )

        # 1. Disable reset in FormalTop.sv (snapshot provides initial state)
        formal_top = Path(self.formal_rtl_file).parent / "FormalTop.sv"
        if formal_top.exists():
            content = formal_top.read_text()
            content = content.replace(
                "reg reg_reset = 1'b1;", "reg reg_reset = 1'b0;"
            )
            formal_top.write_text(content)
            self.logger.info(f"Disabled reset in {formal_top}")

        # 2. Generate template initial-block copies (all regs = 0)
        prepared = self.snapshot_loader.prepare_rtl()
        if prepared is None:
            self.logger.error("Failed to prepare RTL with template initial blocks")
            return False
        self.logger.info(f"Prepared template RTL: {prepared}")

        # 3. Create SnapshotManager (scorer auto-selected by project_name)
        self.snapshot_manager = SnapshotManager(
            snapshot_dir=Config.SNAPSHOT_DIR,
            project_name=self.project_name,
            prefer_reset_threshold=0,
        )

        self.logger.info("Snapshot components initialized successfully")
        return True

    def load_snapshot(self, wave_file: str) -> bool:
        """
        Load a waveform snapshot into both formal and fuzzer RTL files.

        Replaces the original formal_rtl_file and fuzzer_rtl_file with
        snapshot-loaded copies (initial blocks filled with waveform values),
        then rebuilds the fuzzer.

        Args:
            wave_file: Path to the waveform file (VCD or FST)

        Returns:
            True on success, False on failure.
        """
        self.logger.info(f"Loading snapshot from {wave_file}")

        # Generate snapshot-loaded SV files, writing directly over the originals
        results = self.snapshot_loader.load_snapshot(
            wave_file=wave_file,
            output_map={
                "formal": self.formal_rtl_file,
                "fuzzer": self.fuzzer_rtl_file,
            },
        )
        if results is None:
            self.logger.error("Failed to load snapshot into RTL files")
            return False

        # Rebuild fuzzer with the updated RTL
        rtl_init = get_rtl_manager()
        if not rtl_init.build_fuzzer():
            self.logger.error("Fuzzer rebuild failed after snapshot load")
            return False

        self.logger.info("Snapshot loaded and fuzzer rebuilt")
        return True

    # =========================================================================
    # Snapshot Loop (Level 1)
    # =========================================================================

    def run_snapshot_loop(self) -> None:
        """
        Run the top-level snapshot loop.

        Each iteration:
          1. Select the best snapshot from snapshot_manager.
          2. Load the snapshot (replace RTL files, rebuild fuzzer).
          3. Run a full BMC-CGF loop.
          4. (Snapshots produced by the fuzzer are automatically fed back
             into snapshot_manager via do_fuzz.)

        The first iteration runs fuzz_init (initial corpus, 3000 runs) to
        seed the snapshot pool.  The loop exits when snapshot_manager has
        no viable candidate left.
        """
        self.logger.info("Starting snapshot loop")

        # First round: initial fuzzing to populate snapshot pool
        if Config.FUZZER_INIT:
            self.fuzz_init()
        else:
            self.logger.info("FUZZER_INIT is False - skipping initial fuzzing, running BMC-CGF without snapshot")
            self.run_bmc_cgf()

        # Subsequent rounds: pick best snapshot -> load -> BMC-CGF
        while True:
            best = self.snapshot_manager.select_best()
            if best is None:
                self.logger.info(
                    "No more viable snapshots - exiting snapshot loop"
                )
                break

            self.logger.info(
                f"Selected snapshot {best['id']}(score={best['score']})"
            )
            self.logger.info(f"Snapshot details: {best['details']}")

            self.current_snapshot_id = best["id"]
            if not self.load_snapshot(best["wave_path"]):
                self.logger.error(
                    f"Failed to load snapshot {best['id']}, skipping"
                )
                continue

            self.run_bmc_cgf()

        self.coverage.display_coverage()
        self.logger.info("Snapshot loop finished")

    def fuzz_init(self) -> None:
        """
        Run an initial fuzzing pass to populate the snapshot pool.

        Uses the seed corpus from Config.INIT_CORPUS_DIR with a fixed
        3000 runs.  Coverage and snapshots are collected the same way
        as do_fuzz().
        """
        rtl_init = get_rtl_manager()

        self.logger.info(
            f"Running initial fuzzing: corpus={Config.INIT_CORPUS_DIR}, "
            f"max_runs={Config.FUZZER_INIT_RUNS}"
        )

        rtl_init.run_fuzzer(
            corpus_dir=Config.INIT_CORPUS_DIR,
            max_runs=Config.FUZZER_INIT_RUNS,
        )

        fuzzer_result = rtl_init.get_fuzzer_results()

        # Update coverage
        fuzz_coverage = fuzzer_result["coverage"]
        fuzz_points: List[int] = fuzz_coverage.get("points", [])
        new_covered = self.coverage.update_fuzz(fuzz_points)
        self.coverage.display_coverage()

        self.logger.info(
            f"Initial fuzz covered {len(new_covered)} point(s)"
        )
        self.point_selector.update(fuzz_points)

        # Collect snapshots into manager
        snapshots = fuzzer_result.get("snapshots", [])
        if snapshots:
            added = self.snapshot_manager.add_snapshots(snapshots)
            self.logger.info(f"Initial fuzz produced {added} snapshot(s)")

        self.logger.info("Initial fuzzing complete")


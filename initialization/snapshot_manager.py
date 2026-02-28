"""
Snapshot Manager

Two responsibilities:

  1. add_snapshots(snapshots)
       Ingest [{flag, wave, snapshot}, ...] from rtl_init.get_snapshots().
       Scores each via scorer, drops zero-score and duplicate entries
       (duplicates detected by scorer.get_identifier), copies the kept
       wave and snapshot files to snapshot_dir with auto-incrementing index.

  2. select_best()
       Picks the highest-scoring snapshot, decays its scorer weights,
       recalculates scores for the remaining pool, and returns the
       snapshot info dict.  Returns None when the pool is empty or every
       score is at or below the reset threshold.
"""

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from utils.logger import BMCFuzzLogger
from initialization.scorer import Scorer, create_scorer


class SnapshotManager:
    """
    Manages scored snapshots and selects the best candidate.

    Snapshot dict format (from rtl_init.get_snapshots()):
        {"flag": <csv_path>, "wave": <vcd_path>, "snapshot": <binary_path>}
    """

    def __init__(
        self,
        snapshot_dir: str,
        project_name: Optional[str] = None,
        scorer: Optional[Scorer] = None,
        prefer_reset_threshold: Optional[int] = None
    ):
        """
        Args:
            snapshot_dir:            Directory for persisted wave / snapshot files
            project_name:            Project identifier (e.g. "nutshell"); used to
                                     auto-create the matching scorer for known CPUs.
            scorer:                  Scorer instance for evaluating snapshots.
                                     Use this for generic Verilog modules with a
                                     custom scorer.  Mutually exclusive with
                                     project_name — if both are given, scorer wins.
            prefer_reset_threshold:  Return None (use reset) when best score ≤ this
                                     value.  Defaults to scorer.reset_score.
        """
        if scorer is not None:
            self.scorer = scorer
        elif project_name is not None:
            self.scorer = create_scorer(project_name)
        else:
            raise ValueError(
                "Either 'project_name' or 'scorer' must be provided"
            )
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.prefer_reset_threshold = (
            prefer_reset_threshold
            if prefer_reset_threshold is not None
            else self.scorer.reset_score
        )
        self.logger = BMCFuzzLogger.get_logger("SnapshotManager")

        self._next_id: int                   = 1
        self._seen:    Set[str]              = set()    # identifiers of accepted snaps
        self._scores:  List[Tuple[int, int]] = []       # [(score, id)]
        self._id2data: Dict[int, Any]        = {}       # id → parsed input_data
        self._id2snap: Dict[int, str]        = {}       # id → saved snapshot path
        self._id2wave: Dict[int, str]        = {}       # id → saved wave path

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    def add_snapshots(self, snapshots: List[Dict[str, str]]) -> int:
        """
        Ingest snapshots produced by rtl_init.get_snapshots().

        Each entry is processed as follows:
        - flag is parsed by the scorer; entries that fail to parse are dropped
        - zero-score entries are dropped
        - duplicates (same scorer.get_identifier output) are dropped
        - accepted entries are copied to snapshot_dir/{id} and {id}.vcd

        Returns: number of snapshots actually added
        """
        added = sum(1 for snap in snapshots if self._add_one(snap))
        self.logger.info(f"Added {added}/{len(snapshots)} snapshots")
        return added

    def select_best(self) -> Optional[Dict[str, Any]]:
        """
        Select the highest-scoring snapshot from the current pool.

        - Decays scorer weights for the selected entry (encourages diversity)
        - Recalculates scores for all remaining pool entries
        - Returns None when the pool is empty or best score ≤ reset threshold

        Returns:
            {"id": int, "score": int, "snapshot_path": str, "wave_path": str}
            or None  (caller should fall back to reset snapshot)
        """
        if not self._scores:
            self.logger.warning("No snapshots available")
            return None

        best_score, best_id = max(self._scores)

        if best_score <= self.prefer_reset_threshold:
            self.logger.info(
                f"Best score {best_score} ≤ threshold "
                f"{self.prefer_reset_threshold} — prefer reset"
            )
            return None

        # Decay weights so subsequent selections favour unexplored states
        input_data = self._id2data[best_id]
        if input_data is not None:
            self.scorer.update_weights(input_data)

        # Remove selected entry and recalculate remaining scores
        self._scores = [
            (self._rescore(sid, old_score), sid)
            for old_score, sid in self._scores
            if sid != best_id
        ]

        self.logger.info(f"Selected snapshot {best_id}, score: {best_score}")
        return {
            "id":            best_id,
            "score":         best_score,
            "details":       self._id2data[best_id],
            "snapshot_path": self._id2snap[best_id],
            "wave_path":     self._id2wave[best_id],
        }

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _add_one(self, snap: Dict[str, str]) -> bool:
        """Process and store a single snapshot entry. Returns True if added."""
        flag     = snap.get("flag", "")
        wave     = snap.get("wave", "")
        snapshot = snap.get("snapshot", "")

        # self.logger.debug(f"Processing snapshot entry: flag={flag}, wave={wave}, snapshot={snapshot}")

        if not Path(flag).exists():
            self.logger.debug(f"Flag file not found: {flag}")
            return False

        input_data = self.scorer.parse_input(flag)
        if input_data is None:
            return False

        score      = self.scorer.calculate_score(input_data)
        identifier = self.scorer.get_identifier(input_data)

        if score == 0:
            self.logger.debug(f"Zero-score snapshot skipped: {identifier}")
            return False

        if identifier in self._seen:
            self.logger.debug(f"Duplicate snapshot skipped: {identifier}")
            return False

        # Accept this snapshot
        snap_id = self._next_id
        self._next_id += 1
        self._seen.add(identifier)

        saved_snap = self.snapshot_dir / str(snap_id)
        saved_wave = self.snapshot_dir / f"{snap_id}.vcd"
        shutil.copyfile(snapshot, saved_snap)
        shutil.copyfile(wave, saved_wave)

        self._id2data[snap_id] = input_data
        self._id2snap[snap_id] = str(saved_snap)
        self._id2wave[snap_id] = str(saved_wave)
        self._scores.append((score, snap_id))

        self.logger.debug(f"Added snapshot {snap_id}, score={score}, identifier={identifier}")
        return True

    def _rescore(self, snap_id: int, old_score: int) -> int:
        """Re-evaluate a snapshot after scorer weights have changed."""
        input_data = self._id2data[snap_id]
        return (
            self.scorer.calculate_score(input_data)
            if input_data is not None
            else old_score
        )


__all__ = ['SnapshotManager']

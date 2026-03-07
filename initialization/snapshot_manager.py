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

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from utils.logger import BMCFuzzLogger
from core.config import Config
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
        shutil.rmtree(self.snapshot_dir, ignore_errors=True)
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
        - if pool size exceeds Config.SNAPSHOT_POOL_CAPACITY, lowest-scoring
          snapshots are removed until at capacity.

        Returns: number of snapshots actually added
        """
        added = sum(1 for snap in snapshots if self._add_one(snap))
        self.logger.info(f"Added {added}/{len(snapshots)} snapshots")
        self._trim_to_capacity()
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
            "details":       self.scorer.get_identifier(self._id2data[best_id]),
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
        saved_wave = self.snapshot_dir / f"{snap_id}.fst"
        if os.path.exists(snapshot):
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

    def _trim_to_capacity(self) -> None:
        """If pool exceeds Config.SNAPSHOT_POOL_CAPACITY, remove lowest-scoring snapshots."""
        cap = Config.SNAPSHOT_POOL_CAPACITY
        if len(self._scores) <= cap:
            return
        # Sort by score ascending; remove (current - cap) lowest
        sorted_scores = sorted(self._scores, key=lambda x: (x[0], x[1]))
        to_remove = len(sorted_scores) - cap
        remove_ids = {sid for _, sid in sorted_scores[:to_remove]}
        self.logger.info(
            f"Pool size {len(self._scores)} > capacity {cap}, removing {to_remove} lowest-scoring snapshots"
        )
        for sid in remove_ids:
            self._remove_snapshot(sid)
        self._scores = [(s, i) for s, i in self._scores if i not in remove_ids]

    def _remove_snapshot(self, snap_id: int) -> None:
        """Remove one snapshot from pool and delete its files; update _seen."""
        if snap_id in self._id2data:
            identifier = self.scorer.get_identifier(self._id2data[snap_id])
            self._seen.discard(identifier)
        for key in (self._id2snap, self._id2wave):
            if snap_id in key:
                p = Path(key[snap_id])
                if p.exists():
                    try:
                        p.unlink()
                    except OSError as e:
                        self.logger.warning(f"Could not delete {p}: {e}")
                del key[snap_id]
        if snap_id in self._id2data:
            del self._id2data[snap_id]


__all__ = ['SnapshotManager']

"""
Module-level scorer implementation

Scores snapshots based on **minimum Hamming distance** between their
coverage vector and all previously selected snapshots' vectors.

Distance metric — Hamming distance
===================================
Why Hamming distance is the right choice here:

1. **Binary data native**: Cover-point status is inherently binary
   (covered / not-covered).  Hamming distance is the canonical metric
   for fixed-length binary vectors — it simply counts the number of
   positions that differ.

2. **Diversity maximisation**: By selecting the candidate whose
   *minimum* Hamming distance to every already-selected vector is
   largest, we greedily build a maximally diverse subset.  This pushes
   the formal engine to start from snapshots that exercise distinct
   combinations of cover points, avoiding redundant exploration.

3. **Cold-start semantics**: When no snapshot has been selected yet,
   the reference is the all-zero vector, so the initial score equals
   ``popcount(vec)`` — snapshots that hit more cover points are
   preferred first, which is a sensible bootstrapping strategy.

4. **Efficiency**: O(n) per pair comparison (XOR + popcount), trivially
   parallelisable across the selected set.

Alternative metrics considered and rejected:
  - Jaccard: undefined when both vectors are all-zero; returns a float
    that needs arbitrary scaling.
  - Cosine: poor discriminator for sparse binary vectors (many
    snapshots have very few 1-bits).
  - Asymmetric "new-coverage-only": ignores positions where the
    candidate *loses* coverage, giving a biased view of diversity.
"""

import csv
import os
from typing import Any, Dict, List, Optional, Tuple

from initialization.scorer import Scorer


class ModuleScorer(Scorer):
    """
    Distance-based scorer for module-level projects.

    Each snapshot carries a ``control_cover_points-*.csv`` whose
    ``Covered`` column is read as a binary coverage vector.

    Score = min Hamming distance to every previously *selected* vector.
    Before any selection the reference is the all-zero vector.
    """

    def __init__(self, name: str = "module", reset_score: int = 0):
        self._selected_vectors: List[tuple] = []
        super().__init__(name=name, reset_score=reset_score)

    # -----------------------------------------------------------------
    # Criteria table (required by base class, kept minimal)
    # -----------------------------------------------------------------

    def _init_criteria_table(self):
        self.criteria_table = {"C_coverage": {}}

    def _store_initial_weights(self):
        self.initial_weights = {"C_coverage": 1}

    # -----------------------------------------------------------------
    # Core interface
    # -----------------------------------------------------------------

    def parse_input(self, flag: str) -> Optional[tuple]:
        """
        Parse a control_cover_points CSV into a binary coverage vector.

        Args:
            flag: Path to a CSV with columns ``Index,Covered``

        Returns:
            Tuple of ints (0 or 1) per cover point, or None on error
        """
        if not os.path.isfile(flag):
            self.logger.error(f"Flag file does not exist: {flag}")
            return None

        try:
            bits: List[int] = []
            with open(flag, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    bits.append(
                        1 if row.get("Covered", "0").strip() == "1" else 0
                    )
            if not bits:
                self.logger.error(f"Empty coverage file: {flag}")
                return None
            return tuple(bits)
        except Exception as e:
            self.logger.error(f"Failed to parse flag file {flag}: {e}")
            return None

    def evaluate_criteria(
        self, input_data: tuple
    ) -> List[Tuple[str, str, int]]:
        """Required by base class; returns coverage count as criterion."""
        return [("C_coverage", str(sum(input_data)), 1)]

    # -----------------------------------------------------------------
    # Distance-based scoring
    # -----------------------------------------------------------------

    @staticmethod
    def _hamming_distance(a: tuple, b: tuple) -> int:
        """Hamming distance between two binary vectors (padded to equal length)."""
        la, lb = len(a), len(b)
        if la < lb:
            a = a + (0,) * (lb - la)
        elif lb < la:
            b = b + (0,) * (la - lb)
        return sum(x != y for x, y in zip(a, b))

    def calculate_score(self, input_data: tuple) -> int:
        """
        Score = min Hamming distance to every selected vector.

        When no vector has been selected yet the reference is all-zeros,
        so the score equals ``sum(input_data)`` (number of covered points).
        """
        if not self._selected_vectors:
            return sum(input_data)

        return min(
            self._hamming_distance(input_data, sel)
            for sel in self._selected_vectors
        )

    def update_weights(self, input_data: tuple):
        """Record the selected vector so future scores reflect it."""
        self._selected_vectors.append(input_data)

    def get_identifier(self, input_data: tuple) -> str:
        """Compact hex digest of the binary coverage vector."""
        n = 0
        for bit in input_data:
            n = (n << 1) | bit
        return hex(n)

    def reset_criteria(self):
        """Reset criteria table and clear selected vectors."""
        super().reset_criteria()
        self._selected_vectors.clear()

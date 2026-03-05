"""
Module-level scorer implementation

Scores snapshots purely by simulation cycle count —
higher cycle means the module ran longer before stopping,
which is more interesting for formal verification seeding.
"""

from typing import Any, Dict, List, Optional, Tuple

from initialization.scorer import Scorer


class ModuleScorer(Scorer):
    """
    Cycle-based scorer for module-level projects.

    The flag from module fuzzer snapshots is the cycle number
    (extracted from snapshot-{cycle}.vcd filenames).
    Score = cycle count directly; no criteria weight decay.
    """

    def __init__(self, name: str = "module", reset_score: int = 32):
        super().__init__(name=name, reset_score=reset_score)

    # -----------------------------------------------------------------
    # Criteria table (required by base class, kept minimal)
    # -----------------------------------------------------------------

    def _init_criteria_table(self):
        self.criteria_table = {
            "C_cycle": {},
        }

    def _store_initial_weights(self):
        self.initial_weights = {
            "C_cycle": 1,
        }

    # -----------------------------------------------------------------
    # Core interface
    # -----------------------------------------------------------------

    def parse_input(self, input_file: str) -> Optional[int]:
        """
        Parse the flag value (cycle number string) into an integer.

        Args:
            input_file: Cycle number as a string (e.g. "3519")

        Returns:
            Cycle count as int, or None if invalid
        """
        try:
            cycle = int(input_file)
            if cycle < 0:
                return None
            return cycle
        except (ValueError, TypeError):
            self.logger.error(f"Invalid cycle flag: {input_file}")
            return None

    def evaluate_criteria(self, input_data: int) -> List[Tuple[str, str, int]]:
        """Return a single criterion keyed by the cycle value."""
        return [("C_cycle", str(input_data), 1)]

    def calculate_score(self, input_data: int) -> int:
        """Score equals the cycle count — higher cycle, higher score."""
        return input_data

    def update_weights(self, input_data: int):
        """No-op: cycle-based scoring has no decay."""
        pass

    def get_identifier(self, input_data: int) -> str:
        return str(input_data)

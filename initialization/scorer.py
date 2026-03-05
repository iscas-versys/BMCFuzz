"""
Generic scoring mechanism for snapshot evaluation

This module provides an abstract base class for scorers that
maintain evaluation criteria and dynamically adjust weights.

Scorers maintain a criteria table and provide scoring for
inputs (can be state or transition, interface is unified).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type

from utils.logger import BMCFuzzLogger
from core.config import Config


class Scorer(ABC):
    """
    Abstract base class for snapshot scorers
    
    Scorers maintain a criteria table with initial weights and:
    - Parse input to determine which criteria are satisfied
    - Calculate scores based on current weights for satisfied criteria
    - Update weights after selection
    
    A criteria table entry has:
    - criteria_type: Identifier for the criterion
    - evaluation_key: Key that identifies the specific evaluation
    - initial_weight: Default weight for this criterion
    
    The input can be a state or a transition - the interface
    is unified and doesn't distinguish between them.
    """
    
    def __init__(self, name: str, reset_score: int = 32):
        """
        Initialize scorer
        
        Args:
            name: Scorer identifier (e.g., 'csr', 'gpr')
            reset_score: Default score for reset snapshot
        """
        self.name = name
        self.reset_score = reset_score
        self.logger = BMCFuzzLogger.get_logger(f"{self.__class__.__name__}")
        
        # Initialize criteria table
        # Format: Dict[criteria_type, Dict[evaluation_key, current_weight]]
        self.criteria_table: Dict[str, Dict[str, int]] = {}
        self._init_criteria_table()
        
        # Store initial weights for reference
        self.initial_weights: Dict[str, int] = {}
        self._store_initial_weights()
        
        self.logger.info(
            f"Scorer '{name}' initialized with {len(self.criteria_table)} criteria"
        )
    
    @abstractmethod
    def _init_criteria_table(self):
        """
        Initialize criteria table for this scorer
        
        Should populate self.criteria_table with criteria types.
        Each criteria_type maps to an empty dict that will store
        (evaluation_key -> current_weight) mappings.
        
        Example for CSR:
            self.criteria_table = {
                'C_1': {},  # Privilege mode
                'C_2': {},  # Virtual memory
                'C_3': {},  # TSR, TW, TVM
                ...
            }
        """
        pass
    
    def _store_initial_weights(self):
        """
        Store initial weights from criteria table
        
        Each criteria type should have a predefined initial weight.
        Subclasses should override this to define their initial weights.
        """
        # Default: no initial weights defined
        pass
    
    @abstractmethod
    def parse_input(self, input_file: str) -> Optional[Any]:
        """
        Parse input data from file
        
        Args:
            input_file: Path to input data file
        
        Returns:
            Parsed input (state, transition, or any format)
            or None if parsing fails
        """
        pass
    
    @abstractmethod
    def evaluate_criteria(self, input_data: Any) -> List[tuple]:
        """
        Evaluate which criteria are satisfied by the input
        
        Args:
            input_data: Parsed input (state, transition, or any format)
        
        Returns:
            List of (criteria_type, evaluation_key, initial_weight) tuples
        """
        pass
    
    def calculate_score(self, input_data: Any) -> int:
        """
        Calculate score for input
        
        Args:
            input_data: Input data (state, transition, or any format)
        
        Returns:
            Score (higher is more interesting)
        """
        score = 0
        
        # Evaluate which criteria are satisfied
        criteria_list = self.evaluate_criteria(input_data)
        
        # Calculate score based on satisfied criteria
        for criteria_type, evaluation_key, initial_weight in criteria_list:
            criteria_dict = self.criteria_table[criteria_type]
            
            # Get or initialize current weight
            if evaluation_key not in criteria_dict:
                criteria_dict[evaluation_key] = initial_weight
                current_weight = initial_weight
            else:
                current_weight = criteria_dict[evaluation_key]
            
            # Skip if weight is zero
            if current_weight == 0:
                continue
            
            # Add to score (2^weight)
            score += 2 ** current_weight
        
        return score
    
    def update_weights(self, input_data: Any):
        """
        Update weights after selecting an input
        
        This implements decay mechanism - selecting reduces weights
        to encourage diversity.
        
        Args:
            input_data: Input data (state, transition, or any format)
        """
        # Evaluate which criteria are satisfied
        criteria_list = self.evaluate_criteria(input_data)
        
        # Decay weights for satisfied criteria
        for criteria_type, evaluation_key, _ in criteria_list:
            criteria_dict = self.criteria_table[criteria_type]
            
            # Decay weight if exists
            if evaluation_key in criteria_dict:
                criteria_dict[evaluation_key] = max(
                    0, criteria_dict[evaluation_key] - 1
                )
    
    def get_identifier(self, input_data: Any) -> str:
        """
        Get unique identifier for input
        
        Args:
            input_data: Input data
        
        Returns:
            String identifier
        """
        return str(input_data)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scorer statistics
        
        Returns:
            Dictionary with statistics about criteria and weights
        """
        criteria_stats = {}
        for criteria_type, keys in self.criteria_table.items():
            # Count keys by weight
            weight_counts = {}
            for weight in keys.values():
                weight_counts[weight] = weight_counts.get(weight, 0) + 1
            
            criteria_stats[criteria_type] = {
                'total_keys': len(keys),
                'weight_distribution': weight_counts,
                'initial_weight': self.initial_weights.get(criteria_type, None)
            }
        
        return {
            'scorer_name': self.name,
            'reset_score': self.reset_score,
            'criteria': criteria_stats,
            'total_criteria': len(self.criteria_table)
        }
    
    def get_criteria_table(self) -> Dict[str, Dict[str, int]]:
        """
        Get current criteria table
        
        Returns:
            Dictionary mapping criteria types to evaluation key weights
        """
        return self.criteria_table
    
    def reset_criteria(self):
        """Reset all criteria weights to initial state"""
        self.criteria_table.clear()
        self._init_criteria_table()
        self.logger.info(f"Scorer '{self.name}' criteria table reset")


# =============================================================================
# Project → Scorer mapping (uses Config.CPU_PROJECTS / Config.MODULE_PROJECTS)
# =============================================================================


def get_scorer_class(project_name: str) -> Type["Scorer"]:
    """
    Get the scorer class for a given project.

    Args:
        project_name: Project identifier

    Returns:
        Scorer subclass

    Raises:
        ValueError: If no scorer is registered for the project
    """
    if project_name in Config.CPU_PROJECTS:
        from initialization.csr_scorer import CSRScorer
        return CSRScorer
    if project_name in Config.MODULE_PROJECTS:
        from initialization.module_scorer import ModuleScorer
        return ModuleScorer
    raise ValueError(f"No scorer available for project: {project_name}")


def create_scorer(project_name: str, **kwargs) -> "Scorer":
    """
    Create a scorer instance for a given project.

    Args:
        project_name: Project identifier
        **kwargs: Forwarded to the scorer constructor

    Returns:
        Scorer instance
    """
    scorer_class = get_scorer_class(project_name)
    return scorer_class(**kwargs)


def is_project_supported(project_name: str) -> bool:
    """Check whether a project has a registered scorer."""
    return project_name in Config.CPU_PROJECTS or project_name in Config.MODULE_PROJECTS

__all__ = [
    'Scorer',
    'get_scorer_class',
    'create_scorer',
    'is_project_supported',
]
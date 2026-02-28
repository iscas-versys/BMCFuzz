"""
CSR (Control and Status Register) specific scorer implementation

This module provides CSR-specific scoring logic by extending
the generic Scorer base class.

Only processes CSR transitions (past, now) format.
"""

from typing import Dict, List, Tuple, Any, Optional
import csv

from initialization.scorer import Scorer
from utils.logger import BMCFuzzLogger


# MSTATUS field definitions for parsing
MSTATUS_FIELDS = {
    "SD": (63, 63),
    "WPRI1": (62, 38),
    "MBE": (37, 37),
    "SBE": (36, 36),
    "SXL": (35, 34),
    "UXL": (33, 32),
    "WPRI2": (31, 23),
    "TSR": (22, 22),
    "TW": (21, 21),
    "TVM": (20, 20),
    "MXR": (19, 19),
    "SUM": (18, 18),
    "MPRV": (17, 17),
    "XS": (16, 15),
    "FS": (14, 13),
    "MPP": (12, 11),
    "VS": (10, 9),
    "SPP": (8, 8),
    "MPIE": (7, 7),
    "UBE": (6, 6),
    "SPIE": (5, 5),
    "WPRI3": (4, 4),
    "MIE": (3, 3),
    "WPRI4": (2, 2),
    "SIE": (1, 1),
    "WPRI5": (0, 0),
}


def parse_mstatus(mstatus_hex: str) -> Dict[str, str]:
    """
    Parse mstatus register value into individual fields
    
    Args:
        mstatus_hex: Hexadecimal string representation of mstatus
    
    Returns:
        Dictionary mapping field names to binary string values
    """
    mstatus_bin = bin(int(mstatus_hex, 16))[2:].zfill(64)
    parsed_fields = {}
    for name, (start, end) in MSTATUS_FIELDS.items():
        value = mstatus_bin[63 - start:64 - end]
        parsed_fields[name] = value
    return parsed_fields


def get_satp_hi(satp: str) -> str:
    """
    Extract high 4 bits from satp register
    
    Args:
        satp: Hexadecimal string representation of satp
    
    Returns:
        Binary string of high 4 bits (mode bits)
    """
    satp_bin = bin(int(satp, 16))[2:].zfill(64)
    return satp_bin[:4]


def vm_is_enabled(privilege_mode: str, mstatus_hex: str, satp_hex: str) -> bool:
    """
    Check if virtual memory is enabled
    
    Args:
        privilege_mode: Current privilege mode ('00'='U', '01'='S', '11'='M')
        mstatus_hex: mstatus register value
        satp_hex: satp register value
    
    Returns:
        True if virtual memory is enabled
    """
    parsed_mstatus = parse_mstatus(mstatus_hex)
    mprv = parsed_mstatus['MPRV'] == '1'
    mpp = parsed_mstatus['MPP']
    satp_mode = int(get_satp_hi(satp_hex), 2)
    
    if satp_mode == 8 and (
        (privilege_mode in ['00', '01']) or 
        (mprv and mpp in ['00', '01'])
    ):
        return True
    return False


class CSRScorer(Scorer):
    """
    CSR-specific scorer implementation
    
    Processes CSR transitions (past, now) and evaluates
    which criteria changed.
    
    Criteria table:
    - C1: Privilege mode (weight=3)
    - C2: Virtual memory configuration (weight=5)
    - C3: Translation settings (TSR, TW, TVM) (weight=4)
    - C4: MPP, SPP, MPIE, SPIE, MIE, SIE (weight=3)
    - C5: M mode delegation (weight=2)
    """
    
    def __init__(self, name: str = 'csr', reset_score: int = 32):
        """
        Initialize CSR scorer
        
        Args:
            name: Scorer name (default: 'csr')
            reset_score: Default score for reset snapshot
        """
        super().__init__(name=name, reset_score=reset_score)
    
    def _init_criteria_table(self):
        """Initialize CSR criteria table"""
        self.criteria_table = {
            'C_1': {},  # Privilege mode: weight=3
            'C_2': {},  # Virtual memory: weight=5
            'C_3': {},  # TSR, TW, TVM: weight=4
            'C_4': {},  # MPP, SPP, MPIE, SPIE, MIE, SIE: weight=3
            'C_5': {},  # M mode delegation: weight=2
        }
    
    def _store_initial_weights(self):
        """Store initial weights for each criterion"""
        self.initial_weights = {
            'C_1': 3,
            'C_2': 5,
            'C_3': 4,
            'C_4': 3,
            'C_5': 2,
        }
    
    def parse_input(self, input_file: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Parse CSR transition from file
        
        Args:
            input_file: Path to transition CSV file
        
        Returns:
            Tuple of (past_state, now_state), or None if parsing fails
        """

        # self.logger.debug(f"Parsing CSR transition file: {input_file}")
        try:
            with open(input_file, mode="r", newline="", encoding="utf-8") as f:
                csv_reader = list(csv.DictReader(f))
            
            if len(csv_reader) < 2:
                self.logger.error(f"Insufficient data in {input_file}")
                return None
            
            # Ensure required fields exist
            required_fields = ['privilegeMode', 'mstatus', 'satp', 'medeleg']
            for row in csv_reader:
                for field in required_fields:
                    if field not in row:
                        self.logger.error(f"Missing field: {field}")
                        return None
            
            # Return transition (past, now)
            return (csv_reader[0], csv_reader[1])
            
        except Exception as e:
            self.logger.error(f"Error parsing transition file {input_file}: {e}")
            return None
    
    def evaluate_criteria(
        self,
        input_data: Tuple[Dict[str, Any], Dict[str, Any]]
    ) -> List[Tuple[str, str, int]]:
        """
        Evaluate which criteria changed in the transition
        
        Only includes criteria that actually changed.
        
        Args:
            input_data: Tuple of (past_state, now_state)
        
        Returns:
            List of (criteria_type, evaluation_key, initial_weight) tuples
        """
        past, now = input_data
        evaluations = []
        
        # Get evaluations for both states
        past_evals = {t: k for t, k, _ in self._get_state_evaluations(past)}
        now_evals = {t: k for t, k, _ in self._get_state_evaluations(now)}
        
        # Compare and include only changed criteria
        for criteria_type, initial_weight in self.initial_weights.items():
            past_key = past_evals.get(criteria_type)
            now_key = now_evals.get(criteria_type)
            
            # Skip if no change
            if past_key == now_key:
                continue
            
            # Add changed criterion (use now state's evaluation)
            evaluations.append((criteria_type, self.get_identifier(past_key+now_key), initial_weight))
        
        return evaluations
    
    def _get_state_evaluations(self, state: Dict[str, Any]) -> List[Tuple[str, str, int]]:
        """
        Get all criteria evaluations for a state
        
        Args:
            state: CSR state dictionary
        
        Returns:
            List of (criteria_type, evaluation_key, initial_weight) tuples
        """
        evaluations = []
        
        # Parse CSR fields
        privilege_mode = state['privilegeMode']
        mstatus = state['mstatus']
        satp = state['satp']
        medeleg = state['medeleg']
        
        parsed_mstatus = parse_mstatus(mstatus)
        satp_hi = get_satp_hi(satp)
        
        # C1: Privilege mode (weight=3)
        c1_key = f"privilege_mode:{privilege_mode}"
        evaluations.append(('C_1', c1_key, 3))
        
        # C2: Virtual memory configuration (weight=5)
        # Only count if VM is actually enabled
        if vm_is_enabled(privilege_mode, mstatus, satp):
            mxr_sum = ''.join([
                parsed_mstatus['MXR'],
                parsed_mstatus['SUM']
            ])
            c2_key = f"vm:{mxr_sum}:{satp_hi}:{privilege_mode}"
            evaluations.append(('C_2', c2_key, 5))
        
        # C3: Translation settings (TSR, TW, TVM) (weight=4)
        c3_key = ''.join([
            parsed_mstatus['TSR'],
            parsed_mstatus['TW'],
            parsed_mstatus['TVM']
        ])
        evaluations.append(('C_3', c3_key, 4))
        
        # C4: MPP, SPP, MPIE, SPIE, MIE, SIE (weight=3)
        c4_key = ''.join([
            parsed_mstatus['MPP'],
            parsed_mstatus['SPP'],
            parsed_mstatus['MPIE'],
            parsed_mstatus['SPIE'],
            parsed_mstatus['MIE'],
            parsed_mstatus['SIE']
        ])
        evaluations.append(('C_4', c4_key, 3))
        
        # C5: M mode delegation (weight=2)
        c5_key = f"medeleg:{medeleg}"
        evaluations.append(('C_5', c5_key, 2))
        
        return evaluations
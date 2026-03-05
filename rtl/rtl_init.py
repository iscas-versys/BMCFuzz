"""
RTL Initialization Module for BMCFuzz

This module provides a unified generic interface for RTL code generation,
emulator management, and fuzzer operations. 

RTLInit must be initialized with a project configuration dictionary, which 
defines project-specific implementations for RTL generation, emulation, 
and fuzzing. Configuration is done entirely in Python code.

Only RTLInit class and base classes are exposed to external users.
"""

import os
import sys
from typing import Dict, List, Any, Tuple
from pathlib import Path
from abc import ABC, abstractmethod

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import BMCFuzzLogger
from core.config import Config, BMCFUZZ_HOME


# =============================================================================
# Abstract Base Classes for Project-Specific Implementations
# =============================================================================

class RTLGeneratorBase(ABC):
    """Abstract base class for RTL code generation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = BMCFuzzLogger.get_logger("RTLGenerator")
    
    @abstractmethod
    def build(self, **kwargs) -> bool:
        """
        Build RTL code
        
        Args:
            **kwargs: Build arguments
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_rtl_info(self) -> Dict[str, Any]:
        """
        Get all RTL Info
        """
        pass
    
    @abstractmethod
    def prepare_formal(self, output_dir: str, **kwargs) -> str:
        """
        Prepare RTL for formal verification
        
        Args:
            output_dir: Output directory
            **kwargs: Additional arguments
        
        Returns:
            Output directory path
        """
        pass

    @abstractmethod
    def get_cover_points_name(self) -> List[Tuple[str, str]]:
        """
        Get cover points name

        Returns:
            List[Tuple[str, str]]: cover points name
        """
        pass


class EmulatorManagerBase(ABC):
    """Abstract base class for emulator management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = BMCFuzzLogger.get_logger("EmulatorManager")
    
    @abstractmethod
    def build(self, **kwargs) -> bool:
        """
        Build emulator
        
        Args:
            **kwargs: Build arguments
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def run(self, **kwargs) -> Tuple[int, str]:
        """
        Run emulator
        
        Args:
            **kwargs: Run arguments
        
        Returns:
            Tuple of (return_code, result_directory)
        """
        pass
    
    @abstractmethod
    def get_results(self) -> Dict[str, Any]:
        """
        Get emulator results
        
        Returns:
            Dictionary with emulator results
        """
        pass


class FuzzerManagerBase(ABC):
    """Abstract base class for fuzzer management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = BMCFuzzLogger.get_logger("FuzzerManager")
    
    @abstractmethod
    def build(self, **kwargs) -> bool:
        """
        Build fuzzer
        
        Args:
            **kwargs: Build arguments
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run fuzzer
        
        Args:
            **kwargs: Run arguments
        
        Returns:
            Dictionary with fuzzer results
        """
        pass
    
    @abstractmethod
    def get_fuzz_inputs(self) -> List[str]:
        """
        Get fuzz inputs
        
        Returns:
            List of fuzz inputs
        """
        pass
    
    @abstractmethod
    def get_results(self) -> Dict[str, Any]:
        """
        Get fuzzer results including coverage, snapshots, waves
        
        Returns:
            Dictionary with fuzzer results
        """
        pass

    @abstractmethod
    def get_coverage(self) -> Dict[str, Any]:
        """
        Get coverage information
        
        Returns:
            Dictionary with coverage information
        """
        pass
    
    @abstractmethod
    def get_snapshots(self) -> List[Dict]:
        """
        Get snapshot information
        
        Returns:
            List of snapshot dictionaries
        """
        pass


# =============================================================================
# Public Interface Class
# =============================================================================

class RTLInit:
    """
    Unified RTL Initialization Interface for BMCFuzz
    
    This is the only class exposed to external users. It provides a unified
    interface for RTL code generation, emulator management, and fuzzer operations.
    
    Must be initialized with a project configuration dictionary that defines 
    the project name, directory, and implementation classes.
    
    Usage:
        config = {
            "project_name": "nutshell",
            "project_dir": "/path/to/nutshell",
            "rtl_dir": "/path/to/rtl",
            "formal_rtl_dir": "/path/to/formal_rtl",
            "rtl_generator": CPURTLGenerator,
            "emu_manager": CPUEmulatorManager,
            "fuzzer_manager": CPUFuzzerManager
        }
        rtl = RTLInit(config=config)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize RTL interface with project configuration
        
        Args:
            config: Configuration dictionary containing:
                - project_name: Project name
                - project_dir: Project directory path
                - rtl_dir: RTL directory path
                - formal_rtl_dir: Formal RTL directory path
                - rtl_generator: RTLGeneratorBase subclass
                - emu_manager: EmulatorManagerBase subclass
                - fuzzer_manager: FuzzerManagerBase subclass
        
        Raises:
            ValueError: If required config fields are missing
        """
        self.logger = BMCFuzzLogger.get_logger("RTLInit")
        
        # Store configuration
        self.config = config
        
        # Validate required config fields
        self._validate_config()
        
        # Extract basic config
        self.project_name = self.config["project_name"]
        self.project_dir = self.config["project_dir"]
        self.bmcfuzz_home = BMCFUZZ_HOME
        
        # Initialize project-specific implementations
        self._rtl_generator = self._init_rtl_generator()
        self._emu_manager = self._init_emu_manager()
        self._fuzzer_manager = self._init_fuzzer_manager()
        
        self.logger.info(f"RTLInit initialized for project: {self.project_name}")
        self.logger.info(f"Project directory: {self.project_dir}")
    
    def _validate_config(self):
        """Validate required configuration fields"""
        required_fields = ["project_name", "project_dir"]
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required config field: {field}")
    
    def _init_rtl_generator(self) -> RTLGeneratorBase:
        """Initialize RTL generator from config"""
        if "rtl_generator" not in self.config:
            raise ValueError("Config must include 'rtl_generator' class")
        
        generator_class = self.config["rtl_generator"]
        return generator_class(self.config)
    
    def _init_emu_manager(self) -> EmulatorManagerBase:
        """Initialize emulator manager from config"""
        if "emu_manager" not in self.config:
            raise ValueError("Config must include 'emu_manager' class")
        
        manager_class = self.config["emu_manager"]
        return manager_class(self.config)
    
    def _init_fuzzer_manager(self) -> FuzzerManagerBase:
        """Initialize fuzzer manager from config"""
        if "fuzzer_manager" not in self.config:
            raise ValueError("Config must include 'fuzzer_manager' class")
        
        manager_class = self.config["fuzzer_manager"]
        return manager_class(self.config)
    
    # =========================================================================
    # RTL Interface
    # =========================================================================
    
    def build_rtl(self, **kwargs) -> bool:
        """
        Build RTL code
        
        Args:
            **kwargs: Build arguments (cover_type, make_args, etc.)
        
        Returns:
            True if successful
        """
        return self._rtl_generator.build(**kwargs)
    
    def get_rtl_info(self) -> Dict[str, Any]:
        """
        Get RTL information including all file paths
        
        Returns:
            Dictionary with RTL information:
            {
                "top_module": str,
                "rtl_file": str,
                "rtl_dir": str
            }
        """
        return self._rtl_generator.get_rtl_info()
    
    def prepare_formal_rtl(self, **kwargs) -> str:
        """
        Prepare RTL for formal verification
        
        Args:
            output_dir: Output directory path
            **kwargs: Additional arguments (e.g., snapshot_id for initialization)
        
        Returns:
            Output verilog file path
        """
        return self._rtl_generator.prepare_formal(**kwargs)
    
    def get_cover_points_name(self) -> List[Tuple[str, str]]:
        """
        Get cover points name
        
        Returns:
            List of tuples (module_name, point_name)
        """
        return self._rtl_generator.get_cover_points_name()
    
    # =========================================================================
    # Emulator Interface
    # =========================================================================
    
    def build_emu(self, pre_build:bool = False, **kwargs) -> bool:
        """
        Build emulator
        
        Args:
            **kwargs: Build arguments (trace, snapshot, cover_type, etc.)
        
        Returns:
            True if successful
        """
        if pre_build:
            self.build_rtl(**kwargs)  # Ensure RTL is built before emulator
        return self._emu_manager.build(**kwargs)
    
    def run_emu(self, **kwargs) -> Tuple[int, str]:
        """
        Run emulator
        
        Args:
            **kwargs: Run arguments (workload, max_instr, max_cycle, etc.)
        
        Returns:
            Tuple of (return_code, result_directory)
        """
        return self._emu_manager.run(**kwargs)
    
    def get_emu_results(self) -> Dict[str, Any]:
        """
        Get emulator results
        
        Returns:
            Dictionary with emulator results
        """
        return self._emu_manager.get_results()
    
    # =========================================================================
    # Fuzzer Interface
    # =========================================================================
    
    def build_fuzzer(self, pre_build:bool = False, **kwargs) -> bool:
        """
        Build fuzzer
        
        Args:
            **kwargs: Build arguments (cover_type, make_args, etc.)
        
        Returns:
            True if successful
        """
        if pre_build:
            self.build_rtl(**kwargs)  # Ensure RTL is built before fuzzer
        return self._fuzzer_manager.build(**kwargs)
    
    def run_fuzzer(self, **kwargs) -> Dict[str, Any]:
        """
        Run fuzzer
        
        Args:
            **kwargs: Run arguments (corpus_dir, max_runs, etc.)
        
        Returns:
            Dictionary with fuzzer results
        """
        return self._fuzzer_manager.run(**kwargs)
    
    def get_fuzz_inputs(self) -> List[str]:
        """
        Get fuzz inputs
        
        Returns:
            List of fuzz inputs
        """
        return self._fuzzer_manager.get_fuzz_inputs()
    
    def get_fuzzer_results(self) -> Dict[str, Any]:
        """
        Get fuzzer results including coverage, snapshots, waves
        
        Returns:
            Dictionary with fuzzer results
        """
        return self._fuzzer_manager.get_results()
    
    def get_coverage(self) -> Dict[str, Any]:
        """Get coverage information"""
        return self._fuzzer_manager.get_coverage()
    
    def get_snapshots(self) -> List[Dict]:
        """Get snapshot information"""
        return self._fuzzer_manager.get_snapshots()

    # =========================================================================
    # Utility Interface
    # =========================================================================
    
    def get_project_dir(self) -> str:
        """Get project directory"""
        return self.project_dir
    
    def get_project_name(self) -> str:
        """Get project name"""
        return self.project_name
    
    def get_config(self) -> Dict[str, Any]:
        """Get full configuration"""
        return self.config.copy()
    
    def cleanup(self) -> None:
        """Clean up temporary files"""
        import shutil
        
        self.logger.info("Cleaning up temporary files")
        
        # Clean fuzzer run directory
        fuzzer_run_dir = os.path.join(self.project_dir, "tmp", "fuzz_run")
        if os.path.exists(fuzzer_run_dir):
            shutil.rmtree(fuzzer_run_dir)
            os.makedirs(fuzzer_run_dir)
        
        # Clean project tmp directory
        tmp_dir = os.path.join(self.project_dir, "tmp")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
            os.makedirs(tmp_dir)


# =============================================================================
# Global Instance and Initialization
# =============================================================================

# Global RTLInit instance
rtl_manager = None

def initialize_rtl(project_name: str, cover_type: str = "toggle") -> RTLInit:
    """
    Initialize the global RTLInit instance with CPU defaults.
    
    Args:
        project_name: Project name (e.g., "nutshell")
        bmcfuzz_home: BMCFuzz home directory
        cover_type: Coverage type
        
    Returns:
        Initialized RTLInit instance
    """
    global rtl_manager
    # Local import to avoid circular dependency
    from rtl.cpu_init import create_cpu_rtl_init
    from rtl.module_init import create_module_rtl_init

    if project_name in Config.CPU_PROJECTS:
        rtl_manager = create_cpu_rtl_init(project_name, BMCFUZZ_HOME, cover_type)
    elif project_name in Config.MODULE_PROJECTS:
        rtl_manager = create_module_rtl_init(project_name, BMCFUZZ_HOME, cover_type)
    else:
        raise ValueError(f"No RTLInit available for project: {project_name}")
    return rtl_manager

def get_rtl_manager() -> RTLInit:
    """
    Get the global RTLInit instance.
    
    Returns:
        Global RTLInit instance or None if not initialized
    """
    if rtl_manager is None:
        raise ValueError("RTLInit not initialized")
    return rtl_manager


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    'RTLInit',
    'RTLGeneratorBase', 
    'EmulatorManagerBase', 
    'FuzzerManagerBase',
    'rtl_manager',
    'initialize_rtl',
    'get_rtl_manager'
]
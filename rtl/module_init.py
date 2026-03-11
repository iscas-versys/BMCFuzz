"""
Module-specific implementations for RTL initialization

This module provides concrete implementations for module-level projects
(e.g., rocket_dcache) to work with RTLInit.

Usage:
    from rtl.module_init import get_module_config, create_module_rtl_init
    
    # Method 1: Get config and create RTLInit
    config = get_module_config("rocket_dcache", bmcfuzz_home)
    rtl = RTLInit(config=config)
    
    # Method 2: Direct creation
    rtl = create_module_rtl_init("rocket_dcache", bmcfuzz_home)
"""

import os
import re
import shutil
import time
from typing import Dict, List, Any, Tuple, Optional

from rtl.rtl_init import (
    RTLGeneratorBase,
    EmulatorManagerBase,
    FuzzerManagerBase
)
from utils.logger import BMCFuzzLogger
from utils.command import run_command
from core.config import Config


# Module project name -> config (noop_home_suffix etc), names must be in Config.MODULE_PROJECTS
MODULE_PROJECT_CONFIGS = {
    "rocket_dcache": {
        "noop_home_suffix": os.path.join("rtl", "rocket-modules"),
    },
    "rocket_fpu": {
        "noop_home_suffix": os.path.join("rtl", "rocket-modules"),
    },
    "rocket_frontend": {
        "noop_home_suffix": os.path.join("rtl", "rocket-modules"),
    },
    "boom_dcache": {
        "noop_home_suffix": os.path.join("rtl", "boom-modules"),
    },
}


# =============================================================================
# Module RTL Generator
# =============================================================================

class ModuleRTLGenerator(RTLGeneratorBase):
    """
    RTL generator for module-level projects (e.g., rocket_dcache)
    
    Handles:
    - Building RTL via make src + module_parser.py
    - Preparing formal verification RTL
    - Managing RTL file paths (noop_home/modules/rtl)
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.project_name = config.get("project_name", "rocket_dcache")
        self.cover_type = config.get("cover_type", "toggle")
        self.noop_home = config.get("noop_home", "")
        self.bmcfuzz_home = config.get("bmcfuzz_home", "")
        self.formal_rtl_dir = config.get("formal_rtl_dir", "")

        os.makedirs(os.path.join(self.noop_home, "tmp"), exist_ok=True)
    
    def build(self, run_snapshot = False, make_args: str = "", **kwargs) -> bool:
        """
        Build RTL: make src FIRRTL_COVER=<cover_type> + module_parser.py
        
        Args:
            make_args: Additional make arguments
        
        Returns:
            True if successful
        """
        self.logger.info(f"Building RTL for module {self.project_name}, cover_type={self.cover_type}")

        log_file = os.path.join(self.noop_home, "tmp", "make_rtl.log")
        
        build_command = (
            f"cd {self.noop_home} && source env.sh && make clean && "
            f"make src XFUZZ=1 FIRRTL_COVER={self.cover_type},control -j16 {make_args} > {log_file} 2>&1 && "
            f"python3 modules/module_parser.py --project-name {self.project_name}"
        )

        if not run_snapshot:
            build_command += " --initial"
        
        build_command += f" >> {log_file} 2>&1"
        build_command = f"bash -c '{build_command}'"
        
        return_code = run_command(build_command, shell=True)
        
        if return_code == 0:
            self.logger.info("Module RTL build completed successfully")
            return True
        else:
            self.logger.error(f"Module RTL build failed with return code {return_code}")
            return False
    
    def get_rtl_info(self) -> Dict[str, Any]:
        """Get RTL info for module project"""
        rtl_dir = os.path.join(self.noop_home, "modules", "rtl")
        rtl_file = os.path.join(rtl_dir, "SimTop.sv")
        
        return {
            "top_module": "SimTop",
            "rtl_file": rtl_file,
            "rtl_dir": rtl_dir
        }
    
    def prepare_formal(self, **kwargs) -> str:
        """
        Prepare RTL for formal verification
        
        Copies RTL files from noop_home/modules/rtl and FormalTop.sv
        from noop_home/modules/ to the formal RTL directory.
        
        Returns:
            Formal RTL file path (SimTop.sv)
        """
        os.makedirs(self.formal_rtl_dir, exist_ok=True)
        
        self.logger.info(f"Preparing formal RTL in {self.formal_rtl_dir}")

        rtl_dir = os.path.join(self.noop_home, "modules", "rtl")
        
        # Copy SimTop.sv with enToggle modification
        # src_rtl = os.path.join(rtl_dir, "SimTop.sv")
        # dst_rtl = os.path.join(self.formal_rtl_dir, "SimTop.sv")
        
        # if os.path.exists(src_rtl):
        #     with open(src_rtl, 'r') as f:
        #         lines = f.readlines()
            
        #     lines = self._modify_enToggle_value(lines)
            
        #     with open(dst_rtl, 'w') as f:
        #         f.writelines(lines)
        
        # Copy other RTL files (.v, .sv) from modules/rtl/
        self._copy_other_rtl_files(rtl_dir)
        
        # Copy FormalTop.sv from modules/
        formal_top_src = os.path.join(self.noop_home, "modules", "FormalTop.sv")
        formal_top_dst = os.path.join(self.formal_rtl_dir, "FormalTop.sv")
        if os.path.exists(formal_top_src):
            shutil.copy(formal_top_src, formal_top_dst)
        
        return formal_top_dst
    
    def get_cover_points_name(self) -> List[Tuple[str, str]]:
        """Parse firrtl-cover.cpp in modules/rtl/ to get cover point names"""
        cover_points_name = []
        cover_name_file = os.path.join(self.noop_home, "modules", "rtl", "firrtl-cover.cpp")

        if not os.path.exists(cover_name_file):
            self.logger.warning(f"Cover name file not found: {cover_name_file}")
            return cover_points_name

        with open(cover_name_file, 'r') as file:
            lines = file.readlines()
            cover_name_begin = re.compile(r"static const char \*\w+_NAMES\[\] = {")
            cover_name_end = re.compile(r'};')
            cover_name_pattern = re.compile(r'\"(.*)\"')
            cover_name_flag = False
            for line in lines:
                cover_name_match = cover_name_begin.search(line)
                if cover_name_match:
                    cover_name_flag = True
                    continue
                if cover_name_flag:
                    if cover_name_end.search(line):
                        break
                    cover_name_match = cover_name_pattern.search(line)
                    if cover_name_match:
                        module_name = cover_name_match.group(1).split(".")[0]
                        signal_name = cover_name_match.group(1).split(".")[1:]
                        signal_name = ".".join(signal_name)
                        cover_points_name.append((module_name, signal_name))
        return cover_points_name
    
    def _modify_enToggle_value(self, src_lines: List[str]) -> List[str]:
        """Change enToggle and enToggle_past values"""
        for i, line in enumerate(src_lines):
            elements = line.split()
            if len(elements) > 1 and elements[0] == "reg":
                if elements[1] == "enToggle" or elements[1] == "enToggle_past":
                    src_lines[i] = src_lines[i].replace("1'h0", "1'h1")
        return src_lines
    
    def _copy_other_rtl_files(self, rtl_dir: str):
        """Copy other RTL files (.v, .sv) from modules/rtl/ excluding SimTop.sv"""
        for item in os.listdir(rtl_dir):
            if item.endswith(('.v', '.sv')) and item != "SimTop.sv":
                src = os.path.join(rtl_dir, item)
                dst = os.path.join(self.formal_rtl_dir, item)
                if os.path.isfile(src):
                    shutil.copy(src, dst)


# =============================================================================
# Module Emulator Manager
# =============================================================================

class ModuleEmulatorManager(EmulatorManagerBase):
    """
    Emulator manager for module-level projects
    
    Build: make modules EMU_TRACE=1
    Run:   emu -i <workload> -m <max_cycle> [-v <wave.vcd>]
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.project_name = config.get("project_name", "rocket_dcache")
        self.cover_type = config.get("cover_type", "toggle")
        self.noop_home = config.get("noop_home", "")
        self.bmcfuzz_home = config.get("bmcfuzz_home", "")
        
        self._results: Dict[str, Any] = {}
        self.emu_path = os.path.join(self.noop_home, "build", "emu")
    
    def build(self, trace: bool = True, make_args: str = "", **kwargs) -> bool:
        """
        Build module emulator: make modules EMU_TRACE=1
        
        Args:
            trace: Enable waveform tracing
            make_args: Additional make arguments
        
        Returns:
            True if successful
        """
        self.logger.info(f"Building module emulator for {self.project_name}")
        
        make_flags = []
        if trace:
            make_flags.append("EMU_TRACE=1")
        
        make_command = (
            f"cd {self.noop_home} && source env.sh && "
            f"make modules {' '.join(make_flags)} {make_args} -j16"
        )
        
        log_file = os.path.join(self.noop_home, "tmp", "make_emu.log")
        make_command += f" > {log_file} 2>&1"
        make_command = f"bash -c '{make_command}'"
        
        return_code = run_command(make_command, shell=True)
        
        if return_code == 0:
            self.logger.info("Module emulator build completed successfully")
            return True
        else:
            self.logger.error(f"Module emulator build failed with return code {return_code}")
            return False
    
    def run(self, workload: str, max_instr: int = 10000, max_cycle: int = 10000,
            dump_wave: bool = True, no_diff: bool = False, **kwargs) -> Tuple[int, str]:
        """
        Run module emulator with workload
        
        Args:
            workload: Workload file path
            max_cycle: Maximum simulation cycles
            dump_wave: Dump VCD waveform
        
        Returns:
            Tuple of (return_code, result_directory)
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(self.noop_home, "tmp", "emu_run", timestamp)
        os.makedirs(run_dir, exist_ok=True)
        
        self.logger.info(f"Running module emulator with workload: {workload}")
        
        cmd = f"cd {self.noop_home} && source env.sh && {self.emu_path}"
        cmd += f" -i {workload}"
        cmd += f" -m {max_cycle}"
        
        if dump_wave:
            wave_path = os.path.join(run_dir, "trace.vcd")
            cmd += f" -v {wave_path}"
        
        log_file = os.path.join(run_dir, "emu.log")
        cmd += f" > {log_file} 2>&1"
        cmd = f"bash -c '{cmd}'"
        
        return_code = run_command(cmd, shell=True)
        
        self._results = {
            "return_code": return_code,
            "run_dir": run_dir,
            "emu_path": self.emu_path,
            "workload": workload,
            "wave_file": os.path.join(run_dir, "wave.vcd") if dump_wave else None
        }
        
        self.logger.info(f"Module emulator finished with return code: {return_code}")
        return return_code, run_dir
    
    def get_results(self) -> Dict[str, Any]:
        """Get emulator results"""
        return self._results.copy()


# =============================================================================
# Module Fuzzer Manager
# =============================================================================

class ModuleFuzzerManager(FuzzerManagerBase):
    """
    Fuzzer manager for module-level projects
    
    Build: make modules XFUZZ=1 EMU_TRACE=1
    
    Snapshots are VCD waveforms stored in fuzz_run/{fuzz_id}/ directories.
    Format: snapshot-{cycle}.vcd, where cycle serves as the flag.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.project_name = config.get("project_name", "rocket_dcache")
        self.cover_type = config.get("cover_type", "toggle")
        self.noop_home = config.get("noop_home", "")
        self.bmcfuzz_home = config.get("bmcfuzz_home", "")
        
        self.fuzzer_path = os.path.join(self.noop_home, "build", "fuzzer")
        self._results: Dict[str, Any] = {}
    
    def build(self, make_args: str = "", **kwargs) -> bool:
        """
        Build module fuzzer: make modules XFUZZ=1 EMU_TRACE=1
        
        Args:
            make_args: Additional make arguments
        
        Returns:
            True if successful
        """
        self.logger.info(f"Building module fuzzer for {self.project_name}")
        
        make_command = (
            f"cd {self.noop_home} && source env.sh && "
            f"make modules XFUZZ=1 EMU_TRACE=1 {make_args} -j16"
        )
        
        log_file = os.path.join(self.noop_home, "tmp", "make_fuzzer.log")
        make_command += f" > {log_file} 2>&1"
        make_command = f"bash -c '{make_command}'"
        
        return_code = run_command(make_command, shell=True)
        
        if return_code == 0:
            self.logger.info("Module fuzzer build completed successfully")
            return True
        else:
            self.logger.error(f"Module fuzzer build failed with return code {return_code}")
            return False
    
    def run(self, corpus_dir: str, max_runs: int = 0, formal_cover_rate: Optional[float] = None,
            max_instr: int = 10000, max_cycle: int = 10000,
            run_snapshot: bool = False, dump_snapshot: bool = True,
            continue_on_errors: bool = True,
            only_fuzz: bool = False,
            save_errors: bool = False, no_diff: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Run module fuzzer with corpus
        
        Args:
            corpus_dir: Corpus directory path
            max_runs: Maximum runs (0 = unlimited)
            max_cycle: Maximum simulation cycles per run
            dump_wave: Enable snapshot VCD dumping
            continue_on_errors: Continue on errors
            save_errors: Save error cases
            (max_instr, snapshot_id, dump_csr, no_diff
             are accepted for interface compatibility but unused)
        
        Returns:
            Dictionary with fuzzer results
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(self.noop_home, "tmp", "fuzz_run")
        shutil.rmtree(run_dir, ignore_errors=True)
        os.makedirs(run_dir, exist_ok=True)
        
        self.logger.info(f"Running module fuzzer from corpus: {corpus_dir}")
        
        # Fuzzer command (same structure as cpu_init)
        cmd = f"cd {self.noop_home} && source env.sh && {self.fuzzer_path} -f"
        cmd += f" -c {self.cover_type}"
        
        if max_runs > 0:
            cmd += f" --max-runs {max_runs}"
        
        if formal_cover_rate is not None:
            cmd += f" --formal-cover-rate {formal_cover_rate}"
        
        if corpus_dir:
            cmd += f" --corpus-input {corpus_dir}"
        
        if continue_on_errors:
            cmd += " --continue-on-errors"
        
        if save_errors:
            cmd += " --save-errors"
        
        if only_fuzz:
            cmd += " --only-fuzz"
        
        formal_cover_points_file = os.path.join(self.bmcfuzz_home, "formal_run", "cover_points.csv")
        if os.path.exists(formal_cover_points_file):
            cmd += f" --cover-points-file {formal_cover_points_file}"
        
        # Module-specific sim args after -- separator
        cmd += f" -- -m {max_cycle}"

        if run_snapshot:
            cmd += " --run-snapshot"
        
        if dump_snapshot:
            cmd += " --dump-snapshot"
        
        log_file = os.path.join(self.bmcfuzz_home, "logs", "fuzz", f"fuzzer-{timestamp}.log")
        cmd += f" > {log_file} 2>&1"
        cmd = f"bash -c '{cmd}'"
        
        start_time = time.time()
        return_code = run_command(cmd, shell=True)
        elapsed_time = time.time() - start_time
        
        self._results = self._collect_results(run_dir, return_code, elapsed_time)
        
        self.logger.info(f"Module fuzzer finished with return code: {return_code}")
        return self._results
    
    def _collect_results(self, run_dir: str, return_code: int, 
                         elapsed_time: float) -> Dict[str, Any]:
        """Collect fuzzer results"""
        return {
            "success": True,
            "return_code": return_code,
            "run_dir": run_dir,
            "time_elapsed": elapsed_time,
            "coverage": self._parse_coverage(),
            "snapshots": self._collect_snapshots(),
            "errors": self._collect_errors()
        }
    
    def _parse_coverage(self) -> Dict[str, Any]:
        """Parse coverage data from cover_points.csv (same format as cpu_init)"""
        coverage = {
            "total": 0,
            "covered": 0,
            "percentage": 0.0,
            "points": []
        }
        cover_file = os.path.join(self.noop_home, "tmp", "fuzz_run", "cover_points.csv")
        
        if os.path.exists(cover_file):
            try:
                with open(cover_file, 'r') as f:
                    lines = f.readlines()
                    coverage["total"] = len(lines) - 1  # Exclude header
                    for line in lines[1:]:  # Skip header
                        parts = line.strip().split(',')
                        if len(parts) >= 2:
                            status = int(parts[1])
                            coverage["points"].append(status)
                            if status == 1:
                                coverage["covered"] += 1
                        else:
                            coverage["points"].append(0)
                if coverage["total"] > 0:
                    coverage["percentage"] = (coverage["covered"] / coverage["total"]) * 100
            except Exception as e:
                self.logger.error(f"Error parsing coverage: {e}")
        
        return coverage
    
    def _collect_snapshots(self) -> List[Dict]:
        """
        Collect snapshots from fuzz_run/ directory.

        Files are directly in fuzz_run_dir (no fuzz_id subdirectories):
          - wave:  snapshot-{fuzz_id}-{cycle}.fst
          - flag:  control_cover_points-{fuzz_id}-{cycle}.csv

        A valid snapshot requires both files with matching fuzz_id and cycle.
        The flag path points to the CSV file for scorer parsing.
        """
        snapshots = []
        fuzz_run_dir = os.path.join(self.noop_home, "tmp", "fuzz_run")

        if not os.path.exists(fuzz_run_dir):
            return snapshots

        # Index wave files by (fuzz_id, cycle)
        wave_map: dict[tuple[str, str], str] = {}
        flag_map: dict[tuple[str, str], str] = {}

        for fname in os.listdir(fuzz_run_dir):
            fpath = os.path.join(fuzz_run_dir, fname)
            if not os.path.isfile(fpath):
                continue

            wave_match = re.match(r"snapshot-(\d+)-(\d+)\.fst$", fname)
            if wave_match:
                key = (wave_match.group(1), wave_match.group(2))
                wave_map[key] = fpath
                continue

            flag_match = re.match(
                r"control_cover_points-(\d+)-(\d+)\.csv$", fname
            )
            if flag_match:
                key = (flag_match.group(1), flag_match.group(2))
                flag_map[key] = fpath

        # Only keep entries that have both wave and flag
        for key in wave_map.keys() & flag_map.keys():
            snapshots.append({
                "flag": flag_map[key],
                "wave": wave_map[key],
                "snapshot": "",
            })

        return snapshots
    
    def _collect_errors(self) -> List[str]:
        """Collect error cases"""
        errors = []
        errors_dir = os.path.join(self.noop_home, "errors")
        
        if os.path.exists(errors_dir):
            errors = os.listdir(errors_dir)
        
        return errors
    
    def get_fuzz_inputs(self) -> List[str]:
        """Get fuzz inputs"""
        fuzz_input_file = os.path.join(self.noop_home, "modules", "fuzz_inputs.txt")
        if os.path.exists(fuzz_input_file):
            with open(fuzz_input_file, "r") as f:
                return f.readlines()
        return []
    
    def get_coverage(self) -> Dict[str, Any]:
        """Get coverage data"""
        if self._results.get("coverage") is None:
            self._results["coverage"] = self._parse_coverage()
        return self._results["coverage"].copy()
    
    def get_snapshots(self) -> List[Dict]:
        """Get snapshots"""
        if self._results.get("snapshots") is None:
            self._results["snapshots"] = self._collect_snapshots()
        return self._results["snapshots"].copy()
    
    def get_results(self) -> Dict[str, Any]:
        """Get fuzzer results"""
        if self._results.get("success") is None:
            self.logger.warning("Fuzzer results not available yet. Returning empty results.")
        return self._results.copy()


# =============================================================================
# Factory Functions
# =============================================================================

def get_module_config(project_name: str, bmcfuzz_home: str,
                      cover_type: str = "toggle") -> Dict[str, Any]:
    """
    Get configuration for a module project
    
    Args:
        project_name: Module project name (e.g., rocket_dcache)
        bmcfuzz_home: BMCFuzz home directory
        cover_type: Coverage type
    
    Returns:
        Configuration dictionary
    """
    if project_name not in Config.MODULE_PROJECTS:
        raise ValueError(f"Unknown module project: {project_name}. "
                         f"Supported: {list(Config.MODULE_PROJECTS)}")
    
    project_info = MODULE_PROJECT_CONFIGS[project_name]
    noop_home = os.path.join(bmcfuzz_home, project_info["noop_home_suffix"])
    
    return {
        "project_name": project_name,
        "project_dir": noop_home,
        "bmcfuzz_home": bmcfuzz_home,
        "noop_home": noop_home,
        "rtl_dir": os.path.join(noop_home, "modules", "rtl"),
        "formal_rtl_dir": os.path.join(bmcfuzz_home, "formal_run", "rtl"),
        "cover_type": cover_type,
        "rtl_generator": ModuleRTLGenerator,
        "emu_manager": ModuleEmulatorManager,
        "fuzzer_manager": ModuleFuzzerManager
    }


def create_module_rtl_init(project_name: str, bmcfuzz_home: str,
                            cover_type: str = "toggle"):
    """
    Create RTLInit instance for a module project
    
    Args:
        project_name: Module project name (e.g., rocket_dcache)
        bmcfuzz_home: BMCFuzz home directory
        cover_type: Coverage type
    
    Returns:
        RTLInit instance
    """
    from rtl.rtl_init import RTLInit
    
    config = get_module_config(project_name, bmcfuzz_home, cover_type)
    return RTLInit(config=config)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    'ModuleRTLGenerator',
    'ModuleEmulatorManager', 
    'ModuleFuzzerManager',
    'get_module_config',
    'create_module_rtl_init'
]

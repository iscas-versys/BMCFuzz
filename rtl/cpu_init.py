"""
CPU-specific implementations for RTL initialization

This module provides concrete implementations for CPU projects
(nutshell, rocket, boom) to work with RTLInit.

Usage:
    from rtl.cpu_init import get_cpu_config, create_cpu_rtl_init
    
    # Method 1: Get config and create RTLInit
    config = get_cpu_config("nutshell", bmcfuzz_home, noop_home)
    rtl = RTLInit(config=config)
    
    # Method 2: Direct creation
    rtl = create_cpu_rtl_init("rocket", bmcfuzz_home, noop_home)
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


# =============================================================================
# CPU RTL Generator
# =============================================================================

class CPURTLGenerator(RTLGeneratorBase):
    """
    RTL generator for CPU projects (nutshell, rocket, boom)
    
    Handles:
    - Building RTL from source
    - Preparing formal verification RTL
    - Managing RTL file paths
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cpu_type = config.get("cpu_type", "rocket")
        self.cover_type = config.get("cover_type", "toggle")
        self.noop_home = config.get("noop_home", "")
        self.bmcfuzz_home = config.get("bmcfuzz_home", "")
        self.formal_rtl_dir = config.get("formal_rtl_dir", "")

        os.makedirs(os.path.join(self.noop_home, "tmp"), exist_ok=True)
        
        # Reset cycles for different CPUs
        self.reset_cycles = {
            "nutshell": 6,
            "rocket": 24,
            "boom": 35
        }
    
    def build(self, make_args: str = "", **kwargs) -> bool:
        """
        Build RTL code from source
        
        Args:
            make_args: Additional make arguments
        
        Returns:
            True if successful
        """
        self.logger.info(f"Building RTL for {self.cpu_type}, cover_type={self.cover_type}")
        
        build_command = (
            f"cd {self.noop_home} && source env.sh && unset VERILATOR_ROOT && "
            f"make clean && make src REF=$(pwd)/ready-to-run/riscv64-spike-so "
            f"FIRRTL_COVER={self.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 "
            f"-j16 {make_args}"
        )
        
        log_file = os.path.join(self.noop_home, "tmp", "make_rtl.log")
        build_command += f" > {log_file} 2>&1"
        build_command = f"bash -c '{build_command}'"
        
        return_code = run_command(build_command, shell=True)

        # Append array files if nutshell
        if self.cpu_type == "nutshell":
            src_rtl = os.path.join(self.noop_home, "build", "rtl", "SimTop.sv")
            
            if os.path.exists(src_rtl):
                if self.cpu_type == "nutshell":
                    lines = self._append_array_file()
                
                with open(src_rtl, 'a') as f:
                    f.writelines(lines)
                
                self.logger.info("Nutshell: Appended array files to SimTop.sv")
        
        # copy memory helper files from template
        self._copy_memory_files()
        
        if return_code == 0:
            self.logger.info("RTL build completed successfully")
            return True
        else:
            self.logger.error(f"RTL build failed with return code {return_code}")
            return False
    
    def get_rtl_info(self) -> Dict[str, Any]:
        """
        Get rtl info
        """
        top_module = "SimTop"
        rtl_file = os.path.join(self.noop_home, "build", "rtl", "SimTop.sv")
        
        rtl_info = {
            "top_module": top_module,
            "rtl_file": rtl_file,
            "rtl_dir": self.noop_home
        }
        
        return rtl_info
    
    def prepare_formal(self, **kwargs) -> str:
        """
        Prepare RTL for formal verification
        
        Args:
            snapshot_id: Optional snapshot ID for initialization
        
        Returns:
            Formal RTL directory path
        """
        os.makedirs(self.formal_rtl_dir, exist_ok=True)
        
        self.logger.info(f"Preparing formal RTL in {self.formal_rtl_dir}")

        # Copy SimTop.sv
        src_rtl = os.path.join(self.noop_home, "build", "rtl", "SimTop.sv")
        dst_rtl = os.path.join(self.formal_rtl_dir, "SimTop.sv")
        
        if os.path.exists(src_rtl):
            with open(src_rtl, 'r') as f:
                lines = f.readlines()
            
            # Modify enToggle values
            lines = self._modify_enToggle_value(lines)
            
            with open(dst_rtl, 'w') as f:
                f.writelines(lines)
        
        # Copy other RTL files
        self._copy_other_rtl_files()
        
        return dst_rtl
    
    def get_cover_points_name(self) -> List[Tuple[str, str]]:
        """ Parse firrtl-cover.cpp to get cover point names """
        cover_points_name = []
        cover_name_file = os.path.join(self.noop_home, "build", "generated-src", "firrtl-cover.cpp")

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
                        # log_message(f"module_name: {module_name}, signal_name: {signal_name}", False)
                        cover_points_name.append((module_name, signal_name))
        return cover_points_name
    
    def _copy_memory_files(self):
        """Copy memory helper files from template to proper location"""
        memory_dir = os.path.join(self.bmcfuzz_home, "rtl", "memory", self.cpu_type)
        src = os.path.join(memory_dir, "MemRWHelper_difftest.v")
        dst = os.path.join(self.noop_home, "build", "rtl", "MemRWHelper.v")
        if os.path.exists(src):
            shutil.copy(src, dst)
    
    def _modify_enToggle_value(self, src_lines: List[str]) -> List[str]:
        """Change enToggle and enToggle_past values"""
        for i, line in enumerate(src_lines):
            elements = line.split()
            if len(elements) > 1 and elements[0] == "reg":
                if elements[1] == "enToggle" or elements[1] == "enToggle_past":
                    src_lines[i] = src_lines[i].replace("1'h0", "1'h1")
        return src_lines
    
    def _append_array_file(self) -> List[str]:
        """Append array files to SimTop (nutshell specific)"""
        rtl_dir = os.path.join(self.noop_home, "build", "rtl")
        
        array_lines = []
        with os.scandir(rtl_dir) as entries:
            for entry in entries:
                if entry.name.startswith("array"):
                    self.logger.debug(f"Appending {entry.name} to SimTop")
                    with open(entry.path, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            ram_match = re.search(r"ram \[(\d+):0\]", line)
                            if ram_match:
                                line = line.replace(
                                    f"ram [{ram_match.group(1)}:0]",
                                    f"ram [0:{ram_match.group(1)}]"
                                )
                            array_lines.append(line)
                    os.remove(os.path.join(rtl_dir, entry.name))
        return array_lines
    
    def _copy_other_rtl_files(self):
        """Copy RTL files"""
        rtl_dir = os.path.join(self.noop_home, "build", "rtl")
        
        for item in os.listdir(rtl_dir):
            # if item.startswith("GEN_") or item in ["MemRWHelper.v"]:
            if item.endswith(('.v', '.sv')):
                if item.startswith("array") or item.startswith("SimTop"):
                    continue
                src = os.path.join(rtl_dir, item)
                dst = os.path.join(self.formal_rtl_dir, item)
                if os.path.isfile(src):
                    shutil.copy(src, dst)
        
        # Copy memory helpers from template if available
        memory_dir = os.path.join(self.bmcfuzz_home, "rtl", "memory", self.cpu_type)
        src = os.path.join(memory_dir, "MemRWHelper_formal.v")
        dst = os.path.join(self.formal_rtl_dir, "MemRWHelper.v")
        shutil.copy(src, dst)

        # Copy formal top module if exists
        formal_top = os.path.join(self.bmcfuzz_home, "rtl", "formal", self.cpu_type, "FormalTop.sv")
        if os.path.exists(formal_top):
            shutil.copy(formal_top, os.path.join(self.formal_rtl_dir, "FormalTop.sv"))
    
    # def _copy_firrtl_cover(self):
    #     """Copy firrtl-cover.cpp"""
    #     src = os.path.join(self.noop_home, "build", "generated-src", "firrtl-cover.cpp")
    #     dst = os.path.join(self.formal_rtl_dir, "firrtl-cover.cpp")
    #     if os.path.exists(src):
    #         shutil.copy(src, dst)
    
# =============================================================================
# CPU Emulator Manager
# =============================================================================

class CPUEmulatorManager(EmulatorManagerBase):
    """
    Emulator manager for CPU projects
    
    Handles:
    - Building emulator
    - Running emulator with workloads
    - Managing outputs
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cpu_type = config.get("cpu_type", "nutshell")
        self.cover_type = config.get("cover_type", "toggle")
        self.noop_home = config.get("noop_home", "")
        self.bmcfuzz_home = config.get("bmcfuzz_home", "")
        
        self._results: Dict[str, Any] = {}
        self.emu_path = os.path.join(self.noop_home, "build", "emu")
    
    def build(self, trace: bool = True, snapshot: bool = True, 
              make_args: str = "", **kwargs) -> bool:
        """
        Build emulator
        
        Args:
            trace: Enable waveform tracing
            snapshot: Enable snapshot support
            make_args: Additional make arguments
        
        Returns:
            True if successful
        """
        self.logger.info(f"Building emulator for {self.cpu_type}")
        
        make_flags = [f"FIRRTL_COVER={self.cover_type}"]
        if trace:
            make_flags.append("EMU_TRACE=1")
        if snapshot:
            make_flags.append("EMU_SNAPSHOT=1")
        
        make_command = (
            f"cd {self.noop_home} && source env.sh && unset VERILATOR_ROOT && "
            f"make emu REF=$(pwd)/ready-to-run/riscv64-spike-so "
            f"{' '.join(make_flags)} -j16 {make_args}"
        )
        
        log_file = os.path.join(self.noop_home, "tmp", "make_emu.log")
        make_command += f" > {log_file} 2>&1"
        make_command = f"bash -c '{make_command}'"
        
        return_code = run_command(make_command, shell=True)
        
        if return_code == 0:
            self.logger.info("Emulator build completed successfully")
            return True
        else:
            self.logger.error(f"Emulator build failed with return code {return_code}")
            return False
    
    def run(self, workload: str, max_instr: int = 10000, max_cycle: int = 10000,
            snapshot_id: int = None, dump_wave: bool = True, dump_commit_trace: bool = True, dump_csr: bool = False,
            no_diff: bool = False, **kwargs) -> Tuple[int, str]:
        """
        Run emulator with workload
        
        Args:
            workload: Workload file path
            max_instr: Maximum instructions
            max_cycle: Maximum cycles
            snapshot_id: Snapshot ID to load
            dump_wave: Dump waveform
            dump_csr: Dump CSR changes
            no_diff: Disable diff test
        
        Returns:
            Tuple of (return_code, result_directory)
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(self.noop_home, "tmp", "emu_run", timestamp)
        os.makedirs(run_dir, exist_ok=True)
        
        self.logger.info(f"Running emulator with workload: {workload}")
        
        # Build command
        cmd = f"cd {self.noop_home} && source env.sh && {self.emu_path}"
        cmd += f" -i {workload}"
        cmd += f" -I {max_instr}"
        cmd += f" -C {max_cycle}"
        
        if dump_wave:
            wave_path = os.path.join(run_dir, "wave.vcd")
            cmd += f" --dump-wave-full --wave-path {wave_path}"
        
        if dump_commit_trace:
            cmd += f" --dump-commit-trace"
            if not no_diff:
                cmd += " --dump-ref-trace"
        
        if dump_csr:
            csr_dir = os.path.join(run_dir, "csr")
            os.makedirs(csr_dir, exist_ok=True)
            cmd += " --dump-csr-change"
        
        if snapshot_id is not None:
            cmd += f" --run-snapshot"
            snapshot_file = os.path.join(
                self.bmcfuzz_home, "snapshots", str(snapshot_id)
            )
            cmd += f" --load-snapshot {snapshot_file}"
        
        if no_diff:
            cmd += " --no-diff"
        
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
        
        self.logger.info(f"Emulator finished with return code: {return_code}")
        return return_code, run_dir
    
    def get_results(self) -> Dict[str, Any]:
        """Get emulator results"""
        return self._results.copy()


# =============================================================================
# CPU Fuzzer Manager
# =============================================================================

class CPUFuzzerManager(FuzzerManagerBase):
    """
    Fuzzer manager for CPU projects
    
    Handles:
    - Building fuzzer
    - Running fuzzer with corpus
    - Collecting results (coverage, snapshots, waves)
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cpu_type = config.get("cpu_type", "nutshell")
        self.cover_type = config.get("cover_type", "toggle")
        self.noop_home = config.get("noop_home", "")
        self.bmcfuzz_home = config.get("bmcfuzz_home", "")
        
        self.fuzzer_path = os.path.join(self.noop_home, "build", "fuzzer")
        self._results: Dict[str, Any] = {}
    
    def build(self, make_args: str = "", **kwargs) -> bool:
        """
        Build fuzzer
        
        Args:
            make_args: Additional make arguments
            run_snapshot: Whether to prepare for snapshot mode
        
        Returns:
            True if successful
        """
        self.logger.info(f"Building fuzzer for {self.cpu_type}")
        
        # Build emu first
        # if run_snapshot:
        make_command = (
            f"cd {self.noop_home} && source env.sh && unset VERILATOR_ROOT && "
            f"make fuzzer REF=$(pwd)/ready-to-run/riscv64-spike-so "
            f"XFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 -j16"
        )
        # else:
        #     make_command = (
        #         f"cd {self.noop_home} && source env.sh && unset VERILATOR_ROOT && "
        #         f"make clean && make emu REF=$(pwd)/ready-to-run/riscv64-spike-so "
        #         f"XFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 -j16"
        #     )
        
        log_file = os.path.join(self.noop_home, "tmp", "make_fuzzer.log")
        
        make_command += f" > {log_file} 2>&1"
        make_command = f"bash -c '{make_command}'"
        
        return_code = run_command(make_command, shell=True)
        
        if return_code == 0:
            self.logger.info("Fuzzer build completed successfully")
            return True
        else:
            self.logger.error(f"Fuzzer build failed with return code {return_code}")
            return False
    
    def run(self, corpus_dir: str, max_runs: int = 0, formal_cover_rate: Optional[float] = None,
            max_instr: int = 10000, max_cycle: int = 10000, snapshot_id: int = None, dump_csr: bool = True,
            dump_wave: bool = True, continue_on_errors: bool = True,
            save_errors: bool = True, no_diff: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Run fuzzer with corpus
        
        Args:
            corpus_dir: Corpus directory path
            max_runs: Maximum runs (0 = unlimited)
            max_instr: Maximum instructions per run
            max_cycle: Maximum cycles per run
            snapshot_id: Snapshot ID to load
            dump_csr: Dump CSR changes
            dump_wave: Dump waveform
            continue_on_errors: Continue on errors
            save_errors: Save error cases
            no_diff: Disable diff test
        
        Returns:
            Dictionary with fuzzer results
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(self.noop_home, "tmp", "fuzzer")
        os.makedirs(run_dir, exist_ok=True)
        
        self.logger.info(f"Running fuzzer from corpus: {corpus_dir}")
        
        # Build fuzzer command
        cmd = f"cd {self.noop_home} && source env.sh && {self.fuzzer_path} -f"
        cmd += f" -c firrtl.{self.cover_type}"
        
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
        
        formal_cover_points_file = os.path.join(self.bmcfuzz_home, "formal_run", "cover_points.csv")
        if os.path.exists(formal_cover_points_file):
            cmd += f" --cover-points-file {formal_cover_points_file}"
        
        # Emulator options
        cmd += f" -- -I {max_instr} -C {max_cycle}"
        
        if dump_csr:
            cmd += " --dump-csr-change"
        
        if dump_wave:
            cmd += " --dump-wave-full"
        
        if snapshot_id is not None:
            snapshot_file = os.path.join(
                self.bmcfuzz_home, "snapshots", str(snapshot_id)
            )
            cmd += f" --run-snapshot --load-snapshot {snapshot_file}"
        
        if no_diff:
            cmd += " --no-diff"
        
        log_file = os.path.join(self.bmcfuzz_home, "logs", "fuzz", f"fuzzer-{timestamp}.log")
        cmd += f" > {log_file} 2>&1"
        cmd = f"bash -c '{cmd}'"
        
        start_time = time.time()
        return_code = run_command(cmd, shell=True)
        elapsed_time = time.time() - start_time
        
        # Collect results
        self._results = self._collect_results(run_dir, return_code, elapsed_time)
        
        self.logger.info(f"Fuzzer finished with return code: {return_code}")
        return self._results
    
    def _collect_results(self, run_dir: str, return_code: int, 
                         elapsed_time: float) -> Dict[str, Any]:
        """Collect fuzzer results"""
        results = {
            "success": True,
            "return_code": return_code,
            "run_dir": run_dir,
            "time_elapsed": elapsed_time,
            "coverage": self._parse_coverage(),
            "snapshots": self._collect_snapshots(),
            "errors": self._collect_errors()
        }
        return results
    
    def _parse_coverage(self) -> Dict[str, Any]:
        """
        Parse coverage data
        
        Returns:
            Dictionary with:
            - total: Total number of coverage points
            - covered: Number of covered points
            - percentage: Coverage percentage
            - points: List of coverage status for each point (0 or 1)
        """
        coverage = {
            "total": 0,
            "covered": 0,
            "percentage": 0.0,
            "points": []  # List of coverage status (0 or 1) for each point
        }
        cover_file = os.path.join(self.noop_home, "tmp", "cover_points.csv")
        
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
        Collect snapshots (each snapshot contains score csv and corresponding wave vcd)
        
        A snapshot is a collection containing:
        - id: Snapshot identifier
        - score_csv: CSV file recording key register states/transitions (for scoring)
        - wave_vcd: VCD waveform file for corresponding clock cycles
        
        Returns:
            List of snapshot dictionaries with score_csv and wave_vcd paths
        """
        snapshots = []
        fuzz_run_dir = os.path.join(self.noop_home, "tmp", "fuzz_run")
        
        if not os.path.exists(fuzz_run_dir):
            return snapshots
        
        # Iterate through each run directory
        for run_id in os.listdir(fuzz_run_dir):
            run_dir = os.path.join(fuzz_run_dir, run_id)
            if not os.path.isdir(run_dir):
                continue
            
            csr_trans_dir = os.path.join(run_dir, "csr_transition")
            csr_wave_dir = os.path.join(run_dir, "csr_wave")
            csr_snapshot_dir = os.path.join(run_dir, "csr_snapshot")
            
            if not os.path.exists(csr_trans_dir):
                continue
                
            for wave_file in os.listdir(csr_wave_dir):
                snapshot_id_match = re.search(r"csr_wave_(\d+)", wave_file)
                snapshot_id = snapshot_id_match.group(1)
                
                csr_wave_path = os.path.join(csr_wave_dir, wave_file)
                csr_transition_path = os.path.join(csr_trans_dir, f"csr_transition_{snapshot_id}.csv")
                csr_snapshot_path = os.path.join(csr_snapshot_dir, f"csr_snapshot_{snapshot_id}")

                # self.logger.debug(f"Adding snapshot: {snapshot_id}, wave: {csr_wave_path}, transition: {csr_transition_path}, snapshot: {csr_snapshot_path}")

                snapshots.append({
                    "flag": csr_transition_path,
                    "wave": csr_wave_path,
                    "snapshot": csr_snapshot_path
                })
        
        return snapshots
    
    def _collect_errors(self) -> List[str]:
        """Collect error cases"""
        errors = []
        errors_dir = os.path.join(self.noop_home, "errors")
        
        if os.path.exists(errors_dir):
            errors = os.listdir(errors_dir)
        
        return errors
    
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

def get_cpu_config(cpu_type: str, bmcfuzz_home: str, noop_home: str,
                   cover_type: str = "toggle") -> Dict[str, Any]:
    """
    Get configuration for a CPU project
    
    Args:
        cpu_type: CPU type (nutshell, rocket, boom)
        bmcfuzz_home: BMCFuzz home directory
        noop_home: NOOP home directory (project directory)
        cover_type: Coverage type
    
    Returns:
        Configuration dictionary
    """
    return {
        "project_name": cpu_type,
        "project_dir": noop_home,
        "cpu_type": cpu_type,
        "bmcfuzz_home": bmcfuzz_home,
        "noop_home": noop_home,
        "rtl_dir": os.path.join(noop_home, "build", "rtl"),
        "formal_rtl_dir": os.path.join(bmcfuzz_home, "formal_run", "rtl"),
        "cover_type": cover_type,
        "rtl_generator": CPURTLGenerator,
        "emu_manager": CPUEmulatorManager,
        "fuzzer_manager": CPUFuzzerManager
    }


def create_cpu_rtl_init(cpu_type: str, bmcfuzz_home: str, cover_type: str = "toggle"):
    """
    Create RTLInit instance for a CPU project
    
    Args:
        cpu_type: CPU type (nutshell, rocket, boom)
        bmcfuzz_home: BMCFuzz home directory
        noop_home: NOOP home directory
        cover_type: Coverage type
    
    Returns:
        RTLInit instance
    """
    from rtl.rtl_init import RTLInit

    noop_home_dict = {
        "nutshell": os.path.join(bmcfuzz_home, "rtl", "nutshell"),
        "rocket": os.path.join(bmcfuzz_home, "rtl", "rocket"),
        "boom": os.path.join(bmcfuzz_home, "rtl", "boom")
    }
    
    config = get_cpu_config(cpu_type, bmcfuzz_home, noop_home_dict[cpu_type], cover_type)
    return RTLInit(config=config)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    'CPURTLGenerator',
    'CPUEmulatorManager', 
    'CPUFuzzerManager',
    'get_cpu_config',
    'create_cpu_rtl_init'
]
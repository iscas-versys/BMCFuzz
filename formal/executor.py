"""
Formal verification executor for BMCFuzz

This module is responsible for generating sby files for coverage points
and executing BMC verification tasks.
"""

import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable, Any
from tqdm import tqdm
import shutil

from core.config import Config
from utils.logger import BMCFuzzLogger
from utils.command import run_command


class FormalExecutor:
    """
    Formal verification executor
    
    Generates sby files for coverage points and executes BMC verification
    using SymbiYosys (sby). Results are processed by a seed generator callback.
    """
    
    def __init__(self):
        """Initialize FormalExecutor"""
        self.logger = BMCFuzzLogger.get_logger("FormalExecutor")
        self.bmcfuzz_home = Config.BMCFUZZ_HOME
        self.sby_path = Config.SBY_PATH
        self.oss_cad_suite_env = Config.OSS_CAD_SUITE_ENV
        self.rIC3_path = Config.RIC3_PATH
        self.formal_run_dir = Config.FORMAL_RUN_DIR
        self.max_workers = Config.FORMAL_MAX_WORKERS
        # self.timeout = Config.FORMAL_TIMEOUT
        
        # Paths
        self.rtl_dir = os.path.join(self.formal_run_dir, "rtl")
        self.corpus_dir = Config.CORPUS_DIR
        self.template_path = os.path.join(
            self.bmcfuzz_home,
            "formal", "template.sby"
        )
        
        # Ensure directories exist
        os.makedirs(self.rtl_dir, exist_ok=True)
        os.makedirs(self.corpus_dir, exist_ok=True)
        os.makedirs(self.formal_run_dir, exist_ok=True)
        
        # Seed generator callback
        self.seed_generator: Optional[Callable] = None
        
        # Project and mode configuration
        self.project_name = None
        self.mode = None  # "smt" or "sat"
        self.cover_type = None
        
        # Load template
        self.template_content = self._load_template()
        
        self.logger.info("FormalExecutor initialized")
        self.logger.debug(f"BMCFUZZ_HOME: {self.bmcfuzz_home}")
        self.logger.debug(f"OSS_CAD_SUITE_ENV: {self.oss_cad_suite_env}")
        self.logger.debug(f"rIC3 path: {self.rIC3_path}")
        self.logger.debug(f"RTL dir: {self.rtl_dir}")
        self.logger.debug(f"Formal run dir: {self.formal_run_dir}")

        # Try to load oss-cad-suite environment
        if run_command(f"bash -c 'source {self.oss_cad_suite_env}'", shell=True) != 0:
            self.logger.error(
                f"Loading OSS CAD Suite environment failed: {self.oss_cad_suite_env}"
            )
            exit(1)
    
    def _load_template(self) -> str:
        """Load sby template file"""
        if not os.path.exists(self.template_path):
            self.logger.warning(f"Template not found: {self.template_path}")
            return ""
        
        with open(self.template_path, 'r') as f:
            content = f.read()
        self.logger.debug("Sby template loaded")
        return content
    
    def set_seed_generator(self, seed_generator: Callable):
        """
        Set seed generator callback
        
        Args:
            seed_generator: Callback function to process BMC results
        """
        self.seed_generator = seed_generator
        self.logger.info("Seed generator callback set")
    
    def configure(self, project_name: str, mode: str, cover_type: str):
        """
        Configure executor for specific project and mode

        Args:
            project_name: Project name ("nutshell", "rocket", "boom", or custom)
            mode: Solver mode ("smt" or "sat")
            cover_type: Coverage type ("toggle", "line", "control")
        """
        self.project_name = project_name
        self.mode = mode
        self.cover_type = cover_type

        self.logger.info(
            f"Configured for project_name={project_name}, mode={mode}, cover_type={cover_type}"
        )
    
    def get_default_config(self) -> dict:
        """
        Get default configuration for current CPU and mode
        
        Returns:
            Dictionary with depth and timeout settings
        """
        configs = {
            'nutshell': {'depth': 90, 'timeout': 2 * 3600},
            'rocket': {'depth': 75, 'timeout': 3 * 3600},
            'boom': {'depth': 75, 'timeout': 4 * 3600},
            'rocket_dcache': {'depth': 300, 'timeout': 10 * 60},
            'rocket_fpu': {'depth': 300, 'timeout': 10 * 60},
        }

        default = {'depth': 300, 'timeout': 10 * 60}
        return configs.get(self.project_name, default)
    
    def generate_sby_files(self, cover_points: List[int]) -> bool:
        """
        Generate sby files for coverage points
        
        Args:
            cover_points: List of coverage point IDs
        
        Returns:
            True if successful, False otherwise
        """
        if not self.template_content:
            self.logger.error("No template content available")
            return False
        
        if not os.path.exists(self.rtl_dir):
            self.logger.error(f"RTL directory not found: {self.rtl_dir}")
            return False
        
        # Get RTL files
        rtl_files = [
            os.path.join(self.rtl_dir, f) 
            for f in os.listdir(self.rtl_dir) 
            if f.endswith('.v') or f.endswith('.sv')
        ]
        
        if not rtl_files:
            self.logger.warning(f"No RTL files found in {self.rtl_dir}")
        
        # Format formal and verilog file lists
        formal_files = '\n'.join([
            f"read -formal {os.path.basename(f)}" 
            for f in rtl_files
        ])
        verilog_files = '\n'.join(rtl_files)
        
        # Get default configuration
        config = self.get_default_config()
        default_depth = config['depth']
        default_timeout = config['timeout']
        
        # Set mode and engine
        if self.mode == "smt":
            sby_mode = "cover"
            engine = "smtbmc bitwuzla"
        elif self.mode == "sat":
            sby_mode = "bmc"
            engine = "aiger rIC3"
        else:
            self.logger.error(f"Unknown mode: {self.mode}")
            return False
        
        # Generate sby files for each cover point
        for cover_id in cover_points:
            cover_label = f"cov_count_{cover_id}"
            
            if self.mode == "smt":
                scripts = (
                    f"chformal -remove -cover c:{cover_label} %n\n"
                    f"chformal -assert2assume\n"
                )
            elif self.mode == "sat":
                scripts = f"chformal -remove -assert c:{cover_label} %n\n"
            
            # Format template (without define.sv reference)
            sby_file_content = self.template_content.format(
                mode=sby_mode,
                depth=default_depth,
                timeout=default_timeout,
                engines=engine,
                formal_files=formal_files,
                top_module_name="FormalTop",
                scripts=scripts,
                cover_label=cover_label,
                verilog_files=verilog_files
            )
            
            # Write sby file
            sby_file_path = os.path.join(
                self.formal_run_dir,
                f"cover_{cover_id}.sby"
            )
            with open(sby_file_path, 'w') as f:
                f.write(sby_file_content)
        
        self.logger.info(
            f"Generated {len(cover_points)} sby files in {self.formal_run_dir}"
        )
        return True
    
    def execute(self, cover_points: List[int]) -> Dict[str, Any]:
        """
        Execute formal verification for coverage points
        
        Args:
            cover_points: List of coverage point IDs
        
        Returns:
            List of successfully covered point IDs
        """
        self.logger.info(
            f"Executing formal verification for {len(cover_points)} points"
        )
        
        start_time = time.time()
        covered_points = []
        
        # Use ThreadPoolExecutor for parallel execution
        actual_workers = min(
            self.max_workers,
            len(cover_points),
            os.cpu_count()
        )
        
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            # Submit all tasks
            future_to_point = {
                executor.submit(self._execute_single_task, cover): cover
                for cover in cover_points
            }
            
            # Process completed tasks
            with tqdm(total=len(future_to_point), desc="Processing covers") as pbar:
                for future in as_completed(future_to_point):
                    point = future_to_point[future]
                    try:
                        result = future.result()
                        if result:
                            covered_points.append(point)
                                
                    except Exception as e:
                        self.logger.error(
                            f"Point {point} task failed: {e}"
                        )
                    pbar.update(1)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.logger.info(
            f"Formal verification completed: "
            f"{len(covered_points)}/{len(cover_points)} covered, "
            f"time: {execution_time:.2f}s"
        )
        
        return {
            "covered_points": covered_points,
            "execution_time": execution_time
        }
    
    def _execute_single_task(self, cover_point: int) -> bool:
        """
        Execute single formal verification task
        
        Args:
            cover_point: Coverage point ID to verify
        
        Returns:
            True if point is covered, False otherwise
        """
        sby_file = os.path.join(
            self.formal_run_dir,
            f"cover_{cover_point}.sby"
        )
        
        # Check if sby file exists
        if not os.path.exists(sby_file):
            self.logger.warning(
                f"Sby file not found for point {cover_point}: {sby_file}"
            )
            return False
        
        # Build sby command with oss-cad-suite environment
        # For SAT mode, add --rIC3 parameter
        if self.mode == "sat":
            sby_command = (
                f"source {self.oss_cad_suite_env} && "
                f"{self.sby_path} --rIC3 {self.rIC3_path} -f {sby_file}"
            )
        else:
            sby_command = (
                f"source {self.oss_cad_suite_env} && "
                f"{self.sby_path} -f {sby_file}"
            )
        sby_command = f"bash -c '{sby_command}'"
        
        try:
            start_time = time.time()
            return_code = run_command(sby_command, shell=True)
            end_time = time.time()
            
            execution_time = end_time - start_time
            self.logger.debug(
                f"Point {cover_point}: execution time {execution_time:.2f}s, "
                f"return code {return_code}"
            )
            
            # Check if verification succeeded
            # Return code 0: successful verification (covered)
            # Return code 1: not covered
            # Return code 2: counterexample found (covered)
            if return_code == 0 and self.mode == "smt" or return_code == 2 and self.mode == "sat":
                # Call seed generator callback if set
                if self.seed_generator(cover_point, self.formal_run_dir) is not None:
                    self.logger.info(f"Point {cover_point} successfully verified")
                    return True
                else:
                    self.logger.info(f"Point {cover_point} not covered, return code: {return_code}")
                    return False
            else:
                self.logger.info(
                    f"Point {cover_point} not covered, return code: {return_code}"
                )
                return False
                
        except Exception as e:
            self.logger.error(
                f"Exception executing point {cover_point}: {e}"
            )
            return False
    
    def add_cover_statements(self, rtl_file: str = None) -> bool:
        """
        Add cover/assert statements to RTL file for cover blocks
        
        Parses RTL file to find cover blocks (GEN_w{len}_{cover_type}_{index})
        and adds corresponding cov_count_ statements:
        - SMT mode: cover(valid)
        - SAT mode: assert(~valid)
        
        Args:
            rtl_file: Path to RTL file (default: self.rtl_dir/SimTop.sv)
        
        Returns:
            True if successful, False otherwise
        """
        if rtl_file is None:
            rtl_file = os.path.join(self.rtl_dir, "SimTop.sv")
        
        if not os.path.exists(rtl_file):
            self.logger.error(f"RTL file not found: {rtl_file}")
            return False
        
        self.logger.info(f"Adding cover statements to {rtl_file}")
        
        try:
            with open(rtl_file, 'r') as f:
                lines = f.readlines()
            
            new_lines = []
            cover_type = self.cover_type or "toggle"
            
            # Patterns for cover block parsing
            cover_block_begin_pattern = re.compile(
                rf'GEN_w(\d+)_{cover_type}.*{cover_type}_(\d+)'
            )
            cover_block_end_pattern = re.compile(r'\);')
            cover_block_reset_pattern = re.compile(r"\.reset\((.*)\),")
            cover_block_valid_pattern = re.compile(r"\.valid\((.*)\)")
            
            cover_block_match = False
            cover_block_len = 0
            cover_block_reset = ""
            cover_block_valid = ""
            cov_counter = 0  # independent counter, not tied to RTL index
            
            for line in lines:
                new_lines.append(line)
                
                # Check for cover block begin
                cover_block_begin_match = cover_block_begin_pattern.search(line)
                if cover_block_begin_match:
                    cover_block_match = True
                    cover_block_len = int(cover_block_begin_match.group(1))
                
                # Extract reset and valid signals
                if cover_block_match:
                    cover_block_reset_match = re.search(cover_block_reset_pattern, line)
                    if cover_block_reset_match:
                        cover_block_reset = cover_block_reset_match.group(1)
                    
                    cover_block_valid_match = re.search(cover_block_valid_pattern, line)
                    if cover_block_valid_match:
                        cover_block_valid = cover_block_valid_match.group(1)
                    
                    # Check for cover block end
                    if re.search(cover_block_end_pattern, line):
                        cover_block_match = False
                        
                        # Add cover/assert statements
                        new_lines.append("  always @(posedge glb_clk) begin\n")
                        new_lines.append(f"    if (!{cover_block_reset}) begin\n")
                        
                        if cover_block_len > 1:
                            for i in range(cover_block_len):
                                if self.mode == "smt":
                                    new_lines.append(
                                        f"      cov_count_{cov_counter}: "
                                        f"cover({cover_block_valid}[{i}]);\n"
                                    )
                                elif self.mode == "sat":
                                    new_lines.append(
                                        f"      cov_count_{cov_counter}: "
                                        f"assert(~{cover_block_valid}[{i}]);\n"
                                    )
                                cov_counter += 1
                        else:
                            if self.mode == "smt":
                                new_lines.append(
                                    f"      cov_count_{cov_counter}: "
                                    f"cover({cover_block_valid});\n"
                                )
                            elif self.mode == "sat":
                                new_lines.append(
                                    f"      cov_count_{cov_counter}: "
                                    f"assert(~{cover_block_valid});\n"
                                )
                            cov_counter += 1
                        
                        new_lines.append("    end\n")
                        new_lines.append("  end\n")
            
            # Write modified content back
            with open(rtl_file, 'w') as f:
                f.writelines(new_lines)
            
            self.logger.info(f"Successfully added cover statements to {rtl_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding cover statements: {e}")
            return False
    
    def add_reg_initial_statements(self, rtl_file: str = None) -> int:
        """
        Insert ``initial assume(!reg)`` for every register in each module
        of *rtl_file*.  Memory arrays are zero-initialised with a for-loop.

        Used when there is no snapshot to provide initial register values,
        so that the formal tool starts from a constrained (all-zero) state.

        Args:
            rtl_file: Path to RTL file (default: self.rtl_dir/SimTop.sv)

        Returns:
            Total number of registers that received initial statements.
        """
        if rtl_file is None:
            rtl_file = os.path.join(self.rtl_dir, "SimTop.sv")

        if not os.path.exists(rtl_file):
            self.logger.error(f"RTL file not found: {rtl_file}")
            return 0

        self.logger.info(f"Inserting register initial statements in {rtl_file}")

        with open(rtl_file, 'r') as f:
            lines = f.readlines()

        # Detect module boundaries
        module_ranges: list[tuple[int, int]] = []
        current_start: int | None = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r'^module\s+', stripped):
                current_start = i
            elif stripped == 'endmodule' and current_start is not None:
                module_ranges.append((current_start, i))
                current_start = None

        total_regs = 0
        for start, end in reversed(module_ranges):
            module_text = ''.join(lines[start:end + 1])
            processed_text, count = self._insert_reg_initial(module_text)
            total_regs += count
            if count > 0:
                processed_lines = processed_text.splitlines(keepends=True)
                lines[start:end + 1] = processed_lines

        with open(rtl_file, 'w') as f:
            f.writelines(lines)

        self.logger.info(
            f"Inserted initial statements for {total_regs} registers in {rtl_file}"
        )
        return total_regs

    @staticmethod
    def _insert_reg_initial(module_text: str) -> tuple[str, int]:
        """
        Insert initial statements for all registers in a single module block.

        - Scalar registers:  ``initial assume(!<reg>);``
        - Memory arrays:     zero-initialised via ``for`` loop
        - ``_RAND_*`` helper registers are skipped.

        Returns:
            (processed_module_text, register_count)
        """
        scalar_reg_pat = re.compile(
            r'^\s+reg\s+(?:\[\d+:\d+\]\s+)?(\w+)\s*;', re.MULTILINE
        )
        mem_reg_pat = re.compile(
            r'^\s+reg\s+(?:\[\d+:\d+\]\s+)?(\w+)\s+\[(\d+):(\d+)\]\s*;',
            re.MULTILINE,
        )

        scalar_regs: list[str] = []
        mem_regs: list[tuple[str, int, int]] = []

        for m in scalar_reg_pat.finditer(module_text):
            name = m.group(1)
            if name.startswith("_RAND_"):
                continue
            scalar_regs.append(name)

        for m in mem_reg_pat.finditer(module_text):
            name = m.group(1)
            lo, hi = int(m.group(2)), int(m.group(3))
            if name.startswith("_RAND_"):
                continue
            mem_regs.append((name, lo, hi))

        mem_names = {name for name, _, _ in mem_regs}
        scalar_regs = [r for r in scalar_regs if r not in mem_names]

        if not scalar_regs and not mem_regs:
            return module_text, 0

        init_lines: list[str] = []
        for name in scalar_regs:
            init_lines.append(f"  initial assume(!{name});")

        if mem_regs:
            init_lines.append("  integer _init_i;")
            init_lines.append("  initial begin")
            for name, lo, hi in mem_regs:
                init_lines.append(
                    f"    for (_init_i = {lo}; _init_i <= {hi}; "
                    f"_init_i = _init_i + 1)"
                )
                init_lines.append(f"      {name}[_init_i] = '0;")
            init_lines.append("  end")

        init_block = "\n".join(init_lines) + "\n"

        module_text = module_text.rstrip()
        if module_text.endswith("endmodule"):
            module_text = (
                module_text[: -len("endmodule")] + init_block + "endmodule\n"
            )
        else:
            module_text += "\n" + init_block

        return module_text, len(scalar_regs) + len(mem_regs)

    def cleanup(self, cover_points: List[int] = None):
        """
        Clean up generated files
        
        Args:
            cover_points: List of coverage points to clean up.
                        If None, clean all files in formal_run_dir.
        """
        if cover_points is None:
            # Clean all files in formal_run_dir except rtl
            for item in os.listdir(self.formal_run_dir):
                item_path = os.path.join(self.formal_run_dir, item)
                if item == "rtl":
                    continue
                # if item == "corpus":
                #     continue
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            self.logger.info(f"Cleaned up {self.formal_run_dir}")
        else:
            # Clean specific coverage point files
            for point in cover_points:
                sby_file = os.path.join(
                    self.formal_run_dir,
                    f"cover_{point}.sby"
                )
                cover_dir = os.path.join(
                    self.formal_run_dir,
                    f"cover_{point}"
                )
                
                if os.path.exists(sby_file):
                    os.remove(sby_file)
                
                if os.path.exists(cover_dir):
                    shutil.rmtree(cover_dir)
            
            self.logger.info(
                f"Cleaned up {len(cover_points)} coverage point files"
            )

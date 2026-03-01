"""
Seed generator for parsing BMC verification results

This module acts as a callback for formal executor,
responsible for parsing BMC execution results and generating seeds
for fuzzing.
"""

import os
import re
from typing import List, Dict, Optional, Callable, Any
from abc import ABC, abstractmethod

from utils.logger import BMCFuzzLogger
from utils.command import run_command


class ResultParser(ABC):
    """
    Abstract base class for BMC result parsers
    
    Custom parsers can be implemented by extending this class.
    """
    
    @abstractmethod
    def parse(self, cover_point: int, formal_run_dir: str) -> Optional[Dict[str, Any]]:
        """
        Parse BMC result for a coverage point
        
        Args:
            cover_point: Coverage point ID
            formal_run_dir: Directory containing BMC results
        
        Returns:
            Dictionary with parsed data, or None if parsing failed
        """
        pass


class CPUConfig:
    """
    CPU-specific configuration for parsing
    
    Contains signal rules and other CPU-specific information
    needed for parsing BMC results.
    """
    
    # Default configurations for different CPUs
    DEFAULT_CONFIGS = {
        'nutshell': {
            'SIGNAL_RULES': {
                'r_data': {'hier': 'FormalTop.dut.mem.rdata_mem.helper_0', 'role': 'data'},
                'r_enable': {'hier': 'FormalTop.dut.mem.rdata_mem.helper_0', 'role': 'enable'},
                'r_index': {'hier': 'FormalTop.dut.mem.rdata_mem.helper_0', 'role': 'addr'}
            }
        },
        'rocket': {
            'SIGNAL_RULES': {
                'r_data': {'hier': 'FormalTop.dut.mem.srams.mem.helper_0', 'role': 'data'},
                'r_enable': {'hier': 'FormalTop.dut.mem.srams.mem.helper_0', 'role': 'enable'},
                'r_index': {'hier': 'FormalTop.dut.mem.srams.mem.helper_0', 'role': 'addr'}
            }
        },
        'boom': {
            'SIGNAL_RULES': {
                'r_data': {'hier': 'FormalTop.dut.mem.srams.mem.helper_0', 'role': 'data'},
                'r_enable': {'hier': 'FormalTop.dut.mem.srams.mem.helper_0', 'role': 'enable'},
                'r_index': {'hier': 'FormalTop.dut.mem.srams.mem.helper_0', 'role': 'addr'}
            }
        }
    }
    
    def __init__(self, cpu: str, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize CPU configuration
        
        Args:
            cpu: CPU type ("nutshell", "rocket", "boom", or custom name)
            custom_config: Optional custom configuration dictionary
        """
        self.cpu = cpu
        self.config = custom_config if custom_config else self.DEFAULT_CONFIGS.get(cpu, {})
        
        self.logger = BMCFuzzLogger.get_logger("CPUConfig")
        self.logger.debug(f"Initialized CPUConfig for {cpu}")
    
    @property
    def signal_rules(self) -> Dict[str, Dict[str, str]]:
        """Get signal rules for this CPU"""
        return self.config.get('SIGNAL_RULES', {})
    
    def get_signal_rule(self, signal_name: str) -> Optional[Dict[str, str]]:
        """
        Get rule for a specific signal
        
        Args:
            signal_name: Name of signal (e.g., 'r_data', 'r_enable')
        
        Returns:
            Dictionary with signal rule, or None if not found
        """
        return self.signal_rules.get(signal_name)
    
    def get_all_rules(self) -> Dict[str, Dict[str, str]]:
        """
        Get all signal rules
        
        Returns:
            Dictionary of all signal rules
        """
        return self.signal_rules


class SMTParser(ResultParser):
    """Parser for SMT mode results (parses VCD files)"""
    
    def __init__(self, cpu_config: Optional[CPUConfig] = None):
        """
        Initialize SMT parser
        
        Args:
            cpu_config: CPU configuration for parsing
        """
        self.cpu_config = cpu_config
        self.logger = BMCFuzzLogger.get_logger("SMTParser")
    
    def parse(self, cover_point: int, formal_run_dir: str) -> Optional[Dict[str, Any]]:
        """
        Parse SMT mode BMC result from VCD file
        
        Args:
            cover_point: Coverage point ID
            formal_run_dir: Directory containing BMC results
        
        Returns:
            Dictionary with parsed data
        """
        cover_dir = os.path.join(formal_run_dir, f"cover_{cover_point}")
        vcd_file = os.path.join(cover_dir, "engine_0", "trace0.vcd")
        
        if not os.path.exists(vcd_file):
            self.logger.warning(f"VCD file not found: {vcd_file}")
            return None
        
        # Get CPU-specific signal rules if available
        signal_rules = {}
        if self.cpu_config:
            signal_rules = self.cpu_config.get_all_rules()
            self.logger.debug(
                f"Using CPU config for SMT parsing: {len(signal_rules)} signal rules"
            )
        
        # Convert signal_rules to match format expected by Verilog_VCD
        # CPUConfig has format: {'signal_name': {'hier': '...', 'role': '...'}}
        # Need to convert to list format for matching
        signal_rule_list = []
        for signal_name, rule in signal_rules.items():
            signal_rule_list.append({
                'name': signal_name,
                'hier': rule['hier'],
                'role': rule['role']
            })
        
        # Parse VCD file
        try:
            from Verilog_VCD.Verilog_VCD import parse_vcd
            vcd_data = parse_vcd(vcd_file)
        except ImportError:
            self.logger.warning("Verilog_VCD not available, returning placeholder")
            return {
                'cover_point': cover_point,
                'mode': 'smt',
                'vcd_file': vcd_file,
                'status': 'covered',
                'cpu_config': self.cpu_config.cpu if self.cpu_config else None,
                'data': {}
            }
        
        # Extract signal values
        signal_values = {'enable': [], 'addr': {}, 'data': {}}
        
        for netinfo in vcd_data.values():
            for signal_rule in signal_rule_list:
                if (
                    'nets' in netinfo and len(netinfo['nets']) > 0 and
                    netinfo['nets'][0]['name'] == signal_rule['name'] and
                    netinfo['nets'][0]['hier'] == signal_rule['hier']
                ):
                    for time_sig in netinfo['tv']:
                        clock = time_sig[0]
                        value = time_sig[1]
                        
                        # self.logger.debug(
                        #     f"Matched signal {signal_rule['name']} at clock {clock}: value={value}"
                        # )
                        if signal_rule['role'] == 'enable':
                            signal_values['enable'].append((int(clock), value))
                        else:
                            signal_values[signal_rule['role']][int(clock)] = value
        
        # Sort enable signals by clock
        signal_values['enable'] = sorted(signal_values['enable'], key=lambda x: x[0])
        
        # Build memory map from enable signals
        memory_map = {}
        for index, (clock, value) in enumerate(signal_values['enable']):
            if value == '1' and index + 1 < len(signal_values['enable']):
                next_clock = signal_values['enable'][index + 1][0]
                addr = signal_values['addr'].get(clock)
                data = signal_values['data'].get(next_clock)
                
                # Parse address and data
                addr, data = self._data_parser(addr, data)
                if data == b'\x00' * 8:
                    self.logger.debug(
                        f"Skipping zero data at clock {clock}: addr={addr:#x}"
                    )
                    continue
                memory_map[addr] = data
                self.logger.debug(
                    f"At clock {clock}: addr={addr:#x}, data={data.hex()}"
                )
        
        # Build output directory
        output_dir = os.path.join(formal_run_dir, "corpus")
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, f"cover_{cover_point}.bin")
        
        # Build bin file
        self._bin_file_builder(memory_map, output_file_path)
        
        return {
            'cover_point': cover_point,
            'mode': 'smt',
            'vcd_file': vcd_file,
            'bin_file': output_file_path,
            'status': 'covered',
            'cpu_config': self.cpu_config.cpu if self.cpu_config else None,
            'data': {'memory_map': memory_map}
        }
    
    def _data_parser(self, addr: str, data: str) -> tuple:
        """
        Parse binary address and data
        
        Args:
            addr: Binary address string (e.g., '0b...')
            data: Binary data string (e.g., '0b...')
        
        Returns:
            Tuple of (address, data_bytes)
        """
        if addr and 'b' in addr:
            addr = addr.split("'b")[1]
        if data and 'b' in data:
            data = data.split("'b")[1]
        
        # Parse address: multiply by 8 to get byte address
        addr_int = int(addr, 2) * 8 if addr else 0
        data_int = int(data, 2) if data else 0
        
        return (addr_int, data_int.to_bytes(8, byteorder='little'))
    
    def _bin_file_builder(self, memory_map: Dict[int, bytes], output_file_path: str):
        """
        Build bin file from memory map
        
        Args:
            memory_map: Dictionary mapping addresses to data
            output_file_path: Path to output bin file
        """
        with open(output_file_path, 'wb') as output_file:
            current_addr = 0
            for addr in sorted(memory_map.keys()):
                if current_addr < addr:
                    # Fill gaps with zeros
                    gap_size = addr - current_addr
                    output_file.write(b'\x00' * gap_size)
                    current_addr = addr
                output_file.write(memory_map[addr])
                current_addr += 8
            if current_addr == 0:
                output_file.write(b'\x00' * 8)  # Write at least one zero entry if no data
        
        self.logger.debug(f"Generated bin file: {output_file_path}")


class SATParser(ResultParser):
    """Parser for SAT mode results (parses witness files)"""
    
    def __init__(self, cpu_config: Optional[CPUConfig] = None):
        """
        Initialize SAT parser
        
        Args:
            cpu_config: CPU configuration for parsing
        """
        self.cpu_config = cpu_config
        self.logger = BMCFuzzLogger.get_logger("SATParser")
    
    def parse(self, cover_point: int, formal_run_dir: str) -> Optional[Dict[str, Any]]:
        """
        Parse SAT mode BMC result from witness file
        
        Args:
            cover_point: Coverage point ID
            formal_run_dir: Directory containing BMC results
        
        Returns:
            Dictionary with parsed data
        """
        cover_dir = os.path.join(formal_run_dir, f"cover_{cover_point}")
        witness_file = os.path.join(cover_dir, "engine_0", "trace0_aiw.yw")
        
        if not os.path.exists(witness_file):
            self.logger.warning(f"Witness file not found: {witness_file}")
            return None
        
        # Build output directory
        output_dir = os.path.join(formal_run_dir, "corpus")
        os.makedirs(output_dir, exist_ok=True)
        witness_output_path = os.path.join(output_dir, f"cover_{cover_point}.witness")
        
        # Get OSS CAD Suite environment
        from core.config import Config
        oss_env = Config.OSS_CAD_SUITE_ENV
        
        # Use yosys-witness display to convert witness file
        display_command = f"source {oss_env} && yosys-witness display {witness_file} > {witness_output_path}"
        display_command = f"bash -c '{display_command}'"
        
        return_code = run_command(display_command, shell=True)
        if return_code != 0:
            self.logger.error(f"Failed to display witness file: return code {return_code}")
            return None
        
        # Parse the displayed witness file
        step_data = []
        try:
            with open(witness_output_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if "rand_value" in line:
                        # Extract binary value (last token)
                        bits = line.strip().split(" ")[-1]
                        step_data.append(bits)
        except Exception as e:
            self.logger.error(f"Failed to parse witness output: {e}")
            return None
        
        # Write processed witness file
        processed_witness_path = os.path.join(output_dir, f"cover_{cover_point}_processed.witness")
        with open(processed_witness_path, 'w') as f:
            steps = len(step_data)
            f.write(str(steps) + "\n")
            
            for step_idx, bits in enumerate(step_data, 1):
                # Parse bits to hex
                bits_int = int(bits, 2) if bits else 0
                hex_bits = f"{bits_int:#018x}"
                
                # Split into upper and lower 32 bits
                upper_32 = f"{int(bits[:32], 2):#010x}" if len(bits) >= 32 else "#0x00000000"
                lower_32 = f"{int(bits[32:], 2):#010x}" if len(bits) >= 64 else "#0x00000000"
                
                f.write(f"{hex_bits}\n")
                
                self.logger.debug(
                    f"Step {step_idx}: {lower_32} {upper_32}"
                )
        
        return {
            'cover_point': cover_point,
            'mode': 'sat',
            'witness_file': witness_file,
            'witness_output': witness_output_path,
            'steps': len(step_data),
            'status': 'covered',
            'cpu_config': self.cpu_config.cpu if self.cpu_config else None,
            'data': {'step_data': step_data}
        }


class SeedGenerator:
    """
    Seed generator for parsing BMC results
    
    Acts as a callback for formal executor to process
    BMC verification results and generate seeds for fuzzing.
    """
    
    def __init__(self):
        """Initialize SeedGenerator"""
        self.logger = BMCFuzzLogger.get_logger("SeedGenerator")
        self.project_name = None
        self.mode = None  # "smt" or "sat"
        
        # CPU configurations (users can register custom configs)
        self.cpu_configs: Dict[str, CPUConfig] = {}
        
        # Custom parsers (users can register their own parsers)
        self.custom_parsers: Dict[str, ResultParser] = {}
        
        self.logger.info("SeedGenerator initialized")
    
    def configure(self, project_name: str, mode: str):
        """
        Configure seed generator for specific project and mode

        Args:
            project_name: Project name ("nutshell", "rocket", "boom", or custom)
            mode: Solver mode ("smt" or "sat")
        """
        self.project_name = project_name
        self.mode = mode

        # Get or create CPU config
        if project_name not in self.cpu_configs:
            self.cpu_configs[project_name] = CPUConfig(project_name)

        self.logger.info(
            f"Configured for project_name={project_name}, mode={mode}"
        )
    
    def register_cpu_config(self, cpu: str, config: Dict[str, Any]):
        """
        Register a custom CPU configuration
        
        Args:
            cpu: CPU type identifier
            config: Configuration dictionary with SIGNAL_RULES and other settings
        """
        self.cpu_configs[cpu] = CPUConfig(cpu, custom_config=config)
        self.logger.info(f"Registered custom CPU config for: {cpu}")
    
    def register_custom_parser(self, name: str, parser: ResultParser):
        """
        Register a custom parser
        
        Args:
            name: Parser name/identifier
            parser: Parser instance implementing ResultParser
        """
        self.custom_parsers[name] = parser
        self.logger.info(f"Registered custom parser: {name}")
    
    def get_parser(self) -> ResultParser:
        """
        Get appropriate parser based on current configuration
        
        Returns:
            ResultParser instance
        """
        # Try custom parsers first
        if self.custom_parsers:
            for name, parser in self.custom_parsers.items():
                self.logger.debug(f"Using custom parser: {name}")
                return parser
        
        # Get CPU config
        cpu_config = self.cpu_configs.get(self.project_name)
        
        # Use default parser based on mode
        if self.mode == "smt":
            return SMTParser(cpu_config=cpu_config)
        elif self.mode == "sat":
            return SATParser(cpu_config=cpu_config)
        else:
            self.logger.warning(
                f"Unknown mode: {self.mode}, using SMT parser as default"
            )
            return SMTParser(cpu_config=cpu_config)
    
    def parse_result(self, cover_point: int, formal_run_dir: str) -> Optional[Dict[str, Any]]:
        """
        Parse BMC result for a coverage point
        
        This is callback method used by FormalExecutor.
        
        Args:
            cover_point: Coverage point ID
            formal_run_dir: Directory containing BMC results
        
        Returns:
            Dictionary with parsed data, or None if parsing failed
        """
        parser = self.get_parser()
        
        try:
            result = parser.parse(cover_point, formal_run_dir)
            
            if result:
                self.logger.debug(
                    f"Parsed result for cover_point {cover_point}: {result.get('status')}"
                )
            else:
                self.logger.warning(
                    f"Failed to parse result for cover_point {cover_point}"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Error parsing result for cover_point {cover_point}: {e}"
            )
            return None
    
    def __call__(self, cover_point: int, formal_run_dir: str):
        """
        Callable interface for use as callback
        
        Args:
            cover_point: Coverage point ID
            formal_run_dir: Directory containing BMC results
        """
        return self.parse_result(cover_point, formal_run_dir)
    
"""
VCD Parser for parsing waveform files

This module provides functionality to parse VCD (Value Change Dump) files
and convert them to JSON format for initialization purposes.

The parser is designed to be extensible for any Verilog module, not just
specific CPU implementations.
"""

import json
import re
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from abc import ABC, abstractmethod

try:
    from Verilog_VCD.Verilog_VCD import parse_vcd
except ImportError:
    parse_vcd = None

from utils.logger import BMCFuzzLogger


class SignalFilter(ABC):
    """
    Abstract base class for signal filtering
    
    Allows customization of signal value processing for different
    Verilog modules.
    """
    
    @abstractmethod
    def should_filter(self, signal_name: str, signal_value: str) -> bool:
        """
        Check if a signal should be filtered
        
        Args:
            signal_name: Full hierarchical signal name
            signal_value: Current signal value
        
        Returns:
            True if signal should be filtered (not included in output)
        """
        pass
    
    @abstractmethod
    def transform_value(self, signal_name: str, signal_value: str) -> str:
        """
        Transform signal value if needed
        
        Args:
            signal_name: Full hierarchical signal name
            signal_value: Current signal value
        
        Returns:
            Transformed signal value
        """
        return signal_value


class DefaultSignalFilter(SignalFilter):
    """
    Default signal filter - no filtering or transformation
    """
    
    def should_filter(self, signal_name: str, signal_value: str) -> bool:
        """No filtering by default"""
        return False
    
    def transform_value(self, signal_name: str, signal_value: str) -> str:
        """No transformation by default"""
        return signal_value


class CPUSignalFilter(SignalFilter):
    """
    CPU-specific signal filter for known CPU implementations
    
    Handles special cases for cache tags, TLB entries, etc.
    """
    
    def __init__(self, project_name: str = 'nutshell'):
        """
        Initialize CPU signal filter
        
        Args:
            project_name: CPU type (nutshell, rocket, boom)
        """
        self.project_name = project_name
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for signal filtering"""
        if self.project_name == "nutshell":
            self.cache_tag_pattern = re.compile(r"cache\.metaArray\.ram\..*ram")
            self.tlb_tag_pattern = re.compile(r"tlb\.mdTLB\.tlbmd_\d+\[\d+\]")
        elif self.project_name == "rocket":
            self.cache_tag_pattern = re.compile(r"cache\.tag_array_\d+\[\d+\]")
            self.tlb_tag_pattern = re.compile(r"ptw\.tags|tag_vpn")
        elif self.project_name == "boom":
            self.cache_tag_pattern = re.compile(
                r"icache\.tag_array_0\[\d+\]\[\d+:\d+\]|"
                r"dcache\.meta_\d+\.tag_array_\d+\[\d+\]\[\d+:\d+\]"
            )
            self.tlb_tag_pattern = re.compile(
                r"tag_vpn|dtlb.*entry_tag\[\d+:\d+\]|"
                r"dtlb.*entries_\d+_tag\[\d+:\d+\]"
            )
        else:
            self.cache_tag_pattern = None
            self.tlb_tag_pattern = None
    
    def should_filter(self, signal_name: str, signal_value: str) -> bool:
        """No filtering by default for CPU"""
        return False
    
    def transform_value(self, signal_name: str, signal_value: str) -> str:
        """
        Transform special signal values for CPU
        
        Sets cache tags and TLB tags to 0 to avoid state pollution.
        """
        # Set cache tags and TLB tags to 0
        if self.cache_tag_pattern and self.cache_tag_pattern.search(signal_name):
            return '0'
        
        if self.tlb_tag_pattern and self.tlb_tag_pattern.search(signal_name):
            return '0'
        
        return signal_value


class RegexSignalFilter(SignalFilter):
    """
    Regex-based signal filter for custom filtering rules
    
    Allows users to specify custom filtering and transformation rules
    using regular expressions.
    """
    
    def __init__(
        self,
        filter_patterns: Optional[List[str]] = None,
        transform_rules: Optional[Dict[str, str]] = None
    ):
        """
        Initialize regex signal filter
        
        Args:
            filter_patterns: List of regex patterns for signals to filter out
            transform_rules: Dict of {pattern: replacement} for value transformation
        """
        self.filter_patterns = [
            re.compile(p) for p in (filter_patterns or [])
        ]
        self.transform_rules = []
        for pattern, replacement in (transform_rules or {}).items():
            self.transform_rules.append((
                re.compile(pattern),
                replacement
            ))
    
    def should_filter(self, signal_name: str, signal_value: str) -> bool:
        """Check if signal matches any filter pattern"""
        return any(pattern.search(signal_name) for pattern in self.filter_patterns)
    
    def transform_value(self, signal_name: str, signal_value: str) -> str:
        """Apply transformation rules"""
        for pattern, replacement in self.transform_rules:
            if pattern.search(signal_name):
                return replacement
        return signal_value


class VCDParser:
    """
    VCD file parser
    
    Parses VCD files and extracts signal values at specific timestamps.
    Used for loading snapshot values into RTL code.
    
    Supports arbitrary Verilog modules through pluggable signal filters.
    """
    
    def __init__(
        self,
        signal_filter: Optional[SignalFilter] = None,
        signal_name_filter: Optional[Callable[[str], bool]] = None
    ):
        """
        Initialize VCD parser
        
        Args:
            signal_filter: Custom signal filter (default: DefaultSignalFilter)
            signal_name_filter: Optional function to filter signals by name
                                Returns True to include signal, False to exclude
        """
        self.signal_filter = signal_filter or DefaultSignalFilter()
        self.signal_name_filter = signal_name_filter
        self.logger = BMCFuzzLogger.get_logger("VCDParser")
    
    @classmethod
    def for_cpu(cls, project_name: str = 'nutshell') -> 'VCDParser':
        """
        Create VCD parser for known CPU type
        
        Args:
            project_name: CPU type (nutshell, rocket, boom)
        
        Returns:
            VCDParser configured with CPU-specific signal filter
        """
        return cls(signal_filter=CPUSignalFilter(project_name))
    
    @classmethod
    def for_regex_filter(
        cls,
        filter_patterns: List[str],
        transform_rules: Optional[Dict[str, str]] = None
    ) -> 'VCDParser':
        """
        Create VCD parser with regex-based filtering
        
        Args:
            filter_patterns: List of regex patterns to filter out
            transform_rules: Dict of {pattern: replacement} for value transformation
        
        Returns:
            VCDParser configured with regex signal filter
        """
        return cls(signal_filter=RegexSignalFilter(filter_patterns, transform_rules))
    
    def _convert_net_to_custom_format(
        self,
        netinfo: Dict[str, Any],
        net_id: int,
        net: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Convert net info to custom format
        
        Args:
            netinfo: Net info dictionary
            net_id: Net ID
            net: Net dictionary
        
        Returns:
            Custom formatted net info or None if should be filtered
        """
        hier = net['hier']
        name = net['name']
        size = int(net['size'])
        
        # Get last value
        if not netinfo['tv']:
            return None
        
        last_time_value = netinfo['tv'][-1]
        last_value = last_time_value[1]
        
        full_name = f"{hier}.{name}"
        
        # Apply signal name filter if provided
        if self.signal_name_filter and not self.signal_name_filter(full_name):
            return None
        
        # Apply signal filter transformation
        transformed_value = self.signal_filter.transform_value(
            full_name, last_value
        )
        
        # Check if signal should be filtered
        if self.signal_filter.should_filter(full_name, transformed_value):
            return None
        
        return {
            "id": net_id,
            "name": full_name,
            "value": f"{size}'b{transformed_value}",
            "width": size
        }
    
    def parse_vcd_to_json(
        self,
        vcd_path: str,
        output_json_path: str
    ) -> bool:
        """
        Parse VCD file and convert to JSON
        
        Args:
            vcd_path: Path to VCD file
            output_json_path: Path to output JSON file
        
        Returns:
            True if successful, False otherwise
        """
        if parse_vcd is None:
            self.logger.error("Verilog_VCD module not available")
            return False
        
        try:
            # Parse VCD file
            vcd_data = parse_vcd(vcd_path)
            
            net_id = 1
            custom_outputs = []
            
            for netinfo in vcd_data.values():
                for net in netinfo['nets']:
                    custom_output = self._convert_net_to_custom_format(
                        netinfo, net_id, net
                    )
                    if custom_output:
                        custom_outputs.append(custom_output)
                        net_id += 1
            
            # Write to JSON
            json_output = json.dumps(custom_outputs, indent=4)
            
            with open(output_json_path, 'w') as f:
                f.write(json_output)
            
            self.logger.info(
                f"Parsed VCD {vcd_path} to {output_json_path} "
                f"({len(custom_outputs)} signals)"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Error parsing VCD {vcd_path}: {e}")
            return False
    
    def normalize_signal_name(self, name: str) -> str:
        """
        Normalize signal name by removing bit ranges and prefixes
        
        Args:
            name: Signal name
        
        Returns:
            Normalized signal name
        """
        # Remove bit range
        normalized = re.sub(r'\[\d+:\d+\]', '', name)
        # Remove TOP. prefix (once)
        normalized = normalized.replace('TOP.', '', 1)
        return normalized.strip()


def parse_vcd_file(
    vcd_path: str,
    output_json_path: str,
    project_name: Optional[str] = None,
    signal_filter: Optional[SignalFilter] = None,
    signal_name_filter: Optional[Callable[[str], bool]] = None
) -> bool:
    """
    Convenience function to parse VCD file
    
    Args:
        vcd_path: Path to VCD file
        output_json_path: Path to output JSON file
        project_name: CPU type for CPU-specific filtering (nutshell, rocket, boom)
        signal_filter: Custom signal filter (takes precedence over project_name)
        signal_name_filter: Optional function to filter signals by name
    
    Returns:
        True if successful, False otherwise
    """
    # Create parser with appropriate filter
    if signal_filter:
        parser = VCDParser(signal_filter=signal_filter, signal_name_filter=signal_name_filter)
    elif project_name:
        parser = VCDParser.for_cpu(project_name)
    else:
        parser = VCDParser(signal_name_filter=signal_name_filter)
    
    return parser.parse_vcd_to_json(vcd_path, output_json_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print(f"Usage: python vcd_parser.py <vcd_path> <output_json_path> [project_name]")
        print(f"")
        print(f"Examples:")
        print(f"  # Parse for any Verilog module (default)")
        print(f"  python vcd_parser.py input.vcd output.json")
        print(f"")
        print(f"  # Parse for specific CPU type")
        print(f"  python vcd_parser.py input.vcd output.json nutshell")
        print(f"  python vcd_parser.py input.vcd output.json rocket")
        print(f"  python vcd_parser.py input.vcd output.json boom")
        sys.exit(1)
    
    vcd_path = sys.argv[1]
    output_json_path = sys.argv[2]
    project_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = parse_vcd_file(vcd_path, output_json_path, project_name=project_name)
    
    if success:
        print(f"Successfully parsed {vcd_path} to {output_json_path}")
        sys.exit(0)
    else:
        print(f"Failed to parse {vcd_path}")
        sys.exit(1)
"""
Wave Parser for parsing waveform files (VCD and FST)

This module provides functionality to parse VCD (Value Change Dump) and
FST (Fast Signal Trace) waveform files, converting them to JSON format
for initialization purposes.

FST files are supported via two strategies:
  1. Native parsing (if a Python FST library is available)
  2. Conversion to VCD using GTKWave's ``fst2vcd`` utility, then
     parsing the resulting VCD

The parser is designed to be extensible for any Verilog module.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from abc import ABC, abstractmethod

try:
    from Verilog_VCD.Verilog_VCD import parse_vcd
except ImportError:
    parse_vcd = None

from core.config import Config
from utils.logger import BMCFuzzLogger


# =========================================================================
# Signal Filters
# =========================================================================

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
        return False

    def transform_value(self, signal_name: str, signal_value: str) -> str:
        return signal_value


class CPUSignalFilter(SignalFilter):
    """
    CPU-specific signal filter for known CPU implementations

    Handles special cases for cache tags, TLB entries, etc.
    """

    def __init__(self, project_name: str = 'nutshell'):
        self.project_name = project_name
        self._compile_patterns()

    def _compile_patterns(self):
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
        return False

    def transform_value(self, signal_name: str, signal_value: str) -> str:
        """Sets cache tags and TLB tags to 0 to avoid state pollution."""
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
        return any(pattern.search(signal_name) for pattern in self.filter_patterns)

    def transform_value(self, signal_name: str, signal_value: str) -> str:
        for pattern, replacement in self.transform_rules:
            if pattern.search(signal_name):
                return replacement
        return signal_value


# =========================================================================
# Wave Parser
# =========================================================================

class WaveParser:
    """
    Waveform file parser supporting VCD and FST formats.

    Parses waveform files and extracts signal values at specific timestamps.
    Used for loading snapshot values into RTL code.

    Supports arbitrary Verilog modules through pluggable signal filters.

    FST support works by converting to VCD via GTKWave's ``fst2vcd``
    utility, then parsing the intermediate VCD.
    """

    SUPPORTED_EXTENSIONS = {'.vcd', '.fst'}

    def __init__(
        self,
        signal_filter: Optional[SignalFilter] = None,
        signal_name_filter: Optional[Callable[[str], bool]] = None
    ):
        self.signal_filter = signal_filter or DefaultSignalFilter()
        self.signal_name_filter = signal_name_filter
        self.logger = BMCFuzzLogger.get_logger("WaveParser")

    # ── Factory methods ──────────────────────────────────────────────

    @classmethod
    def for_cpu(cls, project_name: str = 'nutshell') -> 'WaveParser':
        return cls(signal_filter=CPUSignalFilter(project_name))

    @classmethod
    def for_regex_filter(
        cls,
        filter_patterns: List[str],
        transform_rules: Optional[Dict[str, str]] = None
    ) -> 'WaveParser':
        return cls(signal_filter=RegexSignalFilter(filter_patterns, transform_rules))

    # ── Public API ───────────────────────────────────────────────────

    def parse_to_json(
        self,
        wave_path: str,
        output_json_path: str
    ) -> bool:
        """
        Parse a waveform file (VCD or FST) and convert to JSON.

        The format is auto-detected from the file extension.

        Args:
            wave_path:        Path to VCD or FST file
            output_json_path: Path to output JSON file

        Returns:
            True if successful, False otherwise
        """
        ext = Path(wave_path).suffix.lower()

        if ext == '.fst':
            return self._parse_fst_to_json(wave_path, output_json_path)
        elif ext == '.vcd':
            return self._parse_vcd_to_json(wave_path, output_json_path)
        else:
            self.logger.error(
                f"Unsupported waveform format '{ext}'. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )
            return False

    # backward-compat alias
    def parse_vcd_to_json(self, vcd_path: str, output_json_path: str) -> bool:
        """Backward-compatible alias for :meth:`parse_to_json`."""
        return self.parse_to_json(vcd_path, output_json_path)

    def normalize_signal_name(self, name: str) -> str:
        """
        Normalize signal name by removing bit ranges and prefixes.
        """
        normalized = re.sub(r'\[\d+:\d+\]', '', name)
        normalized = normalized.replace('TOP.', '', 1)
        return normalized.strip()

    # ── VCD parsing ──────────────────────────────────────────────────

    def _parse_vcd_to_json(
        self,
        vcd_path: str,
        output_json_path: str
    ) -> bool:
        if parse_vcd is None:
            self.logger.error(
                "Verilog_VCD module not available. "
                "Install with: pip install Verilog_VCD"
            )
            return False

        try:
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

            json_output = json.dumps(custom_outputs, indent=4)
            with open(output_json_path, 'w') as f:
                f.write(json_output)

            self.logger.info(
                f"Parsed VCD {vcd_path} -> {output_json_path} "
                f"({len(custom_outputs)} signals)"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error parsing VCD {vcd_path}: {e}")
            return False

    # ── FST parsing ──────────────────────────────────────────────────

    @staticmethod
    def _find_fst2vcd() -> Optional[str]:
        """Locate the ``fst2vcd`` utility on PATH."""
        return shutil.which("fst2vcd")

    def _parse_fst_to_json(
        self,
        fst_path: str,
        output_json_path: str
    ) -> bool:
        """
        Parse an FST file by converting to VCD first, then parsing.

        Uses GTKWave's ``fst2vcd`` to perform the conversion.
        """
        fst2vcd = self._find_fst2vcd()
        if fst2vcd is None:
            self.logger.error(
                "fst2vcd not found on PATH. "
                "Install GTKWave to get the fst2vcd utility."
            )
            return False

        tmp_vcd_path = os.path.join(Config.SNAPSHOT_DIR, "fst_conv_tmp.vcd")
        try:
            self.logger.info(
                f"Converting FST -> VCD: {fst_path} -> {tmp_vcd_path}"
            )

            result = subprocess.run(
                [fst2vcd, fst_path, "-o", tmp_vcd_path],
                capture_output=True, text=True, timeout=600
            )

            if result.returncode != 0:
                self.logger.error(
                    f"fst2vcd failed (rc={result.returncode}): "
                    f"{result.stderr.strip()}"
                )
                return False

            return self._parse_vcd_to_json(tmp_vcd_path, output_json_path)

        except subprocess.TimeoutExpired:
            self.logger.error(
                f"fst2vcd timed out converting {fst_path}"
            )
            return False
        except Exception as e:
            self.logger.error(f"Error converting FST {fst_path}: {e}")
            return False
        finally:
            if tmp_vcd_path and os.path.exists(tmp_vcd_path):
                try:
                    os.unlink(tmp_vcd_path)
                except OSError:
                    pass

    # ── Internal helpers ─────────────────────────────────────────────

    def _convert_net_to_custom_format(
        self,
        netinfo: Dict[str, Any],
        net_id: int,
        net: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        hier = net['hier']
        name = net['name']
        size = int(net['size'])

        if not netinfo['tv']:
            return None

        last_time_value = netinfo['tv'][-1]
        last_value = last_time_value[1]

        full_name = f"{hier}.{name}"

        if self.signal_name_filter and not self.signal_name_filter(full_name):
            return None

        transformed_value = self.signal_filter.transform_value(
            full_name, last_value
        )

        if self.signal_filter.should_filter(full_name, transformed_value):
            return None

        return {
            "id": net_id,
            "name": full_name,
            "value": f"{size}'b{transformed_value}",
            "width": size
        }


# backward-compat alias
VCDParser = WaveParser


# =========================================================================
# Convenience functions
# =========================================================================

def parse_wave_file(
    wave_path: str,
    output_json_path: str,
    project_name: Optional[str] = None,
    signal_filter: Optional[SignalFilter] = None,
    signal_name_filter: Optional[Callable[[str], bool]] = None
) -> bool:
    """
    Convenience function to parse a waveform file (VCD or FST).

    Args:
        wave_path:          Path to VCD or FST file
        output_json_path:   Path to output JSON file
        project_name:       CPU type for CPU-specific filtering
        signal_filter:      Custom signal filter (takes precedence over project_name)
        signal_name_filter: Optional function to filter signals by name

    Returns:
        True if successful, False otherwise
    """
    if signal_filter:
        parser = WaveParser(signal_filter=signal_filter, signal_name_filter=signal_name_filter)
    elif project_name:
        parser = WaveParser.for_cpu(project_name)
    else:
        parser = WaveParser(signal_name_filter=signal_name_filter)

    return parser.parse_to_json(wave_path, output_json_path)


# backward-compat alias
parse_vcd_file = parse_wave_file


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print(f"Usage: python wave_parser.py <wave_path> <output_json_path> [project_name]")
        print()
        print("Supported formats: .vcd, .fst")
        print()
        print("Examples:")
        print(f"  python wave_parser.py input.vcd output.json")
        print(f"  python wave_parser.py input.fst output.json")
        print(f"  python wave_parser.py input.vcd output.json rocket")
        sys.exit(1)

    wave_path = sys.argv[1]
    output_json_path = sys.argv[2]
    project_name = sys.argv[3] if len(sys.argv) > 3 else None

    success = parse_wave_file(wave_path, output_json_path, project_name=project_name)

    if success:
        print(f"Successfully parsed {wave_path} to {output_json_path}")
        sys.exit(0)
    else:
        print(f"Failed to parse {wave_path}")
        sys.exit(1)

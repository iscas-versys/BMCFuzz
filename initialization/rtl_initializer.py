"""
RTL Initializer

Two-step pipeline for injecting snapshot state into Verilog sources:

  Step 1 – merge_vcd_into_hierarchy
      Input : hierarchy JSON (from hierarchy_parser) + VCD JSON
      Output: flat register dict {reg_path: {regname, initval, module_name}}
              with initval fields filled from the VCD snapshot.

  Step 2 – insert_initial_blocks
      Input : Verilog source file + the flat register dict from step 1
      Output: Verilog source with 'initial begin … end' blocks injected
              before each module's endmodule keyword.
"""

import json
import re
from pathlib import Path
from typing import Dict, List

from utils.logger import BMCFuzzLogger

# Same module-boundary pattern used by hierarchy_parser
_MODULE_RE = re.compile(r'\bmodule\s+(\w+)\b.*?\bendmodule\b', re.DOTALL)


class RTLInitializer:
    """Injects VCD snapshot values into SystemVerilog source files."""

    def __init__(self):
        self.logger = BMCFuzzLogger.get_logger("RTLInitializer")

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    def merge_vcd_into_hierarchy(
        self,
        hierarchy_json_path: str,
        vcd_json_path: str,
        output_json_path: str
    ) -> bool:
        """
        Overlay VCD snapshot values onto the hierarchy register map.

        Args:
            hierarchy_json_path: JSON produced by hierarchy_parser.generate()
            vcd_json_path:       List of {name, value} signal records from VCD
            output_json_path:    Flat dict {reg_path: {regname, initval, module_name}}

        Returns:
            True on success.
        """
        try:
            with open(hierarchy_json_path, 'r') as f:
                hierarchy = json.load(f)
            with open(vcd_json_path, 'r') as f:
                vcd_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading input files: {e}")
            return False

        # Build normalised VCD lookup: {normalised_signal_name: value}
        vcd_lookup = {
            self._normalise(sig['name']): sig['value']
            for sig in vcd_data
        }

        # Collect all register paths from hierarchy
        from initialization.hierarchy_parser import HierarchyParser
        reg_paths = HierarchyParser().find_registers(hierarchy)

        # Match and update initval from VCD
        unmatched = []
        for path, info in reg_paths.items():
            if self._normalise(path) in vcd_lookup:
                info['initval'] = vcd_lookup[self._normalise(path)]
            else:
                unmatched.append(path)

        if unmatched:
            self.logger.warning(f"{len(unmatched)} register(s) not matched in VCD")
            self.logger.warning(f"Unmatched registers: {unmatched}")

        try:
            with open(output_json_path, 'w') as f:
                json.dump(reg_paths, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Merged VCD into hierarchy: {output_json_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error writing {output_json_path}: {e}")
            return False

    def insert_initial_blocks(
        self,
        sv_file_path: str,
        register_json_path: str,
        output_sv_path: str
    ) -> bool:
        """
        Insert 'initial begin … end' into every module of a Verilog file.

        Args:
            sv_file_path:       Verilog source (single or multi-module file)
            register_json_path: Flat register dict from merge_vcd_into_hierarchy
            output_sv_path:     Output Verilog file with initial blocks injected

        Only registers whose initval is not 'None' are emitted.
        Returns True on success.
        """
        try:
            content = Path(sv_file_path).read_text()
        except Exception as e:
            self.logger.error(f"Error reading {sv_file_path}: {e}")
            return False

        init_map = self._build_init_map(register_json_path)
        result   = self._inject_initial_blocks(content, init_map)

        try:
            Path(output_sv_path).write_text(result)
            self.logger.info(f"Inserted initial blocks: {output_sv_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error writing {output_sv_path}: {e}")
            return False

    def update_mem_rw_helper(
        self,
        vcd_json_path: str,
        src_file_path: str,
        output_file_path: str
    ) -> bool:
        """
        Update the r_data initial value in a MemRWHelper Verilog file.

        Locates the 'helper_0.r_data[63:0]' signal in the VCD JSON and
        replaces the assignment inside the opening 'initial begin … end' block:

            initial begin
                r_data = 64'h0;   ← replaced with the VCD value
            end

        Args:
            vcd_json_path:    VCD signal JSON [{name, value}, ...]
            src_file_path:    Source MemRWHelper Verilog file
            output_file_path: Output file with updated r_data value

        Returns:
            True on success.
        """
        try:
            with open(vcd_json_path, 'r') as f:
                vcd_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading {vcd_json_path}: {e}")
            return False

        r_data_value = next(
            (sig['value'] for sig in vcd_data
             if sig['name'].endswith('helper_0.r_data[63:0]')),
            None
        )
        if r_data_value is None:
            self.logger.warning("helper_0.r_data[63:0] not found in VCD")
            return False

        try:
            content = Path(src_file_path).read_text()
        except Exception as e:
            self.logger.error(f"Error reading {src_file_path}: {e}")
            return False

        # Replace only the first occurrence: initial begin\n    r_data = ...;
        new_content, n = re.subn(
            r'(initial\s+begin\s+r_data\s*=\s*)[^;]+(;)',
            rf'\g<1>{r_data_value}\2',
            content,
            count=1,
            flags=re.DOTALL
        )
        if n == 0:
            self.logger.warning(f"No r_data assignment found in {src_file_path}")
            return False

        try:
            Path(output_file_path).write_text(new_content)
            self.logger.info(
                f"Updated MemRWHelper r_data = {r_data_value}: {output_file_path}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error writing {output_file_path}: {e}")
            return False

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _normalise(name: str) -> str:
        """Strip bit-range suffixes and leading 'TOP.' from a signal name."""
        name = re.sub(r'\[\d+:\d+\]', '', name)
        name = re.sub(r'^TOP\.', '', name)
        return name.strip()

    def _build_init_map(
        self, register_json_path: str
    ) -> Dict[str, List[str]]:
        """
        Build {module_name: ["    reg = value;", ...]} from the flat register JSON.
        Skips entries whose initval is 'None'.
        """
        try:
            with open(register_json_path, 'r') as f:
                reg_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading {register_json_path}: {e}")
            return {}

        init_map: Dict[str, List[str]] = {}
        for info in reg_data.values():
            initval = info.get('initval', 'None')
            if initval == 'None':
                continue
            mod     = info.get('module_name', 'Unknown')
            regname = re.sub(r'\[\d+:\d+\]', '', info.get('regname', '')).strip()
            init_map.setdefault(mod, []).append(f"    {regname} = {initval};")

        return init_map

    def _inject_initial_blocks(
        self, content: str, init_map: Dict[str, List[str]]
    ) -> str:
        """
        For each module block in content whose name appears in init_map,
        insert an 'initial begin … end' block immediately before endmodule.
        """
        def replace_module(m: re.Match) -> str:
            mod_name = m.group(1)
            body     = m.group(0)
            stmts    = init_map.get(mod_name)
            if not stmts:
                return body
            initial_block = "initial begin\n" + "\n".join(stmts) + "\nend\n"
            insert_at = body.rfind('endmodule')
            return body[:insert_at] + initial_block + body[insert_at:]

        return _MODULE_RE.sub(replace_module, content)


# =============================================================================
# Public function interface
# =============================================================================

def merge_vcd_into_hierarchy(
    hierarchy_json_path: str,
    vcd_json_path: str,
    output_json_path: str
) -> bool:
    """
    Overlay VCD snapshot values onto a hierarchy register map.

    Args:
        hierarchy_json_path: JSON from hierarchy_parser.generate()
        vcd_json_path:       [{name, value}, ...] signal records from VCD
        output_json_path:    Output flat register dict with updated initvals

    Returns:
        True on success.
    """
    return RTLInitializer().merge_vcd_into_hierarchy(
        hierarchy_json_path, vcd_json_path, output_json_path
    )


def insert_initial_blocks(
    sv_file_path: str,
    register_json_path: str,
    output_sv_path: str
) -> bool:
    """
    Insert 'initial begin … end' blocks into a Verilog file.

    Args:
        sv_file_path:       Verilog source (single or multi-module)
        register_json_path: Flat register dict from merge_vcd_into_hierarchy
        output_sv_path:     Output Verilog with initial blocks injected

    Returns:
        True on success.
    """
    return RTLInitializer().insert_initial_blocks(
        sv_file_path, register_json_path, output_sv_path
    )


def update_mem_rw_helper(
    vcd_json_path: str,
    src_file_path: str,
    output_file_path: str
) -> bool:
    """
    Update the r_data initial value in a MemRWHelper Verilog file.

    Args:
        vcd_json_path:    VCD signal JSON [{name, value}, ...]
        src_file_path:    Source MemRWHelper Verilog file
        output_file_path: Output file with updated r_data value

    Returns:
        True on success.
    """
    return RTLInitializer().update_mem_rw_helper(
        vcd_json_path, src_file_path, output_file_path
    )


__all__ = [
    'RTLInitializer',
    'merge_vcd_into_hierarchy',
    'insert_initial_blocks',
    'update_mem_rw_helper',
]

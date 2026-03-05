"""
Hierarchy Parser for Verilog module hierarchy

Parse Verilog module hierarchy from a single SystemVerilog file and generate
JSON with register information.  No extra per-module source files are needed.
"""

import json
import re
import os
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path

from utils.logger import BMCFuzzLogger
from utils.command import run_command

# Matches a complete module block: module Name ... endmodule
_MODULE_RE = re.compile(r'\bmodule\s+(\w+)\b.*?\bendmodule\b', re.DOTALL)

# Matches a scalar reg declaration: reg [W:0] name = init;  or  reg name;
_REG_SCALAR_RE = re.compile(
    r'\breg\b\s*(\[\d+:\d+\]\s*)?([a-zA-Z_]\w*)\s*(?:=\s*(.*?))?\s*;',
    re.DOTALL
)

# Matches an array reg declaration: reg [W:0] name [N:0];
_REG_ARRAY_RE = re.compile(
    r'\breg\b\s*(\[\d+:\d+\])?\s+(\w+)\s*\[(\d+):(\d+)\]\s*;',
    re.DOTALL
)


class HierarchyParser:
    """Verilog hierarchy parser - extracts module hierarchy and register info"""

    def __init__(self):
        self.logger = BMCFuzzLogger.get_logger("HierarchyParser")
        self.hierarchy_data = None

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    def load_hierarchy(self, json_file_path: str) -> bool:
        """Load hierarchy from JSON file"""
        try:
            with open(json_file_path, 'r') as f:
                self.hierarchy_data = json.load(f)
            self.logger.info(f"Loaded hierarchy from {json_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error loading hierarchy {json_file_path}: {e}")
            return False

    def find_registers(
        self,
        hierarchy: Optional[Dict[str, Any]] = None,
        path: str = "SimTop"
    ) -> Dict[str, Dict[str, Any]]:
        """Recursively find all registers in hierarchy"""
        if hierarchy is None:
            hierarchy = self.hierarchy_data
        if not hierarchy:
            return {}

        reg_paths = {}
        mod_name = hierarchy.get('mod_name', 'Unknown')

        for reg in hierarchy.get('reg_list', []):
            reg_name = reg.get('regname', '')
            base_name = re.sub(r'\[\d+:\d+\]', '', reg_name).strip()
            reg_paths[f"{path}.{base_name}"] = {
                'regname': reg_name,
                'initval': reg.get('initval', 'None'),
                'module_name': mod_name
            }

        for inst in hierarchy.get('insts', []):
            reg_paths.update(self.find_registers(inst, f"{path}.{inst['inst_name']}"))

        for child in hierarchy.get('children', []):
            reg_paths.update(self.find_registers(child, f"{path}.{child['inst_name']}"))

        return reg_paths

    def generate(
        self,
        sv_top_file: str,
        output_json_path: str,
        inc_dirs: Optional[List[str]] = None,
        define_macros: Optional[List[str]] = None,
        keep_temp: bool = True
    ) -> bool:
        """
        Parse a single Verilog file and generate JSON with module hierarchy
        and register info.  All register data is extracted from sv_top_file
        itself — no additional per-module source files are needed.
        The top module is auto-detected as the one that is never instantiated.
        """
        from core.config import BMCFUZZ_HOME

        sv_top = Path(sv_top_file)
        if not sv_top.exists():
            self.logger.error(f"Top-level SV file not found: {sv_top_file}")
            return False

        temp_yaml = Path(BMCFUZZ_HOME) / "tmp" / f"{sv_top.stem}.yaml"
        temp_yaml.parent.mkdir(exist_ok=True)

        try:
            # Step 1: parse module instantiation hierarchy via svinst
            self.logger.info(f"Step 1: Running svinst on {sv_top_file}")
            if not self._run_svinst(sv_top_file, str(temp_yaml), inc_dirs, define_macros):
                return False

            # Step 2: convert YAML to hierarchy dict (top module auto-detected)
            self.logger.info(f"Step 2: Building hierarchy from {temp_yaml}")
            hierarchy = self._yaml_to_hierarchy(str(temp_yaml))
            if not hierarchy:
                return False

            # Step 3: parse all module registers from the single source file
            self.logger.info(f"Step 3: Parsing registers from {sv_top_file}")
            reg_map = self._parse_all_registers(sv_top_file)
            self._attach_registers(hierarchy, reg_map)

            with open(output_json_path, 'w') as f:
                json.dump(hierarchy, f, indent=4)

            self.logger.info(f"Generated hierarchy: {output_json_path}")
            return True
        finally:
            if not keep_temp and temp_yaml.exists():
                temp_yaml.unlink()

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _run_svinst(
        self,
        sv_file_path: str,
        yaml_output_path: str,
        inc_dirs: Optional[List[str]] = None,
        define_macros: Optional[List[str]] = None
    ) -> bool:
        """Run svinst to generate YAML hierarchy"""
        svinst_path = os.path.join(os.path.dirname(__file__), "bin", "svinst")
        if not os.path.exists(svinst_path):
            self.logger.error(f"svinst not found at {svinst_path}")
            return False

        cmd = f"{svinst_path} {sv_file_path}"
        for d in (inc_dirs or []):
            cmd += f" -I {d}"
        for m in (define_macros or []):
            cmd += f" -D {m}"
        cmd += f" > {yaml_output_path}"

        if run_command(cmd, shell=True) == 0:
            return True
        self.logger.error(f"svinst failed: {cmd}")
        return False

    def _yaml_to_hierarchy(self, yaml_file_path: str) -> Optional[Dict[str, Any]]:
        """Parse svinst YAML output and build a hierarchy dict. Top module is the one never instantiated."""
        try:
            with open(yaml_file_path, 'r') as f:
                data = yaml.safe_load(f)

            all_modules = []
            for file in data.get('files', []):
                all_modules.extend(file.get('defs', []))
                self.logger.debug(f"Found {len(file.get('defs', []))} modules in {file.get('file_name', 'unknown file')}")

            module_map = {m['mod_name']: m for m in all_modules if 'mod_name' in m}
            instantiated = set()
            for m in all_modules:
                for inst in (m.get('insts') or []):
                    instantiated.add(inst.get('mod_name'))
            top_candidates = [name for name in module_map if name not in instantiated]
            if not top_candidates:
                self.logger.error("No top module found (every module is instantiated elsewhere)")
                return None
            top_module_name = top_candidates[0]
            if len(top_candidates) > 1:
                self.logger.warning(f"Multiple top candidates: {top_candidates}, using '{top_module_name}'")
            self.logger.info(f"Auto-detected top module: {top_module_name}")
            top = module_map[top_module_name]

            def build(mod: Dict[str, Any]) -> Dict[str, Any]:
                insts = []
                # for inst in mod.get('insts', []):
                for inst in mod.get('insts', []) or []:
                    child = module_map.get(inst['mod_name'])
                    insts.append({
                        "inst_name": inst['inst_name'],
                        "mod_name": inst['mod_name'],
                        "children": build(child).get('insts', []) if child else []
                    })
                return {"mod_name": mod.get('mod_name', 'Unknown'), "insts": insts}
            return build(top)
        except Exception as e:
            self.logger.error(f"Error parsing YAML {yaml_file_path}: {e}")
            return None

    def _parse_all_registers(self, sv_file_path: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Parse register definitions for every module found in a single SV file.

        Returns: {module_name: [{"regname": ..., "initval": ...}, ...]}
        """
        try:
            content = Path(sv_file_path).read_text()
        except Exception as e:
            self.logger.error(f"Error reading {sv_file_path}: {e}")
            return {}

        reg_map: Dict[str, List[Dict[str, str]]] = {}

        for match in _MODULE_RE.finditer(content):
            mod_name = match.group(1)
            body = match.group(0)
            reg_map[mod_name] = self._extract_registers(body)
            self.logger.debug(
                f"  {mod_name}: {len(reg_map[mod_name])} register(s)"
            )

        return reg_map

    def _extract_registers(self, module_body: str) -> List[Dict[str, str]]:
        """Extract all reg declarations from a module body string"""
        reg_list = []

        # Scalar regs: reg [W:0] name = init;  or  reg name;
        # (re-search each raw 'reg...;' fragment to avoid cross-statement matches)
        for fragment in re.findall(r'\breg\b[^;]*;', module_body, re.DOTALL):
            m = _REG_SCALAR_RE.search(fragment)
            if not m or m.group(2).startswith('_RAND'):
                continue
            bit_width = (m.group(1) or '').strip()
            name = f"{bit_width} {m.group(2)}".strip() if bit_width else m.group(2)
            initval = (m.group(3) or 'None').strip()
            reg_list.append({"regname": name, "initval": initval})

        # Array regs: reg [W:0] name [N:M];
        for m in _REG_ARRAY_RE.finditer(module_body):
            bit_width = (m.group(1) or '').strip()
            reg_name = m.group(2)
            count = abs(int(m.group(3)) - int(m.group(4))) + 1
            if count <= 32:
                for i in range(count):
                    name = f"{bit_width} {reg_name}[{i}]".strip() if bit_width else f"{reg_name}[{i}]"
                    reg_list.append({"regname": name, "initval": 'None'})
            else:
                self.logger.warning(
                    f"Skipping large register array {reg_name} ({count} entries)"
                )

        return reg_list

    def _attach_registers(
        self,
        hierarchy: Dict[str, Any],
        reg_map: Dict[str, List[Dict[str, str]]]
    ) -> None:
        """Recursively attach reg_list to each hierarchy node from pre-parsed map"""
        mod_name = hierarchy.get('mod_name')
        if mod_name in reg_map:
            hierarchy['reg_list'] = reg_map[mod_name]

        for node in hierarchy.get('insts', []) + hierarchy.get('children', []):
            self._attach_registers(node, reg_map)


# =============================================================================
# Public function interface
# =============================================================================

def generate_hierarchy_with_regs(
    sv_top_file: str,
    output_json_path: str,
    inc_dirs: Optional[List[str]] = None,
    define_macros: Optional[List[str]] = None,
    keep_temp: bool = True
) -> bool:
    """
    Parse a single Verilog file and generate JSON with module hierarchy
    and register info. Top module is auto-detected (never instantiated).

    Args:
        sv_top_file:      Path to the SystemVerilog source file
        output_json_path: Path to output JSON file
        inc_dirs:         Include directories for svinst
        define_macros:    Macros to define (e.g. ["SYNTHESIS"])
        keep_temp:        Keep temporary YAML file (default: False)

    Returns:
        True if successful, False otherwise
    """
    return HierarchyParser().generate(
        sv_top_file=sv_top_file,
        output_json_path=output_json_path,
        inc_dirs=inc_dirs,
        define_macros=define_macros,
        keep_temp=keep_temp
    )


__all__ = ['HierarchyParser', 'generate_hierarchy_with_regs']
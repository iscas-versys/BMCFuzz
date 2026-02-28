"""
Snapshot Loader

Provides two public operations on one or more Verilog source files:

  1. prepare_rtl()
     Parse hierarchy (once), then insert **template** ``initial begin …
     end`` blocks (every register = 0) into each registered SV file.

  2. load_snapshot(vcd_file)
     Parse VCD + merge with hierarchy (once), then insert **actual-value**
     initial blocks into each registered SV file.

Multiple SV files (e.g. one for formal, another for fuzzer) share the
same hierarchy and VCD data — only the initial-block insertion runs
per-file.

Extra-file processors (e.g. MemRWHelper) are run once per load_snapshot
call.
"""

import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

from core.config import BMCFUZZ_HOME
from utils.logger import BMCFuzzLogger

from initialization.vcd_parser import VCDParser
from initialization.hierarchy_parser import HierarchyParser
from initialization.rtl_initializer import RTLInitializer


class SnapshotLoader:
    """
    High-level orchestrator for Verilog initial-block generation.

    Typical usage
    -------------
    # Multiple SV files
    loader = SnapshotLoader(
        sv_files={
            "formal": "formal_run/rtl/SimTop.sv",
            "fuzzer": "build/rtl/SimTop.sv",
        },
        project_name="nutshell",
    )

    prepared = loader.prepare_rtl()
    # prepared == {"formal": "…/SimTop_prepared.sv", "fuzzer": "…/SimTop_prepared.sv"}

    loaded = loader.load_snapshot("snap.vcd")
    # loaded == {"formal": "…/SimTop_init.sv", "fuzzer": "…/SimTop_init.sv"}

    # Single SV file (backward compatible)
    loader = SnapshotLoader(sv_files="path/to/SimTop.sv")
    prepared = loader.prepare_rtl()
    # prepared == {"main": "…/SimTop_prepared.sv"}
    """

    def __init__(
        self,
        sv_files: Union[str, Dict[str, str]],
        project_name: Optional[str] = None,
        hierarchy_json: Optional[str] = None,
    ):
        """
        Args:
            sv_files:       Verilog source file(s) to process.
                            - str: single file (stored under the key "main")
                            - Dict[str, str]: named mapping {label: path}
                              e.g. {"formal": "formal/SimTop.sv",
                                    "fuzzer": "build/SimTop.sv"}
            project_name:       CPU type for VCD signal filtering
                            (nutshell | rocket | boom | None)
            hierarchy_json: Pre-generated hierarchy JSON.  If provided the
                            hierarchy parsing step is skipped.
        """
        self.logger   = BMCFuzzLogger.get_logger("SnapshotLoader")
        self.project_name = project_name
        self.rtl_init = RTLInitializer()

        # Normalise sv_files to Dict[str, Path]
        if isinstance(sv_files, str):
            self._sv_files: Dict[str, Path] = {"main": Path(sv_files)}
        else:
            self._sv_files = {k: Path(v) for k, v in sv_files.items()}

        # Use the first file's stem for hierarchy/template naming
        self._primary_stem = next(iter(self._sv_files.values())).stem

        self._work = Path(BMCFUZZ_HOME) / "tmp" / "snapshot_loader"
        self._work.mkdir(parents=True, exist_ok=True)

        self._extra: List[Tuple[str, str, Callable]] = []

        self._hierarchy_json: Optional[Path] = (
            Path(hierarchy_json) if hierarchy_json else None
        )

        # Auto-register MemRWHelper extra processor for known CPU projects
        _CPU_PROJECTS = {"nutshell", "rocket", "boom"}
        if self.project_name in _CPU_PROJECTS:
            seen: set = set()
            for sv_path in self._sv_files.values():
                mem_helper = sv_path.parent / "MemRWHelper.v"
                if mem_helper.exists() and str(mem_helper) not in seen:
                    seen.add(str(mem_helper))
                    self.register_extra_file(
                        src_file=str(mem_helper),
                        dst_file=str(mem_helper),
                        processor=self.rtl_init.update_mem_rw_helper,
                    )

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    def register_extra_file(
        self,
        src_file: str,
        dst_file: str,
        processor: Callable[[str, str, str], bool],
    ) -> None:
        """
        Register an extra-file processor run after load_snapshot.

        Args:
            src_file:  Source Verilog file (e.g. MemRWHelper_difftest.v)
            dst_file:  Destination path for the processed file
            processor: (vcd_json_path, src_file, dst_file) -> bool
        """
        self._extra.append((src_file, dst_file, processor))
        self.logger.info(
            f"Registered extra processor: "
            f"{Path(src_file)} -> {Path(dst_file)} ({processor.__name__})"
        )

    def prepare_rtl(
        self,
        output_map: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Parse hierarchy and insert template initial blocks into every SV file.

        All registers are initialised to 0.  The hierarchy JSON is parsed
        once (from the first registered SV file) and shared across files.

        Args:
            output_map: {label: output_path} overrides.  Labels not present
                        in the map get an auto-generated path.

        Returns:
            {label: output_path} for every registered SV file,
            or None on failure.
        """
        output_map = output_map or {}

        if not self._ensure_hierarchy():
            return None

        # Build template register JSON (shared across files)
        template_json = self._work / f"{self._primary_stem}_template_regs.json"
        if not self._build_template_registers(str(template_json)):
            return None

        results: Dict[str, str] = {}
        for label, sv_path in self._sv_files.items():
            out = output_map.get(label)
            if out is None:
                out = str(
                    self._work / label / f"{sv_path.stem}_prepared.sv"
                )
            Path(out).parent.mkdir(parents=True, exist_ok=True)

            self.logger.info(
                f"[{label}] Inserting template initial blocks -> {out}"
            )
            if not self.rtl_init.insert_initial_blocks(
                str(sv_path), str(template_json), out
            ):
                self.logger.error(
                    f"[{label}] Failed to insert template initial blocks"
                )
                return None

            results[label] = out

        self.logger.info(f"Prepared RTL for {len(results)} file(s)")
        return results

    def load_snapshot(
        self,
        vcd_file: str,
        output_map: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Load a VCD snapshot into every registered SV file.

        VCD parsing and hierarchy merging are done once; only the
        initial-block insertion runs per file.

        Args:
            vcd_file:   Path to the VCD waveform file
            output_map: {label: output_path} overrides.

        Returns:
            {label: output_path} for every registered SV file,
            or None on failure.
        """
        output_map = output_map or {}

        if not self._ensure_hierarchy():
            return None

        vcd_path = Path(vcd_file)
        if not vcd_path.exists():
            self.logger.error(f"VCD file not found: {vcd_file}")
            return None

        snap_dir = self._work / vcd_path.stem
        snap_dir.mkdir(exist_ok=True)

        # 1. Parse VCD -> JSON  (once)
        vcd_json = snap_dir / "vcd.json"
        self.logger.info(f"Parsing VCD {vcd_file}")
        if not self._parse_vcd(vcd_file, str(vcd_json)):
            return None

        # 2. Merge VCD into hierarchy  (once)
        regs_json = snap_dir / "registers.json"
        self.logger.info("Merging VCD into hierarchy")
        if not self.rtl_init.merge_vcd_into_hierarchy(
            str(self._hierarchy_json), str(vcd_json), str(regs_json)
        ):
            self.logger.error("Failed to merge VCD into hierarchy")
            return None

        # 3. Insert actual-value initial blocks  (per file)
        results: Dict[str, str] = {}
        for label, sv_path in self._sv_files.items():
            out = output_map.get(label)
            if out is None:
                out = str(
                    snap_dir / label / f"{sv_path.stem}_init.sv"
                )
            Path(out).parent.mkdir(parents=True, exist_ok=True)

            self.logger.info(
                f"[{label}] Inserting snapshot initial blocks -> {out}"
            )
            if not self.rtl_init.insert_initial_blocks(
                str(sv_path), str(regs_json), out
            ):
                self.logger.error(
                    f"[{label}] Failed to insert initial blocks"
                )
                return None

            results[label] = out

        # 4. Extra-file processors  (once)
        for src, dst, fn in self._extra:
            self.logger.info(f"Processing extra file {Path(src).name}")
            if not fn(str(vcd_json), src, dst):
                self.logger.warning(
                    f"Extra processor failed for {Path(src).name}"
                )

        self.logger.info(
            f"Snapshot loaded for {len(results)} file(s)"
        )
        return results

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _ensure_hierarchy(self) -> bool:
        """Make sure the hierarchy JSON exists, parsing from the first SV if needed."""
        if self._hierarchy_json and self._hierarchy_json.exists():
            return True

        out = self._work / f"{self._primary_stem}_hierarchy.json"
        # if out.exists():
        #     self._hierarchy_json = out
        #     self.logger.info(f"Reusing cached hierarchy {out}")
        #     return True

        primary_sv = next(iter(self._sv_files.values()))
        self.logger.info(f"Parsing RTL {primary_sv} -> {out}")
        ok = HierarchyParser().generate(
            sv_top_file=str(primary_sv),
            output_json_path=str(out),
        )
        if ok:
            self._hierarchy_json = out
            return True

        self.logger.error(f"Failed to parse RTL: {primary_sv}")
        return False

    def _build_template_registers(self, output_json: str) -> bool:
        """Build a register JSON with every initval set to '0'."""
        try:
            with open(self._hierarchy_json, 'r') as f:
                hierarchy = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading hierarchy JSON: {e}")
            return False

        reg_paths: Dict[str, dict] = HierarchyParser().find_registers(hierarchy)
        for info in reg_paths.values():
            info['initval'] = '0'

        try:
            with open(output_json, 'w') as f:
                json.dump(reg_paths, f, indent=4, ensure_ascii=False)
            self.logger.info(
                f"Template register JSON: {output_json} "
                f"({len(reg_paths)} registers)"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error writing {output_json}: {e}")
            return False

    def _parse_vcd(self, vcd_file: str, output_json: str) -> bool:
        """Parse a VCD file to JSON using the configured signal filter."""
        parser = (
            VCDParser.for_cpu(self.project_name) if self.project_name else VCDParser()
        )
        return parser.parse_vcd_to_json(vcd_file, output_json)


# =============================================================================
# Public function interfaces
# =============================================================================

def prepare_rtl(
    sv_files: Union[str, Dict[str, str]],
    output_map: Optional[Dict[str, str]] = None,
    hierarchy_json: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """
    One-call interface: parse Verilog and produce template-initialised copies.

    Args:
        sv_files:       Single path or {label: path} dict
        output_map:     {label: output_path} overrides
        hierarchy_json: Pre-generated hierarchy JSON (optional)

    Returns:
        {label: output_path} dict, or None on failure.
    """
    loader = SnapshotLoader(sv_files, hierarchy_json=hierarchy_json)
    return loader.prepare_rtl(output_map)


def load_snapshot(
    sv_files: Union[str, Dict[str, str]],
    vcd_file: str,
    output_map: Optional[Dict[str, str]] = None,
    project_name: Optional[str] = None,
    hierarchy_json: Optional[str] = None,
    extra_files: Optional[List[Tuple[str, str, Callable]]] = None,
) -> Optional[Dict[str, str]]:
    """
    One-call interface: load a VCD snapshot into Verilog source(s).

    Args:
        sv_files:       Single path or {label: path} dict
        vcd_file:       VCD waveform file
        output_map:     {label: output_path} overrides
        project_name:       CPU type for VCD filtering
        hierarchy_json: Pre-generated hierarchy JSON (optional)
        extra_files:    List of (src, dst, processor) tuples

    Returns:
        {label: output_path} dict, or None on failure.
    """
    loader = SnapshotLoader(sv_files, project_name=project_name, hierarchy_json=hierarchy_json)
    for src, dst, fn in (extra_files or []):
        loader.register_extra_file(src, dst, fn)
    return loader.load_snapshot(vcd_file, output_map)


__all__ = ['SnapshotLoader', 'prepare_rtl', 'load_snapshot']

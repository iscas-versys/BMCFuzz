import json
import re

from tools import log_message

def find_registers(hierarchy, path="SimTop"):
    """Recursively find all registers with their paths in the hierarchy."""
    reg_paths = {}

    # Process registers at the current level
    mod_name = hierarchy.get('mod_name', 'Unknown')
    for reg in hierarchy.get('reg_list', []):
        reg_name = reg['regname']
        # Extract base name without bit range
        base_name = re.sub(r'\[\d+:\d+\]', '', reg_name).strip()
        reg_paths[f"{path}.{base_name}"] = {
            'regname': reg_name,
            'initval': reg.get('initval', 'None'),
            'module_name': mod_name
        }

    # Process instances at the current level
    for inst in hierarchy.get('insts', []):
        inst_path = f"{path}.{inst['inst_name']}"
        reg_paths.update(find_registers(inst, inst_path))

    # Process children of the current instance
    for child in hierarchy.get('children', []):
        child_path = f"{path}.{child['inst_name']}"
        reg_paths.update(find_registers(child, child_path))

    return reg_paths

def normalize_signal_name(name):
    """Normalize signal name by removing bit ranges and 'TOP.' prefix."""
    # Remove bit range and 'TOP.' prefix
    normalized_name = re.sub(r'\[\d+:\d+\]', '', name).replace('TOP.', '', 1).strip()
    return normalized_name

def update_registers_with_vcd(reg_paths, vcd_data):
    unmatched_registers = []

    # Create a dictionary for quick lookup of VCD signals
    vcd_dict = {}
    for signal in vcd_data:
        # Normalize the signal name
        normalized_name = normalize_signal_name(signal['name'])
        vcd_dict[normalized_name] = signal['value']

    for reg_path, reg in reg_paths.items():
        # Normalize the register name
        normalized_reg_name = normalize_signal_name(reg_path)

        if normalized_reg_name in vcd_dict:
            reg['initval'] = vcd_dict[normalized_reg_name]
        else:
            unmatched_registers.append(f"TOP.{reg_path}")

    return unmatched_registers

def connect_json_vcd(hierarchy_regs_json_path, vcd_parser_json, updated_registers_json):
    # Load hierarchy_emu_new.json
    with open(hierarchy_regs_json_path, 'r') as f:
        hierarchy_data = json.load(f)

    # Find all registers in the hierarchy
    reg_paths = find_registers(hierarchy_data)

    # Load vcd_parser.json
    with open(vcd_parser_json, 'r') as f:
        vcd_data = json.load(f)

    # Update register initvals with VCD data
    unmatched_registers = update_registers_with_vcd(reg_paths, vcd_data)

    # Save the updated register paths to a new JSON file
    with open(updated_registers_json, 'w') as f:
        json.dump(reg_paths, f, indent=4, ensure_ascii=False)

    # Output unmatched registers
    if unmatched_registers:
        log_message(f"[Warn] {len(unmatched_registers)} registers not found in VCD:")
        # return 1
    return 0
    # print("\nUnmatched Registers:")
    # for reg in unmatched_registers:
    #     print(reg)

def main():
    hierarchy_emu_new = "./hierarchy_emu_new.json"
    vcd_parser_json = "./vcd_parser.json"
    updated_registers_json = "./updated_registers.json"
    connect_json_vcd(hierarchy_emu_new, vcd_parser_json, updated_registers_json)

if __name__ == "__main__":
    main()

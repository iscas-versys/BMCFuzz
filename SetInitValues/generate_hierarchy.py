import yaml
import json
import os

from tools import log_message

def parse_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def find_module_by_name(modules, mod_name):
    for module in modules:
        if module['mod_name'] == mod_name:
            return module
    return None

def build_hierarchy(modules, current_module):
    if current_module is None:
        log_message("Error: current_module is None")
        return {}

    hierarchy = {
        "mod_name": current_module.get('mod_name', 'Unknown'),
        "insts": []
    }
    
    insts = current_module.get('insts')
    if insts is None:
        # log_message(f"Warning: No instances found in module {current_module.get('mod_name', 'Unknown')}", print_message=False)
        return hierarchy

    for inst in insts:
        # log_message(f"Processing instance {inst['inst_name']} of module {inst['mod_name']}", print_message=False)
        child_module = find_module_by_name(modules, inst['mod_name'])
        if child_module:
            child_hierarchy = build_hierarchy(modules, child_module)
            hierarchy['insts'].append({
                "inst_name": inst['inst_name'],
                "mod_name": inst['mod_name'],
                "children": child_hierarchy.get('insts', [])
            })
        else:
            # log_message(f"Warning: child module {inst['mod_name']} not found", print_message=False)
            hierarchy['insts'].append({
                "inst_name": inst['inst_name'],
                "mod_name": inst['mod_name'],
                "children": []
            })
    return hierarchy

def hierarchy_yaml_parser(yaml_file_path, json_file_path, top_module_name):
    # Parse the YAML file
    data = parse_yaml(yaml_file_path)

    # Extract all module definitions from all files
    all_modules = []
    for file in data['files']:
        all_modules.extend(file['defs'])

    # Find the top module
    top_module = find_module_by_name(all_modules, top_module_name)
    if not top_module:
        log_message(f"Top module {top_module_name} not found in the YAML file.")
        return -1

    # Build the hierarchy
    hierarchy = build_hierarchy(all_modules, top_module)

    # Write the hierarchy to a JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(hierarchy, json_file, indent=4)

    log_message(f"[Step3] Hierarchy has been written to {json_file_path}")
    return 0

def main():
    yaml_file_path = 'hierarchy_emu.yaml'
    json_file_path = 'hierarchy_emu.json'
    top_module_name = 'SimTop'  # Specify the top module name here
    hierarchy_yaml_parser(yaml_file_path, json_file_path, top_module_name)
if __name__ == "__main__":
    main()

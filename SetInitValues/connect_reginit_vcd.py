import json

from runtools import log_message

def find_registers(hierarchy, path="SimTop"):
    """Recursively find all registers with their paths in the hierarchy."""
    reg_paths = {}
    
    # Process registers at the current level
    for reg in hierarchy.get('reg_list', []):
        reg_name = reg['regname'].split()[-1]
        reg_paths[f"{path}.{reg_name}"] = reg
    
    # Process instances at the current level
    for inst in hierarchy.get('insts', []):
        inst_path = f"{path}.{inst['inst_name']}"
        reg_paths.update(find_registers(inst, inst_path))
    
    # Process children of the current instance
    for child in hierarchy.get('children', []):
        child_path = f"{path}.{child['inst_name']}"
        reg_paths.update(find_registers(child, child_path))
    
    return reg_paths
def find_latest_value(data_list):
    """Find the binary value with the latest timestamp from the data list."""
    if not data_list:
        return None
    latest_value = max(data_list, key=lambda x: x[0])
    return latest_value[1]

def update_registers_with_vcd_data(vcd_data, reg_paths):
    """Update register initial values with the latest values from VCD data."""
    def traverse_vcd(node, path=""):
        if path == "":
            current_path = node['name']  # Start with "SimTop"
        else:
            current_path = f"{path}.{node['name']}"
        
        # print(f"Current VCD Path: {current_path}")
        
        if 'data' in node:
            if current_path in reg_paths:
                latest_value = find_latest_value(node['data'])
                reg_paths[current_path]['initval'] = latest_value
        
        for child in node.get('children', []):
            traverse_vcd(child, current_path)
    
    traverse_vcd(vcd_data)

def find_top_moudle_key(vcd_data, top_module_name):
    for idx, item in enumerate(vcd_data):
        if(item['name'] == top_module_name):
            return idx
    return None

def main():
    # Load hierarchy_emu_new.json
    with open('hierarchy_emu_new.json', 'r') as f:
        hierarchy_data = json.load(f)
    
    # Load vcd_test.json
    with open('testvcd.json', 'r') as f:
        vcd_data = json.load(f)['children'][0]  # Access the "SimTop" node
    
    # Find all registers in the hierarchy
    reg_paths = find_registers(hierarchy_data)
    formatted_output = json.dumps(reg_paths, indent=4, ensure_ascii=False)
    # print("Register Paths:")
    # print(formatted_output)
    top_module_key = find_top_moudle_key(vcd_data['children'], "SimTop")
    if(top_module_key == None):
       log_message("[ERROR] Top module not found in VCD data.")
       return
    # # # Update register initial values based on VCD data
    update_registers_with_vcd_data(vcd_data['children'][top_module_key], reg_paths)
    
    # # # Write the updated hierarchy to a new file
    with open('updated_hierarchy.json', 'w') as f:
        json.dump(hierarchy_data, f, indent=4)
    log_message("[INFO] Updated hierarchy written to updated_hierarchy.json")
    # print(vcd_data['children'][-1]['name'])
if __name__ == "__main__":
    main()

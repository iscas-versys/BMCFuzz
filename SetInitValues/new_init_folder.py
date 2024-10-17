import json
from pathlib import Path
import re

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def create_target_directory(target_dir):
    target_dir.mkdir(exist_ok=True)

def parse_json(data):
    init_values = {}
    for key, value in data.items():
        module_name = value['module_name']
        regname = value['regname']
        match = re.search(r'\b(\w+)\s*\[\d+:\d+\]|\[\d+:\d+\]\s*(\w+)', regname)
        regname_clean = (match.group(1) or match.group(2)) if match else regname
        initval = value['initval']
        if module_name not in init_values:
            init_values[module_name] = []
        init_values[module_name].append(f"    {regname_clean} = {initval};")
    return init_values

def update_sv_files(source_dir, target_dir, init_values):
    for module_name, init_statements in init_values.items():
        sv_file_path = source_dir / f"{module_name}.sv"
        if not sv_file_path.exists():
            print(f"Warning: {sv_file_path} does not exist.")
            continue

        with open(sv_file_path, 'r') as sv_file:
            content = sv_file.read()

        endmodule_match = content.find('endmodule')
        if endmodule_match == -1:
            print(f"Warning: No 'endmodule' found in {sv_file_path}.")
            continue

        initial_block = "initial begin\n" + "\n".join(init_statements) + "\nend\n"
        new_content = content[:endmodule_match] + initial_block + content[endmodule_match:]

        new_sv_file_path = target_dir / f"{module_name}.sv"
        with open(new_sv_file_path, 'w') as new_sv_file:
            new_sv_file.write(new_content)

        print(f"Processed {sv_file_path} -> {new_sv_file_path}")

def merge_sv_files(target_dir, merged_file_name):
    merged_file_path = Path(merged_file_name)
    sv_files = list(target_dir.glob('*.v')) + list(target_dir.glob('*.sv'))

    with open(merged_file_path, 'w') as merged_file:
        for sv_file in sv_files:
            with open(sv_file, 'r') as file:
                content = file.read()
            merged_file.write(f"// {sv_file.name}\n")
            merged_file.write(content + "\n\n")

    print(f"All .v and .sv files have been merged into {merged_file_path}")

if __name__ == "__main__":
    source_dir = Path('SimTop_split')
    target_dir = Path('SimTop_Init')
    json_file_path = 'updated_registers.json'
    merged_file_name = 'SimTop_init.sv'

    data = load_json(json_file_path)
    create_target_directory(target_dir)
    init_values = parse_json(data)
    update_sv_files(source_dir, target_dir, init_values)
    merge_sv_files(target_dir, merged_file_name)

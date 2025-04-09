import json
from pathlib import Path
import re
import shutil

from runtools import log_message

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def create_target_directory(target_dir):
    target_dir.mkdir(exist_ok=True)

def copy_sv_files(source_dir, target_dir):
    for sv_file in source_dir.glob('*.sv'):
        shutil.copy(sv_file, target_dir)

def parse_json(data):
    init_values = {}
    for key, value in data.items():
        module_name = value['module_name']
        regname = value['regname']
        range_match = re.search(r'\[(\d+:\d+)\]', regname)
        regname_clean = re.sub("\["+range_match.group(1)+"\]", '', regname) if range_match else regname
        
        initval = value['initval']
        if module_name not in init_values:
            init_values[module_name] = []
        if initval == 'None':
            continue
        init_values[module_name].append(f"    {regname_clean} = {initval};")
    return init_values

def update_sv_files(target_dir, init_values):
    for module_name, init_statements in init_values.items():
        sv_file_path = target_dir / f"{module_name}.sv"
        if not sv_file_path.exists():
            log_message(f"Warning: {sv_file_path} does not exist.")
            continue

        with open(sv_file_path, 'r') as sv_file:
            content = sv_file.read()

        endmodule_match = content.find('endmodule')
        if endmodule_match == -1:
            log_message(f"Warning: No 'endmodule' found in {sv_file_path}.")
            continue

        initial_block = "initial begin\n" + "\n".join(init_statements) + "\nend\n"
        new_content = content[:endmodule_match] + initial_block + content[endmodule_match:]

        with open(sv_file_path, 'w') as new_sv_file:
            new_sv_file.write(new_content)

        # print(f"Updated {sv_file_path}")

def merge_sv_files(target_dir, merged_file_name):
    merged_file_path = Path(merged_file_name)
    sv_files = list(target_dir.glob('*.v')) + list(target_dir.glob('*.sv'))

    with open(merged_file_path, 'w') as merged_file:
        for sv_file in sv_files:
            with open(sv_file, 'r') as file:
                content = file.read()
            merged_file.write(f"// {sv_file.name}\n")
            merged_file.write(content + "\n\n")

    log_message(f"All .v and .sv files have been merged into {merged_file_path}")

def create_init_files(source_dir, target_dir, json_file_path, merged_file_name):
    source_dir_path = Path(source_dir)
    target_dir_path = Path(target_dir)
    data = load_json(json_file_path)
    create_target_directory(target_dir_path)
    copy_sv_files(source_dir_path, target_dir_path)
    init_values = parse_json(data)
    update_sv_files(target_dir_path, init_values)
    merge_sv_files(target_dir_path, merged_file_name)

if __name__ == "__main__":
    source_dir = './SimTop_split'
    target_dir = './SimTop_Init'
    json_file_path = 'updated_registers.json'
    merged_file_name = 'SimTop_init.sv'

    create_init_files(source_dir, target_dir, json_file_path, merged_file_name)
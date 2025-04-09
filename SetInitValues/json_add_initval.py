import json
import re
import os

from runtools import log_message

reg_cnt = 0

def parse_sv_file(filepath):
    reg_list = []
    global reg_cnt
    with open(filepath, 'r') as file:
        content = file.read()
        # Match register definitions
        reg_matches = re.findall(r'(\breg\b.*?;)', content, re.DOTALL)
        for reg in reg_matches:
            reg_cnt = reg_cnt + 1
            # Match register name and initial value
            reg_name_match = re.search(r'\breg\b\s*(\[\d+:\d+\]\s*)?([a-zA-Z_][a-zA-Z0-9_$]*)\s*(=\s*(.*?))?;', reg, re.DOTALL)
            if reg_name_match:
                bit_width = reg_name_match.group(1) if reg_name_match.group(1) else ''
                reg_name = reg_name_match.group(2)
                init_val = reg_name_match.group(4) if reg_name_match.group(4) else 'None'

                # Skip registers with names starting with _RAND
                if reg_name.startswith('_RAND'):
                    reg_cnt = reg_cnt - 1
                    continue

                
                # Construct the full register name with bit width
                full_reg_name = f"{bit_width}{reg_name}".strip()

                # Add the register to the list
                reg_list.append({"regname": full_reg_name, "initval": init_val})
            
            muti_regname_match = re.search(r"reg\s*(\[\d+:\d+\])?\s+(\w+)\s*\[(\d+):(\d+)\];", reg, re.DOTALL)
            if muti_regname_match:
                bit_width = muti_regname_match.group(1) if muti_regname_match.group(1) else ''
                reg_name = muti_regname_match.group(2)
                reg_num = int(muti_regname_match.group(4)) - int(muti_regname_match.group(3)) + 1
                init_val = 'None'

                if reg_num > 16:
                    # log_message(f"skip multi_reg with reg_num > 16: {reg_name} {reg_num}", print_message=False)
                    continue

                for i in range(reg_num):
                    # Construct the full register name with bit width
                    full_reg_name = f"{bit_width}{reg_name}[{i}]".strip()

                    # Add the register to the list
                    reg_list.append({"regname": full_reg_name, "initval": init_val})

    return reg_list

def update_json_with_regs(json_data, sv_dir):
    def update_module(module):
        mod_name = module.get("mod_name")
        sv_filepath = os.path.join(sv_dir, f"{mod_name}.sv")
        if os.path.exists(sv_filepath):
            module["reg_list"] = parse_sv_file(sv_filepath)
        if "children" in module:
            for child in module["children"]:
                update_module(child)

    if "mod_name" in json_data:
        mod_name = json_data["mod_name"]
        sv_filepath = os.path.join(sv_dir, f"{mod_name}.sv")
        if os.path.exists(sv_filepath):
            json_data["reg_list"] = parse_sv_file(sv_filepath)

    if "insts" in json_data:
        for inst in json_data["insts"]:
            update_module(inst)
    return json_data

def add_regs(input_json_path, output_json_path, sv_dir):
    # 读取JSON文件
    with open(input_json_path, 'r') as json_file:
        json_data = json.load(json_file)

    # 更新JSON数据
    updated_json_data = update_json_with_regs(json_data, sv_dir)

    # 保存更新后的JSON数据
    with open(output_json_path, 'w') as json_file:
        json.dump(updated_json_data, json_file, indent=4)
    
    log_message(f"Total register count: {reg_cnt}")

def main():
    input_json_path = './hierarchy_emu.json'  # 输入的JSON文件路径
    output_json_path = './hierarchy_emu_new.json'  # 输出的JSON文件路径
    sv_dir = './SimTop_split'  # SystemVerilog文件所在的目录
    add_regs(input_json_path, output_json_path, sv_dir)

if __name__ == "__main__":
    main()


import os
import re
import sys
import shutil
import subprocess
import argparse

from runtools import NOOP_HOME, BMCFUZZ_HOME
from runtools import FuzzArgs
from runtools import run_command
from runtools import log_message, clear_logs, log_init, reset_terminal

cover_point_index = 0

def toggle_cover(reg_list, clock):
    toggle_cover_template = f"""
`ifndef SYNTHESIS
    `ifdef DIFFTEST
        import "DPI-C" function void v_cover_toggle (
            longint cover_index
        );
    always @({clock}) begin
        cover_block
    end
    `endif
`endif
"""

    pre_reg_template = "reg_name_pre <= reg_name;\n"
    cover_instance_template = """
        if (valid) begin
            v_cover_toggle(COVER_INDEX);
        end
        """


    cover_block = []
    for reg_name, reg_length in reg_list:
        pre_reg_line = pre_reg_template.replace("reg_name", reg_name)
        cover_block.append(pre_reg_line)
        for bit in range(reg_length):
            global cover_point_index
            if reg_length == 1:
                cover_instance = cover_instance_template.replace("COVER_INDEX", str(cover_point_index)).replace("valid", f"{reg_name}_pre ^ {reg_name}")
            else:
                cover_instance = cover_instance_template.replace("COVER_INDEX", str(cover_point_index)).replace("valid", f"{reg_name}_pre[{bit}] ^ {reg_name}[{bit}]")
            cover_block.append(cover_instance)
            cover_point_index += 1
    
    cover_block = toggle_cover_template.replace("cover_block", "".join(cover_block))
    # log_message(f"\n{cover_block}\n", print_message=False)

    return cover_block

def generate_firrtl_cover_file(cover_type, cover_point_num, cover_point_names):
    src_dir = os.path.join(BMCFUZZ_HOME, "scripts", "template")
    build_dir = os.path.join(NOOP_HOME, "build", "generated-src")

    src_path = os.path.join(src_dir, "firrtl-cover.h")
    dst_path = os.path.join(build_dir, "firrtl-cover.h")
    shutil.copyfile(src_path, dst_path)

    cover_points_block = ""
    for cover_point_name, reg_length in cover_point_names:
        if reg_length == 1:
            cover_points_block += f"  \"{cover_point_name}\",\n"
        else:
            for bit in range(reg_length):
                cover_points_block += f"  \"{cover_point_name}[{bit}]\",\n"

    cover_type_pattern = re.compile(r"#COVER_TYPE#")
    cover_point_num_pattern = re.compile(r"#COVER_POINT_NUM#")
    cover_point_names_pattern = re.compile(r"#COVER_POINT_NAMES#")
    with open(os.path.join(src_dir, "firrtl-cover.cpp"), 'r') as f:
        lines = f.readlines()
        new_lines = []
        for line in lines:
            line = cover_type_pattern.sub(cover_type, line)
            line = cover_point_num_pattern.sub(str(cover_point_num), line)
            line = cover_point_names_pattern.sub(cover_points_block, line)
            new_lines.append(line)
    with open(os.path.join(build_dir, "firrtl-cover.cpp"), 'w') as f:
        f.writelines(new_lines)
    log_message(f"Generated firrtl-cover.cpp and firrtl-cover.h in {build_dir}")

def generate_cover(args):
    rtl_dir = os.path.join(NOOP_HOME, "build", "rtl")
    if not os.path.exists(rtl_dir):
        log_message("RTL directory does not exist. Please run 'make src' first.")
        sys.exit(1)
    
    cover_point_names = []
    module_def_pattern = re.compile(r"^module\s+(\w+)\s*\(")
    module_end_pattern = re.compile(r"endmodule")
    reg_pattern = re.compile(r"reg\s*(\[\d+:\d+\])?\s+(\w+)(\s*=\s*[^;]+)?;")
    clock_pattern = re.compile(r"^\s*always @\((.+)\)")
    with os.scandir(rtl_dir) as entries:
        for entry in entries:
            if entry.name.endswith(".sv"):
                log_message(f"Processing RTL file: {entry.name}")
                global cover_point_index
                # if cover_point_index > 5000:
                #     log_message("Cover point index exceeded 5000. Stopping generation to prevent overflow.")
                #     break
                new_lines = []
                with open(entry.path, 'r') as f:
                    lines = f.readlines()
                    module_clock = None
                    current_module = None
                    reg_list = []
                    for line in lines:
                        new_lines.append(line)
                        module_def_match = module_def_pattern.search(line)
                        if module_def_match:
                            current_module = module_def_match.group(1)
                            log_message(f"Found module definition: {current_module}", print_message=False)
                            continue
                        if current_module is None:
                            continue
                        clock_match = clock_pattern.search(line)
                        if clock_match and "posedge" in clock_match.group(1):
                            module_clock = clock_match.group(1)
                            log_message(f"Found clock definition: {module_clock} in module {current_module}", print_message=False)
                            continue
                        reg_match = reg_pattern.search(line)
                        if reg_match:
                            reg_name = reg_match.group(2)
                            reg_length = reg_match.group(1) if reg_match.group(1) else "[0:0]"
                            log_message(f"Found register: {reg_name}{reg_length}", print_message=False)
                            reg_length = reg_length.replace("[", "").replace("]", "").split(":")
                            reg_length = abs(int(reg_length[0]) - int(reg_length[1])) + 1
                            if reg_name.startswith("_"):
                                log_message(f"Skipping register {reg_name} as it starts with an underscore.", print_message=False)
                                continue
                            if reg_length > 64:
                                log_message(f"[Warn] Big register {reg_name} with length {reg_length} found.", print_message=False)
                            reg_list.append((reg_name, reg_length))
                            cover_point_names.append((f"{current_module}.{reg_name}", reg_length))
                            pre_reg_line = reg_pattern.sub(r"reg \1 \2_pre;", line)
                            new_lines.append(pre_reg_line)
                        if module_end_pattern.search(line):
                            if len(reg_list) == 0:
                                log_message(f"No registers found in module {current_module}. Skipping toggle coverage generation.", print_message=False)
                                continue
                            if module_clock is None:
                                log_message(f"No clock found in module {current_module}. Skipping toggle coverage generation.", print_message=False)
                                continue
                            if args.cover_type == "toggle":
                                cover_block = toggle_cover(reg_list, module_clock)
                            else:
                                log_message(f"Unsupported cover type: {args.cover_type}. Skipping module {current_module}.", print_message=False)
                                continue
                            new_lines = new_lines[:-1] + [cover_block] + [line]

                log_message(f"Generating toggle coverage for {entry.name}...")
                # log_message(f"\n{''.join(new_lines)}\n", print_message=False)
                with open(entry.path, 'w') as f:
                    f.writelines(new_lines)

    # generate firrtl cover file
    generate_firrtl_cover_file(args.cover_type, cover_point_index, cover_point_names)

    log_message(f"Total cover points generated: {cover_point_index}")
    log_message(f"{args.cover_type} coverage generation completed.")

if __name__ == "__main__":
    os.chdir(NOOP_HOME)
    clear_logs()
    log_init()
    
    os.makedirs(os.path.join(NOOP_HOME, "tmp"), exist_ok=True)
    
    parser = argparse.ArgumentParser(description="Generate cover for fuzzing")

    parser.add_argument("--cover-type", type=str, default="toggle", help="Type of coverage to generate")

    args = parser.parse_args()
    
    log_message(f"Generating {args.cover_type} coverage...")
    generate_cover(args)

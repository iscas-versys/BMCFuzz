import os
import sys
import shutil
import subprocess
import argparse

from runtools import run_command
from runtools import log_init, log_message

NOOP_HOME = os.getenv("NOOP_HOME")

def rtl_init(args):
    # 生成build目录
    build_command = f"cd {NOOP_HOME} && source env.sh && unset VERILATOR_ROOT && make clean"
    build_command += f" && make emu REF=$(pwd)/ready-to-run/riscv64-spike-so XFUZZ=1 FIRRTL_COVER={args.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 -j16 > tmp/make_fuzzer.log 2>&1"
    build_command = "bash -c '" + build_command + "'"
    log_message("command:"+build_command)
    ret = run_command(build_command, shell=True)
    if ret:
        log_message("generate build directory failed, ret:", ret)
        return
    log_message("generate build directory")

def generate_nutshell_rtl(args):
    build_dir = os.path.join(NOOP_HOME, "build")
    rtl_src = os.path.join(build_dir, "rtl", "SimTop.sv")
    cover_src = os.path.join(build_dir, "generated-src", "firrtl-cover.cpp")

    formal_dir = os.path.join(NOOP_HOME, "ccover", "Formal", "demo", f"{args.cpu}_{args.cover_type}")
    init_dir = os.path.join(NOOP_HOME, "ccover", "SetInitValues", "rtl_src", f"{args.cpu}")

    # 替换firrtl-cover.cpp
    formal_cover_dst = os.path.join(formal_dir, "firrtl-cover.cpp")
    if os.path.exists(formal_cover_dst):
        os.remove(formal_cover_dst)
    shutil.copy(cover_src, formal_cover_dst)
    log_message("replace firrtl-cover.cpp")

    src_lines = []
    with open(rtl_src, "r") as f:
        src_lines = f.readlines()

    # 修改array中的ram [7:0]为ram [0:7]，并复制array_0_ext.v到SimTop.sv最后
    array_0_ext_src = os.path.join(build_dir, "rtl", "array_0_ext.v")
    with open(array_0_ext_src, "r") as f:
        array_lines = f.readlines()
    for i, line in enumerate(array_lines):
        if "ram [7:0]" in line:
            array_lines[i] = line.replace("ram [7:0]", "ram [0:7]")
    src_lines.extend(array_lines)
    log_message("change ram [7:0] to ram [0:7] and copy array_0_ext.v to SimTop.sv")

    formal_lines = src_lines.copy()

    # 修改enToggle和enToggle_past的值
    for i, line in enumerate(src_lines):
        elements = line.split()
        if len(elements) != 0 and elements[0] == "reg":
            if elements[1] == "enToggle" or elements[1] == "enToggle_past":
                src_lines[i] = src_lines[i].replace("1\'h0", "1'h1")
    log_message("change enToggle and enToggle_past value")
    
    # 插入assume语句限制reset
    assume_line = "assume property(reset == 1'b0);\n"
    formal_assume_line = "initial assume(reset);\n"
    start_module = False
    for i, line in enumerate(src_lines):
        elements = line.split()
        if len(elements) != 0 and elements[0] == "module" and elements[1].startswith("SimTop"):
            start_module = True
        if start_module:
            if len(elements) != 0 and elements[0].startswith(");"):
                src_lines.insert(i+1, assume_line)
                formal_lines.insert(i+1, formal_assume_line)
                break
    log_message("insert assume line")
    
    # 替换Formal目录下的rtl文件
    formal_rtl_dst = os.path.join(formal_dir, "SimTop.sv")
    if os.path.exists(formal_rtl_dst):
        os.remove(formal_rtl_dst)
    with open(formal_rtl_dst, "w") as f:
        f.writelines(formal_lines)
    log_message("replace SimTop.sv in Formal")

    # 替换SetInitValues目录下的rtl文件
    init_rtl_dst = os.path.join(init_dir, "SimTop_"+args.cover_type+".sv")
    if os.path.exists(init_rtl_dst):
        os.remove(init_rtl_dst)
    with open(init_rtl_dst, "w") as f:
        f.writelines(src_lines)
    log_message("replace SimTop.sv in SetInitValues")

def generate_rocket_rtl(args):
    build_dir = os.path.join(NOOP_HOME, "build")
    rtl_src = os.path.join(build_dir, "rtl", "SimTop.sv")
    cover_src = os.path.join(build_dir, "generated-src", "firrtl-cover.cpp")

    formal_dir = os.path.join(NOOP_HOME, "ccover", "Formal", "demo", f"{args.cpu}_{args.cover_type}")
    init_dir = os.path.join(NOOP_HOME, "ccover", "SetInitValues", "rtl_src", f"{args.cpu}")

    log_message("generate rocket rtl")

    # 替换firrtl-cover.cpp
    formal_cover_dst = os.path.join(formal_dir, "firrtl-cover.cpp")
    if os.path.exists(formal_cover_dst):
        os.remove(formal_cover_dst)
    shutil.copy(cover_src, formal_cover_dst)
    log_message("replace firrtl-cover.cpp")

    src_lines = []
    with open(rtl_src, "r") as f:
        src_lines = f.readlines()

    formal_lines = src_lines.copy()

    # 修改enToggle和enToggle_past的值
    for i, line in enumerate(src_lines):
        elements = line.split()
        if len(elements) != 0 and elements[0] == "reg":
            if elements[1] == "enToggle" or elements[1] == "enToggle_past":
                src_lines[i] = src_lines[i].replace("1\'h0", "1'h1")
    log_message("change enToggle and enToggle_past value")
    
    # 插入assume语句限制reset
    assume_line = "assume property(reset == 1'b0);\n"
    formal_assume_line = "initial assume(reset);\n"
    start_module = False
    for i, line in enumerate(src_lines):
        elements = line.split()
        if len(elements) != 0 and elements[0] == "module" and elements[1].startswith("SimTop"):
            start_module = True
        if start_module:
            if len(elements) != 0 and elements[0].startswith(");"):
                src_lines.insert(i+1, assume_line)
                formal_lines.insert(i+1, formal_assume_line)
                break
    log_message("insert assume line")

    # 替换Formal目录下的rtl文件
    formal_rtl_dst = os.path.join(formal_dir, "SimTop.sv")
    if os.path.exists(formal_rtl_dst):
        os.remove(formal_rtl_dst)
    with open(formal_rtl_dst, "w") as f:
        f.writelines(formal_lines)
    log_message("replace SimTop.sv in Formal")

    # 替换SetInitValues目录下的rtl文件
    init_rtl_dst = os.path.join(init_dir, "SimTop_"+args.cover_type+".sv")
    if os.path.exists(init_rtl_dst):
        os.remove(init_rtl_dst)
    with open(init_rtl_dst, "w") as f:
        f.writelines(src_lines)
    log_message("replace SimTop.sv in SetInitValues")

if __name__ == "__main__":
    os.chdir(NOOP_HOME)
    log_init()
    
    parser = argparse.ArgumentParser()

    parser.add_argument("--cpu", type=str, default="rocket")

    parser.add_argument("--only-build", "-b", action="store_true")
    parser.add_argument("--cover-type", "-c", type=str, default="toggle")

    args = parser.parse_args()

    rtl_init(args)
    if not args.only_build:
        if args.cpu == "rocket":
            generate_rocket_rtl(args)
        elif args.cpu == "nutshell":
            generate_nutshell_rtl(args)
    

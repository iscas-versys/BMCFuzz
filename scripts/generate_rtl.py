import os
import re
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
    
    # multi clock -> gbl_clk
    for i, line in enumerate(formal_lines):
        clock_pattern = re.compile(r"\(posedge (\w+)\)")
        clock_match = clock_pattern.search(line)
        if clock_match:
            formal_lines[i] = formal_lines[i].replace(clock_match.group(1), "gbl_clk")
    log_message("change multi clock to gbl_clk")

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

    # 生成reset wave和reset snapshot
    default_reset_cycles = 22
    if not os.path.exists(os.path.join(NOOP_HOME, "tmp", "bin")):
        os.mkdir(os.path.join(NOOP_HOME, "tmp", "bin"))
    with open(os.path.join(NOOP_HOME, "tmp", "bin", "reset.bin"), "wb") as f:
        # 0x00000013
        f.write(b"\x13\x00\x00\x00")
    log_message("generate reset.bin")
    
    commands = f"{NOOP_HOME}/build/fuzzer"
    commands += f" --auto-exit"
    commands += f"-- ./reset.bin"
    commands += f" -C 500"
    commands += f" --dump-wave-full"
    commands += f" --wave-path {NOOP_HOME}/tmp/run_wave.vcd"
    commands += f" --dump-reset-cycles {default_reset_cycles}"
    commands += f" --dump-csr-change"
    log_message("generate reset snapshot command:"+commands)
    ret = run_command(commands, shell=True)
    log_message("generate reset snapshot")

    fuzz_run_dir = os.path.join(NOOP_HOME, "tmp", "fuzz_run", "0")
    src_reset_snapshot = os.path.join(fuzz_run_dir, "csr_snapshot", "csr_snapshot_0")
    src_reset_wave = os.path.join(fuzz_run_dir, "csr_wave", f"csr_wave_0_{default_reset_cycles}.vcd")
    dst_reset_snapshot = os.path.join(init_dir, "reset_snapshot")
    dst_reset_wave = os.path.join(init_dir, f"reset_{args.cover_type}.vcd")
    if os.path.exists(dst_reset_snapshot):
        os.remove(dst_reset_snapshot)
    if os.path.exists(dst_reset_wave):
        os.remove(dst_reset_wave)
    shutil.copy(src_reset_snapshot, dst_reset_snapshot)
    shutil.copy(src_reset_wave, dst_reset_wave)
    log_message("copy reset snapshot and wave")

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
    

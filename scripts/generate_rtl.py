import os
import re
import sys
import shutil
import subprocess
import argparse

from runtools import NOOP_HOME, BMCFUZZ_HOME
from runtools import run_command
from runtools import log_init, log_message

build_dir = os.path.join(NOOP_HOME, "build")
rtl_src = os.path.join(build_dir, "rtl", "SimTop.sv")

formal_dir = ""
init_dir = ""

def rtl_init(args):
    os.mkdir(os.path.join(NOOP_HOME, "tmp"), exist_ok=True)
    # 生成build目录
    build_command = f"cd {NOOP_HOME} && source env.sh && unset VERILATOR_ROOT && make clean"
    build_command += f" && make emu REF=$(pwd)/ready-to-run/riscv64-spike-so BMCFUZZ=1 FIRRTL_COVER={args.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 -j16 > tmp/make_fuzzer.log 2>&1"
    build_command = "bash -c '" + build_command + "'"
    log_message("command:"+build_command)
    ret = run_command(build_command, shell=True)
    if ret:
        log_message("generate build directory failed, ret:", ret)
        exit(1)
    log_message("generate build directory")

def generate_nutshell_rtl(args):
    init_lines = []
    with open(rtl_src, "r") as f:
        init_lines = f.readlines()

    append_array_file(init_lines)
    log_message("append array file to SimTop")

    formal_lines = init_lines.copy()

    init_lines = modify_enToggle_value(init_lines)
    
    formal_rtl_dst = os.path.join(formal_dir, "SimTop.sv")
    write_rtl_file(formal_rtl_dst, formal_lines)
    log_message("replace SimTop.sv in Formal")
    
    init_rtl_dst = os.path.join(init_dir, "SimTop_"+args.cover_type+".sv")
    write_rtl_file(init_rtl_dst, init_lines)
    log_message("replace SimTop.sv in SetInitValues")

    replace_firrtl_file()
    update_GEN_file()

    reset_cycles = 6
    generate_reset_snapshot(args.cover_type, reset_cycles)

def generate_rocket_rtl(args):
    log_message("generate rocket rtl")

    init_lines = []
    with open(rtl_src, "r") as f:
        init_lines = f.readlines()
    formal_lines = init_lines.copy()

    init_lines = modify_enToggle_value(init_lines)

    formal_rtl_dst = os.path.join(formal_dir, "SimTop.sv")
    write_rtl_file(formal_rtl_dst, formal_lines)
    log_message("replace SimTop.sv in Formal")

    init_rtl_dst = os.path.join(init_dir, "SimTop_"+args.cover_type+".sv")
    write_rtl_file(init_rtl_dst, init_lines)
    log_message("replace SimTop.sv in SetInitValues")

    replace_firrtl_file()
    update_GEN_file()

    reset_cycles = 24
    generate_reset_snapshot(args.cover_type, reset_cycles)

def generate_boom_rtl(args):
    log_message("generate boom rtl")
    
    init_lines = []
    with open(rtl_src, "r") as f:
        init_lines = f.readlines()
    formal_lines = init_lines.copy()
    
    init_lines = modify_enToggle_value(init_lines)
    
    formal_rtl_dst = os.path.join(formal_dir, "SimTop.sv")
    write_rtl_file(formal_rtl_dst, formal_lines)
    log_message("replace SimTop.sv in Formal")
    
    init_rtl_dst = os.path.join(init_dir, "SimTop_"+args.cover_type+".sv")
    write_rtl_file(init_rtl_dst, init_lines)
    log_message("replace SimTop.sv in SetInitValues")
    
    replace_firrtl_file()
    update_GEN_file()
    
    reset_cycles = 35
    generate_reset_snapshot(args.cover_type, reset_cycles)

def append_array_file(src_lines):
    array_lines = []
    with os.scandir(os.path.join(build_dir, "rtl")) as entries:
        for entry in entries:
            if entry.name.startswith("array"):
                log_message(f"append {entry.name} to SimTop")
                with open(entry.path, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        ram_match = re.search(r"ram \[(\d+):0\]", line)
                        if ram_match:
                            line = line.replace(f"ram [{ram_match.group(1)}:0]", f"ram [0:{ram_match.group(1)}]")
                        array_lines.append(line)
    src_lines.extend(array_lines)
    return src_lines

def replace_firrtl_file():
    src_file = os.path.join(build_dir, "generated-src", "firrtl-cover.cpp")
    dst_file = os.path.join(formal_dir, "firrtl-cover.cpp")
    if os.path.exists(dst_file):
        os.remove(dst_file)
    shutil.copy(src_file, dst_file)

def modify_enToggle_value(src_lines):
    log_message("change enToggle and enToggle_past value")
    for i, line in enumerate(src_lines):
        elements = line.split()
        if len(elements) != 0 and elements[0] == "reg":
            if elements[1] == "enToggle" or elements[1] == "enToggle_past":
                src_lines[i] = src_lines[i].replace("1\'h0", "1'h1")
    return src_lines

def change_clock(src_lines):
    log_message("change multi clock to glb_clk")
    for i, line in enumerate(src_lines):
        clock_pattern = re.compile(r"\(posedge (\w+)\)")
        clock_match = clock_pattern.search(line)
        if clock_match:
            src_lines[i] = src_lines[i].replace(clock_match.group(1), "glb_clk")
    return src_lines

def write_rtl_file(file_path, lines):
    log_message(f"write rtl file:{file_path}")
    with open(file_path, "w") as f:
        f.writelines(lines)

def update_GEN_file():
    src_dir = os.path.join(build_dir, "rtl")
    dst_dir = formal_dir
    log_message("update GEN file")
    with os.scandir(dst_dir) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.startswith("GEN_"):
                os.remove(entry.path)

    with os.scandir(src_dir) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.startswith("GEN_"):
                src_file = os.path.join(src_dir, entry.name)
                dst_file = os.path.join(dst_dir, entry.name)
                shutil.copy(src_file, dst_file)
                with open(dst_file, "r") as f:
                    lines = f.readlines()
                log_message(f"change clock in {entry.name}")
                lines = change_clock(lines)
                with open(dst_file, "w") as f:
                    f.writelines(lines)

def generate_reset_snapshot(cover_type, reset_cycles):
    log_message("generate reset snapshot")
    if not os.path.exists(os.path.join(NOOP_HOME, "tmp", "bin")):
        os.mkdir(os.path.join(NOOP_HOME, "tmp", "bin"))
    with open(os.path.join(NOOP_HOME, "tmp", "bin", "reset.bin"), "wb") as f:
        # 0x00000013
        f.write(b"\x13\x00\x00\x00")
    log_message("generate reset.bin")

    fuzz_run_dir = os.path.join(NOOP_HOME, "tmp", "fuzz_run", "0")
    os.makedirs(os.path.join(fuzz_run_dir, "csr_snapshot"), exist_ok=True)
    os.makedirs(os.path.join(fuzz_run_dir, "csr_wave"), exist_ok=True)
    
    commands = f"cd {NOOP_HOME} && source env.sh && ./build/fuzzer"
    commands += f" --auto-exit"
    commands += f" --"
    commands += f" {NOOP_HOME}/tmp/bin/reset.bin"
    commands += f" -C 500"
    commands += f" --dump-wave-full"
    commands += f" --wave-path {NOOP_HOME}/tmp/run_wave.vcd"
    commands += f" --dump-reset-cycles {reset_cycles}"
    commands += f" --dump-csr-change"
    # commands += f" --no-diff"
    commands += f" > {NOOP_HOME}/tmp/reset.log"
    commands = "bash -c '" + commands + "'"
    log_message("generate reset snapshot command:"+commands)
    ret = run_command(commands, shell=True)
    log_message("generate reset snapshot")

    src_reset_snapshot = os.path.join(fuzz_run_dir, "csr_snapshot", "csr_snapshot_0")
    src_reset_wave = os.path.join(fuzz_run_dir, "csr_wave", f"csr_wave_0_{reset_cycles}.vcd")
    dst_reset_snapshot = os.path.join(init_dir, "reset_snapshot")
    dst_reset_wave = os.path.join(init_dir, f"reset_{cover_type}.vcd")
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

    formal_dir = os.path.join(BMCFUZZ_HOME, "Formal", "demo", f"{args.cpu}")
    init_dir = os.path.join(BMCFUZZ_HOME, "SetInitValues", "rtl_src", f"{args.cpu}")

    rtl_init(args)
    if not args.only_build:
        if args.cpu == "rocket":
            generate_rocket_rtl(args)
        elif args.cpu == "nutshell":
            generate_nutshell_rtl(args)
        elif args.cpu == "boom":
            generate_boom_rtl(args)
        else:
            log_message("cpu type not support")
            sys.exit(1)

import os
import sys
import shutil
import subprocess
import argparse
import logging
import psutil

from datetime import datetime

NOOP_HOME = os.getenv("NOOP_HOME")
BMCFUZZ_HOME = os.getenv("BMCFUZZ_HOME")

def reset_terminal():
    try:
        subprocess.run(["stty", "sane"], check=True)
        log_message("reset terminal", print_message=False)
    except Exception as e:
        log_message(f"reset terminal error: {e}", print_message=False)

def run_command(command, shell=False):
    try:
        process = subprocess.Popen(command, shell=shell, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        return_code = process.wait()
    except KeyboardInterrupt:
        log_message("Process interrupted, terminating")
        kill_process_and_children(process.pid)
        reset_terminal()
        return_code = -1
    except Exception as e:
        log_message(f"Error: {e}")
        kill_process_and_children(process.pid)
        reset_terminal()
        return_code = -1
    finally:
        log_message("Closing process: " + command)
        return return_code

def kill_process_and_children(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate() 
        parent.terminate()

        gone, still_alive = psutil.wait_procs([parent] + children, timeout=5)
        for p in still_alive:
            p.kill() 
        log_message("All processes killed")
    except psutil.NoSuchProcess:
        log_message("No such process")
    

def log_init(path=None, name="script"):
    if path is None:
        current_dir = os.path.dirname(os.path.realpath(__file__))
    else:
        current_dir = path
        
    if not os.path.exists(os.path.join(current_dir, "logs")):
        os.makedirs(os.path.join(current_dir, "logs"))
    # log_file_name = os.path.join(current_dir, "logs", datetime.now().strftime("%Y-%m-%d_%H-%M") + ".log")
    log_file_name = os.path.join(current_dir, "logs", f"{name}.log")
    logging.basicConfig(filename=log_file_name, level=logging.INFO, format='%(asctime)s - %(message)s', force=True, filemode='w')
    log_message(f"Log initialized in {log_file_name}.")

def log_message(message, print_message=True):
    logging.info(message)
    if print_message:
        print(message)

def clear_logs(path=None):
    if path is None:
        current_dir = os.path.dirname(os.path.realpath(__file__))
    else:
        current_dir = path

    logs_dir = os.path.join(current_dir, "logs")
    if os.path.exists(logs_dir):
        shutil.rmtree(logs_dir)
    os.makedirs(logs_dir)

class FuzzArgs:
    fuzzing = True
    cover_type = "toggle"
    max_runs = 0
    corpus_input = ""
    
    continue_on_errors = False
    insert_nop = False
    save_errors = False
    run_snapshot = False
    only_fuzz = False

    formal_cover_rate = -1.0

    # emu
    max_instr = 100
    max_cycle = 500
    begin_trace = 0

    dump_csr = False

    dump_wave = False
    wave_path = f"{NOOP_HOME}/tmp/run_wave.vcd"

    no_diff = False

    dump_footprints = False
    footprints_path = ""
    as_footprints = False

    snapshot_id = 0
    
    make_log_file = ""
    output_file = ""

    def make_fuzzer(self):
        make_command = f"cd {NOOP_HOME} && source env.sh && unset VERILATOR_ROOT && make clean"
        if self.run_snapshot:
            # make src
            make_command += f" && make emu REF=$(pwd)/ready-to-run/riscv64-spike-so BMCFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 -j16"
            make_command += f" > {self.make_log_file} 2>&1"
            make_command = "bash -c \'" + make_command + "\'"
            log_message(f"Make src command: {make_command}")
            return_code = run_command(make_command, shell=True)
            log_message(f"Make src return code: {return_code}")
            if return_code != 0:
                log_message("Make src failed!")
                sys.exit(1)

            # replace SimTop.sv
            log_message(f"Replace SimTop.sv")
            src_rtl = os.path.join(BMCFUZZ_HOME, "SetInitValues", "SimTop_init.sv")
            dst_rtl = os.path.join(NOOP_HOME, "build", "rtl", "SimTop.sv")

            if os.path.exists(dst_rtl):
                os.remove(dst_rtl)
            
            src_lines = []
            with open(src_rtl, mode='r', encoding='utf-8') as src_file:
                src_lines = src_file.readlines()
                for line in src_lines:
                    if line.startswith("assume"):
                        src_lines.remove(line)
            
            with open(dst_rtl, mode='w', encoding='utf-8') as dst_file:
                dst_file.writelines(src_lines)
            
            # replace MemRWHelper.v
            log_message(f"Replace MemRWHelper.v")
            src_rtl = os.path.join(BMCFUZZ_HOME, "SetInitValues", "MemRWHelper_difftest.v")
            dst_rtl = os.path.join(NOOP_HOME, "build", "rtl", "MemRWHelper.v")

            if os.path.exists(dst_rtl):
                os.remove(dst_rtl)
            shutil.copy(src_rtl, dst_rtl)

            # delete array_0_ext.v
            log_message(f"Delete array_0_ext.v")
            dst_rtl = os.path.join(NOOP_HOME, "build", "rtl", "array_0_ext.v")
            if os.path.exists(dst_rtl):
                os.remove(dst_rtl)

            # make fuzzer
            make_command = f"cd {NOOP_HOME} && source env.sh && unset VERILATOR_ROOT"
            make_command += f" && make fuzzer REF=$(pwd)/ready-to-run/riscv64-spike-so BMCFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 -j16"
            make_command += f" >> {self.make_log_file} 2>&1"
            make_command = "bash -c \'" + make_command + "\'"
            log_message(f"Make fuzzer command: {make_command}")
            return_code = run_command(make_command, shell=True)
            log_message(f"Make fuzzer return code: {return_code}")
            if return_code != 0:
                log_message("Make src failed!")
                sys.exit(1)
        else:
            make_command += f" && make emu REF=$(pwd)/ready-to-run/riscv64-spike-so BMCFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 -j16"
            make_command += f" > {self.make_log_file} 2>&1"
            make_command = "bash -c \'" + make_command + "\'"
            log_message(f"Make fuzzer command: {make_command}")
            return_code = run_command(make_command, shell=True)
            log_message(f"Make fuzzer return code: {return_code}")
            if return_code != 0:
                log_message("Make src failed!")
                sys.exit(1)


    def generate_fuzz_command(self):
        fuzz_command = f"cd {NOOP_HOME} && source env.sh && build/fuzzer"

        if self.fuzzing:
            fuzz_command += " -f"
        fuzz_command += f" -c firrtl.{self.cover_type}"
        if self.max_runs > 0:
            fuzz_command += f" --max-runs {self.max_runs}"
        if self.corpus_input != "":
            fuzz_command += f" --corpus-input {self.corpus_input}"
        
        if self.continue_on_errors:
            fuzz_command += " --continue-on-errors"
        if self.insert_nop:
            fuzz_command += " --insert-nop"
        if self.save_errors:
            fuzz_command += " --save-errors"
        if self.only_fuzz:
            fuzz_command += " --only-fuzz"
        
        if self.formal_cover_rate > 0:
            fuzz_command += f" --formal-cover-rate {self.formal_cover_rate}"
        
        fuzz_command += " --"
        fuzz_command += f" -I {self.max_instr}"
        fuzz_command += f" -C {self.max_cycle}"
        # fuzz_command += f" -b {self.begin_trace}"

        if self.dump_csr:
            fuzz_command += " --dump-csr-change"

        if self.dump_wave:
            fuzz_command += " --dump-wave-full"
            fuzz_command += f" --wave-path {self.wave_path}"

        if self.run_snapshot:
            fuzz_command += " --run-snapshot"
            snapshot_file = os.path.join(BMCFUZZ_HOME, "SetInitValues", "csr_snapshot", f"{self.snapshot_id}")
            fuzz_command += f" --load-snapshot {snapshot_file}"

        if self.no_diff:
            fuzz_command += " --no-diff"
        
        if self.dump_footprints:
            fuzz_command += f" --dump-footprints {self.footprints_path}"
        if self.as_footprints:
            fuzz_command += " --as-footprints"

        if self.output_file != "":
            fuzz_command += f" > {self.output_file}"
            fuzz_command += " 2>&1"
        
        fuzz_command = "bash -c \'" + fuzz_command + "\'"
        log_message(f"Fuzz command: {fuzz_command}")
        return fuzz_command

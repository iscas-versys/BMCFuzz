import os
import sys
import shutil
import subprocess
import argparse

from runtools import NOOP_HOME, BMCFUZZ_HOME
from runtools import FuzzArgs
from runtools import run_command
from runtools import log_message, clear_logs, log_init, reset_terminal

def run_emu(args):
    run_path = os.path.join(NOOP_HOME, "tmp", "fuzz_run", f"{args.fuzz_id}")
    if os.path.exists(run_path):
        shutil.rmtree(run_path)
    os.makedirs(run_path, exist_ok=True)

    if args.make_fuzzer:
        fuzz_args = FuzzArgs()
        fuzz_args.cover_type = args.cover_type
        fuzz_args.run_snapshot = args.run_snapshot
        fuzz_args.make_log_file = os.path.join(NOOP_HOME, "tmp", "make_fuzzer.log")
        fuzz_args.make_fuzzer()

    if args.use_asm_test:
        asm_test_bin = os.path.join(BMCFUZZ_HOME, "asms", "test.bin")
        args.image = asm_test_bin

    if args.dump_csr:
        csr_trans_path = os.path.join(run_path, "csr_transition")
        csr_wave_path = os.path.join(run_path, "csr_wave")
        csr_snapshot_path = os.path.join(run_path, "csr_snapshot")
        os.mkdir(csr_trans_path)
        os.mkdir(csr_wave_path)
        os.mkdir(csr_snapshot_path)
    
    commands = "./build/fuzzer"
    commands += f" -c firrtl.{args.cover_type}"
    commands += f" -- {args.image}"
    commands += f" -I {args.max_instr}"
    commands += f" -C {args.max_circle}"
    commands += f" --fuzz-id {args.fuzz_id}"

    if args.run_snapshot:
        commands += " --run-snapshot"
        snapshot_file = os.path.join(BMCFUZZ_HOME, "SetInitValues", "csr_snapshot", f"{args.snapshot_id}")
        commands += f" --load-snapshot {snapshot_file}"

    if args.no_diff:
        commands += " --no-diff"

    if not args.no_dump_wave:
        commands += " --dump-wave-full"
        commands += f" --wave-path {args.wave_path}"

    if args.dump_trace:
        commands += " --dump-commit-trace"
        if not args.no_diff:
            commands += " --dump-ref-trace"
        commands += " -b 0"
    if args.dump_csr:
        commands += " --dump-csr-change"

    if args.dump_footprints:
        # footprints_path = os.path.join(run_path, "footprints")
        # os.makedirs(footprints_path)
        commands += f" --dump-footprints {args.footprints_path}"
    
    if args.as_footprints:
        commands += " --as-footprints"

    if args.dump_trace:
        commands += f" > {args.output_file}"
        commands += f" 2> {args.err_file}"
    else:
        commands += f" > {args.output_file} 2>&1"
    
    log_message(f"Commands: {commands}")
    ret = run_command(commands, shell=True)
    log_message(f"Return code: {ret}")

def run_fuzz(args):
    default_runs = 1000
    default_fuzz_instr = 5000
    default_fuzz_cycles = 10000

    default_corpus = os.path.join(NOOP_HOME, "corpus", "linearized", "riscv-tests")
    # default_corpus = os.path.join(NOOP_HOME, "corpus", "linearized", "riscv-dv")
    
    fuzz_args = FuzzArgs()

    fuzz_args.cover_type = args.cover_type
    fuzz_args.max_runs = default_runs
    fuzz_args.corpus_input = default_corpus

    fuzz_args.continue_on_errors = True
    # fuzz_args.run_snapshot = args.run_snapshot
    fuzz_args.only_fuzz = True

    fuzz_args.max_instr = default_fuzz_instr
    fuzz_args.max_cycle =  default_fuzz_cycles
    
    # fuzz_args.dump_csr = args.dump_csr
    
    # fuzz_args.dump_wave = not args.no_dump_wave
    # fuzz_args.wave_path = args.wave_path

    fuzz_args.no_diff = args.no_diff
    
    fuzz_args.snapshot_id = args.snapshot_id

    fuzz_args.make_log_file = os.path.join(NOOP_HOME, "tmp", "make_fuzzer.log")
    fuzz_args.output_file = args.output_file

    if args.make_fuzzer:
        fuzz_args.make_fuzzer()

    fuzz_cmd = fuzz_args.generate_fuzz_command()
    ret = run_command(fuzz_cmd, shell=True)
    log_message(f"Return code: {ret}")

if __name__ == "__main__":
    os.chdir(NOOP_HOME)
    clear_logs()
    log_init()

    os.makedirs(os.path.join(NOOP_HOME, "tmp"), exist_ok=True)

    parser = argparse.ArgumentParser()

    # default
    default_max_circle = 3000
    default_max_instr = 300
    default_fuzz_id = 0
    
    default_image = os.path.join(NOOP_HOME, "tmp", "bin", "test.bin")
    default_footprints_path = os.path.join(NOOP_HOME, "tmp", "fuzz_run", "0", "footprints")
    default_wave_path = os.path.join(NOOP_HOME, "tmp", "run_wave.vcd")
    default_output_file = os.path.join(NOOP_HOME, "tmp", "test.log")
    default_err_file = os.path.join(NOOP_HOME, "tmp", "test_err.log")
    
    # emu
    parser.add_argument("--emu", "-e", action='store_true', help="Run emulator")
    parser.add_argument("--image", "-i", type=str, default=default_image, help="Image file")
    parser.add_argument("--dump-trace", "-dt", action='store_true', help="Dump trace")
    parser.add_argument("--dump-csr", "-dc", action='store_true', help="Dump CSR")
    parser.add_argument("--dump-footprints", "-df", action='store_true', help="Dump footprints")
    parser.add_argument("--footprints-path", "-fp", type=str, default=default_footprints_path, help="Footprints path")

    parser.add_argument("--use-asm-test", "-ua", action='store_true', help="Use asm test bin")
    parser.add_argument("--make-fuzzer", "-mf", action='store_true', help="Make fuzzer")
    
    # fuzz
    parser.add_argument("--fuzz", "-f", action='store_true', help="Run fuzz")

    # run options
    parser.add_argument("--cover-type", "-c", type=str, default="toggle", help="Cover type")

    parser.add_argument("--no-diff", "-n", action='store_true', help="No diff")

    parser.add_argument("--max-circle", "-C", type=int, default=default_max_circle, help="Max circle")
    parser.add_argument("--max-instr", "-I", type=int, default=default_max_instr, help="Max instr")   

    parser.add_argument("--no-dump-wave", action='store_true', help="No dump wave")
    parser.add_argument("--wave-path", type=str, default=default_wave_path, help="Wave file")

    parser.add_argument("--as-footprints", "-af", action='store_true', help="As footprints")

    parser.add_argument("--fuzz-id", type=int, default=default_fuzz_id, help="Fuzz id")
    parser.add_argument("--run-snapshot", "-r", action='store_true', help="Run snapshot")
    parser.add_argument("--snapshot-id", "-s", type=int, default=0, help="Snapshot id")

    parser.add_argument("--output-file", "-o", type=str, default=default_output_file, help="Output file")
    parser.add_argument("--err-file", type=str, default=default_err_file, help="Error file")

    args = parser.parse_args()

    if args.emu:
        run_emu(args)
    elif args.fuzz:
        run_fuzz(args)
    
    reset_terminal()
    
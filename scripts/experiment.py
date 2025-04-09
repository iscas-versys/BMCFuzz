import os
import re
import sys
import argparse
import subprocess
import time

import matplotlib.pyplot as plt
import numpy as np

from datetime import datetime

from runtools import NOOP_HOME, BMCFUZZ_HOME
from runtools import log_init, clear_logs, log_message, reset_terminal
from runtools import FuzzArgs
from runtools import kill_process_and_children

TIME_OUT = 30 * 60 * 60
TIME_INTERVAL = 20

def run_and_capture_output(cmd):
    start_time = time.time()
    pre_time = 0
    log_message(cmd)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, shell=True)

    coverage_lines = []

    try:
        for line in iter(process.stdout.readline, ""):
            elapsed_time = time.time() - start_time
            
            if "Total Coverage" in line and elapsed_time - pre_time > TIME_INTERVAL:
                pre_time = elapsed_time
                hours = int(elapsed_time / 3600)
                minutes = int((elapsed_time % 3600) / 60)
                seconds = int(elapsed_time % 60)
                line = "Coverage:"+line.split(' ')[-1].replace('\n','')
                cover_message = f"{hours:>3}h{minutes:>3}m{seconds:>3}s {line}"
                log_message(cover_message, print_message=False)
                coverage_lines.append(cover_message)
            
            if elapsed_time > TIME_OUT:
                log_message("Process timeout, terminating")
                kill_process_and_children(process.pid)
                break

        log_message("Process stdout end")
        process.wait()
    except KeyboardInterrupt:
        log_message("Process interrupted, terminating")
        kill_process_and_children(process.pid)
    except Exception as e:
        log_message(f"Error: {e}")
        kill_process_and_children(process.pid)
    finally:
        log_message("Closing process")
        process.stdout.close()
        process.stderr.close()
        reset_terminal()
    
    return coverage_lines

def fuzz_init(args):
    fuzzer = FuzzArgs()
    fuzzer.cover_type = args.cover_type
    fuzzer.make_log_file = os.path.join(NOOP_HOME, "tmp", "make_fuzzer.log")
    fuzzer.make_fuzzer()

def do_fuzz(args):
    if args.do_xfuzz:
        fuzz_name = "xfuzz"
    elif args.do_pathfuzz:
        fuzz_name = "pathfuzz"
    log_init(name=fuzz_name)
    log_message(f"Running {fuzz_name}")
    log_message("clearing coverage points")
    cover_points_file = os.path.join(BMCFUZZ_HOME, "Formal", "coverTasks", "cover_points.csv")
    if os.path.exists(cover_points_file):
        os.remove(cover_points_file)
    
    fuzzer = FuzzArgs()

    fuzzer.cover_type = args.cover_type
    # fuzzer.max_runs = 1000000
    if args.do_xfuzz:
        fuzzer.corpus_input = os.getenv("LINEARIZED_CORPUS")
    elif args.do_pathfuzz:
        fuzzer.corpus_input = os.getenv("FOOTPRINTS_CORPUS")

    fuzzer.continue_on_errors = True
    fuzzer.only_fuzz = True
    
    fuzzer.max_instr = 10000
    fuzzer.max_cycle = 10000

    fuzzer.as_footprints = args.do_pathfuzz

    fuzz_cmd = fuzzer.generate_fuzz_command()

    coverage_lines = run_and_capture_output(fuzz_cmd)
    log_message("Fuzzing done")

    log_message("Output coverage")
    output_file = os.path.join(NOOP_HOME, "tmp", "exp", f"{fuzz_name}.log")
    with open(output_file, "w") as f:
        f.write("\n".join(coverage_lines))

def do_bmc(args):
    fuzz_cmd = f"cd {NOOP_HOME} && source env.sh"
    if args.do_hypfuzz:
        fuzz_name = "hypfuzz"
        fuzz_cmd += f" && python3 {NOOP_HOME}/ccover/Formal/Scheduler.py -c {args.cover_type}"
    elif args.do_bmcfuzz:
        fuzz_name = "bmcfuzz"
        fuzz_cmd += f" && python3 {NOOP_HOME}/ccover/BMCFuzz.py -f -d -c {args.cover_type}"
    fuzz_cmd = f"bash -c \'{fuzz_cmd}\'"
    log_init(name=fuzz_name)
    log_message(f"Running {fuzz_name}")

    coverage_lines = run_and_capture_output(fuzz_cmd)
    log_message("Fuzzing done")

    log_message("Output coverage")
    output_file = os.path.join(NOOP_HOME, "tmp", "exp", f"{fuzz_name}.log")
    with open(output_file, "w") as f:
        f.write("\n".join(coverage_lines))

def format_time_diff(time_diff):
    total_seconds = time_diff.total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):>3}h {int(minutes):>2}m {int(seconds):>2}s"

def analyze_log(args):
    output_lines = []
    src_file = args.log_file
    if args.analyze_hypfuzz:
        dst_file = args.log_file.split('/')[:-1] + ['hypfuzz.log']
    elif args.analyze_bmcfuzz:
        dst_file = args.log_file.split('/')[:-1] + ['bmcfuzz.log']
    else:
        log_message("Invalid log file")
        return
    dst_file = '/'.join(dst_file)
    with open(src_file, "r") as f:
        lines = f.readlines()
        time_format = "%Y-%m-%d %H:%M:%S,%f"
        start_time = datetime.strptime(lines[0].split(' - ')[0], time_format)
        for line in lines[1:]:
            timestamp_str, coverage_str = line.split(' - ')
            timestamp = datetime.strptime(timestamp_str, time_format)
            coverage = coverage_str.split(': ')[1]

            time_diff = timestamp - start_time

            time_diff_str = format_time_diff(time_diff)
            output_str = f"{time_diff_str} Coverage: {coverage}"
            output_lines.append(output_str)
            log_message(output_str)
    
    with open(dst_file, "w") as f:
        f.write(''.join(output_lines))

def parse_time_to_seconds(time_str):
    hours, minutes, seconds = 0, 0, 0
    parts = time_str.split(' ')
    for part in parts:
        if 'h' in part:
            hours = int(part.replace('h', ''))
        elif 'm' in part:
            minutes = int(part.replace('m', ''))
        elif 's' in part:
            seconds = int(part.replace('s', ''))
    return hours * 3600 + minutes * 60 + seconds

def parse_time_to_hours(time_str):
    hours, minutes, seconds = 0, 0, 0
    parts = time_str.split(' ')
    for part in parts:
        if 'h' in part:
            hours = int(part.replace('h', ''))
        elif 'm' in part:
            minutes = int(part.replace('m', ''))
        elif 's' in part:
            seconds = int(part.replace('s', ''))
    return hours + minutes / 60 + seconds / 3600

def prepare_data(data):
    # times = [parse_time_to_seconds(t[0]) for t in data]
    times = [parse_time_to_hours(t[0]) for t in data]
    coverages = [t[1] for t in data]
    return times, coverages

def generate_graph(args):
    experiment_dir = os.path.join(NOOP_HOME, "tmp", "exp")
    xfuzz_data = []
    pathfuzz_data = []
    hypfuzz_data = []
    bmcfuzz_data = []
    
    match_pattern = re.compile(r"(.*) Coverage:(.*)%")
    if args.analyze_xfuzz:
        with open(os.path.join(experiment_dir, "xfuzz.log"), "r") as f:
            lines = f.readlines()
            for line in lines:
                match = match_pattern.match(line)
                if match:
                    xfuzz_data.append((match.group(1), float(match.group(2))))
    if args.analyze_pathfuzz:
        with open(os.path.join(experiment_dir, "pathfuzz.log"), "r") as f:
            lines = f.readlines()
            for line in lines:
                match = match_pattern.match(line)
                if match:
                    pathfuzz_data.append((match.group(1), float(match.group(2))))
    if args.analyze_hypfuzz:
        with open(os.path.join(experiment_dir, "hypfuzz.log"), "r") as f:
            lines = f.readlines()
            for line in lines:
                match = match_pattern.match(line)
                if match:
                    hypfuzz_data.append((match.group(1), float(match.group(2))))
    if args.analyze_bmcfuzz:
        with open(os.path.join(experiment_dir, "bmcfuzz.log"), "r") as f:
            lines = f.readlines()
            for line in lines:
                match = match_pattern.match(line)
                if match:
                    bmcfuzz_data.append((match.group(1), float(match.group(2))))
    
    xfuzz_times, xfuzz_coverages = prepare_data(xfuzz_data)
    pathfuzz_times, pathfuzz_coverages = prepare_data(pathfuzz_data)
    hypfuzz_times, hypfuzz_coverages = prepare_data(hypfuzz_data)
    bmcfuzz_times, bmcfuzz_coverages = prepare_data(bmcfuzz_data)

    # 绘制图表
    plt.figure(figsize=(10, 6))

    # 绘制每条曲线
    if args.analyze_xfuzz:
        # plt.plot(xfuzz_times, xfuzz_coverages, label='xfuzz', color='r', marker='o')
        plt.plot(xfuzz_times, xfuzz_coverages, label='xfuzz', color='r')
    if args.analyze_pathfuzz:
        # plt.plot(pathfuzz_times, pathfuzz_coverages, label='pathfuzz', color='g', marker='s')
        plt.plot(pathfuzz_times, pathfuzz_coverages, label='pathfuzz', color='g')
    if args.analyze_hypfuzz:
        # plt.plot(hypfuzz_times, hypfuzz_coverages, label='hypfuzz', color='b', marker='^')
        plt.plot(hypfuzz_times, hypfuzz_coverages, label='hypfuzz', color='b')
    if args.analyze_bmcfuzz:
        # plt.plot(bmcfuzz_times, bmcfuzz_coverages, label='bmcfuzz', color='purple', marker='x')
        plt.plot(bmcfuzz_times, bmcfuzz_coverages, label='bmcfuzz', color='purple')

    # 设置标题和标签
    plt.title("Fuzz Coverage", fontsize=14)
    # plt.xlabel("Time (seconds)", fontsize=12)
    plt.xlabel("Time (hours)", fontsize=12)
    plt.ylabel("Coverage (%)", fontsize=12)

    # 显示图例
    plt.legend()

    # 显示图表
    plt.grid(True)
    plt.tight_layout()
    plt.ylim(60, 88)
    # plt.show()
    output_path = os.path.join(NOOP_HOME, "tmp", "exp", "output.png")
    plt.savefig(output_path)

if __name__ == "__main__":
    os.chdir(NOOP_HOME)
    # clear_logs()
    log_init()
    
    parser = argparse.ArgumentParser()

    default_cover_type = "toggle"
    default_time_out = 24 * 60 * 60
    # default_time_out = 60
    default_time_interval = 20
    # default_time_interval = 2

    default_output_dir = os.path.join(NOOP_HOME, "tmp", "exp")
    os.makedirs(default_output_dir, exist_ok=True)

    parser.add_argument("--cover-type", "-c", type=str, default=default_cover_type, help="Coverage type")
    parser.add_argument("--time-out", "-to", type=int, default=default_time_out, help="Timeout")
    parser.add_argument("--time-interval", "-ti", type=int, default=default_time_interval, help="Time interval")
    parser.add_argument("--init", "-i", action='store_true', help="Initialize fuzzing")

    parser.add_argument("--do-xfuzz", "-dx", action='store_true', help="Do xfuzz")
    parser.add_argument("--do-pathfuzz", "-dp", action='store_true', help="Do pathfuzz")

    parser.add_argument("--do-hypfuzz", "-dh", action='store_true', help="Do hypfuzz")
    parser.add_argument("--do-bmcfuzz", "-db", action='store_true', help="Do bmcfuzz")

    parser.add_argument("--analyze-log", "-al", action='store_true', help="Analyze log")
    parser.add_argument("--log-file", "-lf", type=str, help="Log file")

    parser.add_argument("--generate-graph", "-g", action='store_true', help="Generate graph")
    parser.add_argument("--analyze-xfuzz", "-ax", action='store_true', help="Analyze xfuzz log")
    parser.add_argument("--analyze-pathfuzz", "-ap", action='store_true', help="Analyze pathfuzz log")
    parser.add_argument("--analyze-hypfuzz", "-ah", action='store_true', help="Analyze hypfuzz log")
    parser.add_argument("--analyze-bmcfuzz", "-ab", action='store_true', help="Analyze bmcfuzz log")

    args = parser.parse_args()

    TIME_OUT = args.time_out
    TIME_INTERVAL = args.time_interval

    if args.init:
        fuzz_init(args)
    
    if args.do_xfuzz or args.do_pathfuzz:
        do_fuzz(args)

    if args.do_hypfuzz or args.do_bmcfuzz:
        do_bmc(args)
    
    if args.analyze_log:
        analyze_log(args)
    
    if args.generate_graph:
        generate_graph(args)
    

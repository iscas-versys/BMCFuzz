import os
import re
import subprocess
import shutil
import csv

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

from Tools import *

NOOP_HOME = os.getenv("NOOP_HOME")
MAX_WORKERS = 120

def execute_cover_tasks(cover_points, run_snapshot, snapshot_file):
    # return ([], 0)
    # 获取环境变量
    env_path = str(os.getenv("OSS_CAD_SUITE_HOME"))
    output_dir = str(os.getenv("COVER_POINTS_OUT"))

    # 加载OSS CAD Suite环境
    log_message(f"try to load env: {env_path}")
    env_command = f"bash -c 'source {env_path} && env'"
    env_vars = run_command(env_command, shell=True)

    if env_vars != 0:
        log_message(f"env load failed: {env_vars}")
        return 0

    # os.chdir(output_dir)
    cover_cases = []
    strat_time = time.time()
    max_workers = min(MAX_WORKERS, os.cpu_count())
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(execute_cover_task, env_path, cover, output_dir, run_snapshot, snapshot_file): cover for cover in cover_points}
        with tqdm(total=len(futures), desc="Processing covers") as pbar:
            for future in as_completed(futures):
                cover = futures[future]
                log_message(f"cover_{cover}执行完成")
                try:
                    if future.result() != -1:
                        cover_cases.append(cover)
                    # print("result:", future.result())
                except Exception as e:
                    log_message(f"cover_{cover} 任务执行失败: {e}")
                pbar.update(1)
    end_time = time.time()
    log_message(f"任务执行完成, 耗时: {end_time - strat_time:.6f} 秒, 共发现 {len(cover_cases)} 个case")

    return (cover_cases, end_time - strat_time)

def execute_cover_task(env_path, cover, output_dir, run_snapshot, snapshot_file):
    sby_command = f"bash -c 'source {env_path} && sby -f {output_dir}/cover_{cover}.sby'"
    return_code = run_command(sby_command, shell=True)

    cover_point = -1
    cover_dir = os.path.join(output_dir, f"cover_{cover}")
    parse_log_file(cover, cover_dir)
    if return_code == 0:
        log_message(f"发现case: cover_{cover}")
        v_file_path = os.path.join(cover_dir, "engine_0", "trace0_tb.v")
        if os.path.exists(v_file_path):
            log_message(f"开始解析文件: {v_file_path}")
            parse_v_file(cover, v_file_path, f"{output_dir}/hexbin")
            generate_footprint(cover, f"{output_dir}/hexbin", run_snapshot, snapshot_file)
            cover_point = cover
        else:
            log_message(f".v文件不存在: {v_file_path}")
    else:
        log_message(f"未发现case: cover_{cover}, 返回值: {return_code}")
    
    if os.path.exists(f"{output_dir}/cover_{cover}.sby"):
        os.remove(f"{output_dir}/cover_{cover}.sby")
    if os.path.exists(f"{output_dir}/cover_{cover}"):
        shutil.rmtree(f"{output_dir}/cover_{cover}")
    
    return cover_point
    
def parse_log_file(cover_no, cover_dir):
    cover_log_path = os.path.join(cover_dir, "logfile.txt")
    check_log_pattern = r"Checking cover reachability in step (\d+).."
    summary_log_pattern = r"summary: Elapsed clock time \[H:MM:SS \(secs\)\]: (\d+:\d+:\d+) \((\d+\))"
    return_log_pattern = r"DONE \((\S+), rc=(\d+)\)"
    with open(cover_log_path, 'r') as log_file:
        lines = log_file.readlines()
        for line in reversed(lines):
            check_match = re.search(check_log_pattern, line)
            summary_match = re.search(summary_log_pattern, line)
            return_match = re.search(return_log_pattern, line)
            if check_match:
                cover_step = check_match.group(1)
                break
            if summary_match:
                cover_time = summary_match.group(1)
            if return_match:
                cover_return = (return_match.group(1), return_match.group(2))
        log_message(f"cover:{cover_no}, time:{cover_time}, step:{cover_step}, return:({cover_return[0]}, rc={cover_return[1]})")


def parse_v_file(cover_no, v_file_path, output_dir):
    pattern = r"\.helper_0\.memory\[(29'b[01]+)\] = (64'b[01]+);"
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, f"cover_{cover_no}.bin")

    memory_map = {}

    with open(v_file_path, 'r') as v_file:
        for line in v_file:
            match = re.search(pattern, line)
            if match:
                data_addr = match.group(1).split("'b")[1]
                data_bin = match.group(2).split("'b")[1]
                addr_int = int(data_addr, 2) * 8
                data_bytes = int(data_bin, 2).to_bytes(8, byteorder='little')
                memory_map[addr_int] = data_bytes

                addr_hex = f"{addr_int:#010x}"
                lower_32 = int(data_bin[32:], 2)
                lower_32_hex = f"{lower_32:#010x}"
                upper_32 = int(data_bin[:32], 2)
                upper_32_hex = f"{upper_32:#010x}"
                log_message(f"Address: {addr_hex}, Data: {lower_32_hex} {upper_32_hex}")

    with open(output_file_path, 'wb') as output_file:
        current_addr = 0
        for addr in sorted(memory_map.keys()):
            if current_addr < addr:
                gap_size = addr - current_addr
                log_message(f"Filling gap of {gap_size} bytes from {current_addr:#010x} to {addr:#010x}")
                output_file.write(b'\x00' * gap_size)
                current_addr = addr
            output_file.write(memory_map[addr])
            current_addr += 8

    log_message(f"已解析并保存bin文件: {output_file_path}")

def generate_footprint(cover_point, output_dir, run_snapshot, snapshot_file):
    bin_file_path = os.path.join(output_dir, f"cover_{cover_point}.bin")
    footprints_file_path = os.path.join(output_dir, f"cover_{cover_point}.footprints")
    log_file_path = os.path.join(output_dir, f"cover_{cover_point}.log")

    commands = f"{NOOP_HOME}/build/fuzzer"
    commands += f" --auto-exit"
    commands += f" -- {bin_file_path}"
    commands += f" -I 300"
    commands += f" -C 3000"
    commands += f" --fuzz-id 0"
    if run_snapshot:
        commands += " --run-snapshot"
        commands += f" --load-snapshot {snapshot_file}"
    commands += f" --dump-footprints {footprints_file_path}"
    # commands += f" > dev/null 2>&1"
    commands += f" > {log_file_path} 2>&1"

    ret = run_command(commands, shell=True)
    os.remove(bin_file_path)
    os.remove(f"{log_file_path}")
    log_message(f"已生成footprints文件: {footprints_file_path}")

    return 0

if __name__ == "__main__":
    os.chdir(NOOP_HOME)
    clear_logs()
    log_init()
    clean_cover_files()
    # set_max_cover_points(11747)
    set_max_cover_points(8940)
    # set_max_cover_points(1990)
    # sample_cover_points = [5886]
    sample_cover_points = [3148]
    # sample_cover_points = [533, 2549, 1470, 1236, 941, 1816, 1587, 2174, 2446, 1004]
    # generate_rtl_files(run_snapshot=False, cpu="rocket", cover_type="toggle")
    generate_rtl_files(run_snapshot=True, cpu="rocket", cover_type="toggle")
    generate_sby_files(sample_cover_points, cpu="rocket")
    snapshot_file = os.path.join(NOOP_HOME, 'ccover', 'SetInitValues', 'csr_snapshot', "12")
    cover_cases, execute_time = execute_cover_tasks(sample_cover_points, run_snapshot=True, snapshot_file=snapshot_file)
    print(f"共发现 {len(cover_cases)} 个case, 耗时: {execute_time:.6f} 秒")
    print("cover_cases:", cover_cases)
    generate_empty_cover_points_file()

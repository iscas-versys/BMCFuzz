import os
import re
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime
import time

from Pretreat import log_message, log_init, generate_sby_files, clean_cover_files

def run_command(command, shell=False):
    try:
        process = subprocess.Popen(command, shell=shell, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        return_code = process.wait()
        return return_code
    except subprocess.CalledProcessError as e:
        log_message(f"Error occurred: {e.stderr}")
        return None
    except subprocess.TimeoutExpired as e:
        log_message(f"Timeout occurred: {e.stderr}")
        return None
    except Exception as e:
        log_message(f"Exception occurred: {e}")
        return None

def execute_cover_tasks(cover_points):
    # 获取环境变量
    env_path = str(os.getenv("OSS_CAD_SUITE_HOME"))
    output_dir = str(os.getenv("COVER_POINTS_OUT"))

    # 加载OSS CAD Suite环境
    env_command = f"bash -c 'source {env_path} && env'"
    env_vars = run_command(env_command, shell=True)

    if env_vars != 0:
        log_message("环境变量加载失败")
        return 0

    # os.chdir(output_dir)
    cover_cases = []
    strat_time = time.time()
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(execute_cover_task, env_path, cover, output_dir): cover for cover in cover_points}
        with tqdm(total=len(futures), desc="Processing covers") as pbar:
            for future in as_completed(futures):
                cover = futures[future]
                log_message(f"当前正在处理: cover_{cover}")
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

def execute_cover_task(env_path, cover, output_dir):
    sby_command = f"bash -c 'source {env_path} && sby -f {output_dir}/cover_{cover}.sby'"
    return_code = run_command(sby_command, shell=True)

    if return_code == 0:
        log_message(f"发现case: cover_{cover}")
        v_file_path = os.path.join(output_dir, f"cover_{cover}", "engine_0", "trace0_tb.v")
        if os.path.exists(v_file_path):
            log_message(f"开始解析文件: {v_file_path}")
            parse_v_file(cover, v_file_path, f"{output_dir}/hexbin")
            return cover
        else:
            log_message(f".v文件不存在: {v_file_path}")
            return -1
    else:
        log_message(f"未发现case: cover_{cover}, 返回值: {return_code}")
        return -1
    
def parse_v_file(cover_no, v_file_path, output_dir):
    pattern = r"UUT\.mem\.rdata_mem\.helper_0\.memory\[(28'b[01]+)\] = (64'b[01]+);"
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

    log_message(f"已解析并保存: {output_file_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_dir)
    log_init()
    
    clean_cover_files()
    # sample_cover_points = [3933, 4389, 4390, 4392]
    sample_cover_points = [533, 2549, 1470, 1236, 941, 1816, 1587, 2174, 2446, 1004]
    generate_sby_files(sample_cover_points)
    cover_cases, execute_time = execute_cover_tasks(sample_cover_points)
    print(f"共发现 {len(cover_cases)} 个case, 耗时: {execute_time:.6f} 秒")
    print("cover_cases:", cover_cases)

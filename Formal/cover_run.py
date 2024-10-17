import os
import re
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime

# 设置日志记录
log_file_name = datetime.now().strftime("%Y-%m-%d_%H_%M.log")
logging.basicConfig(filename=log_file_name, level=logging.INFO, format='%(asctime)s - %(message)s')

def log_message(message):
    logging.info(message)
    print(message)

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

def run_command(command, shell=False):
    try:
        process = subprocess.Popen(command, shell=shell, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        return_code = process.wait()
        return return_code
    except subprocess.CalledProcessError as e:
        log_message(f"Error occurred: {e.stderr}")
        return None

def execute_cover_task(env_path, cover, output_dir):
    sby_command = f"bash -c 'source {env_path} && sby -f cover_{cover}.sby'"
    return_code = run_command(sby_command, shell=True)

    if return_code == 0:
        log_message(f"发现case: cover_{cover}")
        v_file_path = os.path.abspath(os.path.join(output_dir, f"../cover_{cover}/engine_0/trace0_tb.v"))
        if os.path.exists(v_file_path):
            log_message(f"开始解析文件: {v_file_path}")
            parse_v_file(cover, v_file_path, "hexbin")
        else:
            log_message(f".v文件不存在: {v_file_path}")
    else:
        log_message(f"未发现case: cover_{cover}, 返回值: {return_code}")

def execute_cover_tasks(env_path, cover_to_keep, output_dir):
    env_command = f"bash -c 'source {env_path} && env'"
    env_vars = run_command(env_command, shell=True)

    if env_vars == 0:
        log_message("环境变量加载成功")
        os.chdir(output_dir)
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = {executor.submit(execute_cover_task, env_path, cover, output_dir): cover for cover in cover_to_keep}
            with tqdm(total=len(futures), desc="Processing covers") as pbar:
                for future in as_completed(futures):
                    cover = futures[future]
                    log_message(f"当前正在处理: cover_{cover}")
                    try:
                        future.result()
                    except Exception as e:
                        log_message(f"cover_{cover} 任务执行失败: {e}")
                    pbar.update(1)
    else:
        log_message("环境变量加载失败")

def main():
    cover_to_keep = [3933, 4389, 4390, 4392]  # 示例，保留的 cover 语句编号
    env_path = "/home/seddon/Coding/oss-cad-suite/environment"
    output_dir = './coverTasks'  # 输出文件夹路径
    execute_cover_tasks(env_path, cover_to_keep, output_dir)

if __name__ == "__main__":
    main()

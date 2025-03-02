import re
import os
import shutil
import logging
import csv
import subprocess
import psutil

from datetime import datetime

MAX_COVER_POINTS = 0

def log_init(path=None):
    if path is None:
        current_dir = os.path.dirname(os.path.realpath(__file__))
    else:
        current_dir = path
        
    if not os.path.exists(os.path.join(current_dir, "logs")):
        os.makedirs(os.path.join(current_dir, "logs"))
    if not os.path.exists(os.path.join(current_dir, "logs", "fuzz")):
        os.makedirs(os.path.join(current_dir, "logs", "fuzz"))
    log_file_name = os.path.join(current_dir, "logs", datetime.now().strftime("%Y-%m-%d_%H-%M") + ".log")
    logging.basicConfig(filename=log_file_name, level=logging.INFO, format='%(asctime)s - %(message)s')
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
    fuzz_log_dir = os.getenv("FUZZ_LOG")
    os.makedirs(fuzz_log_dir, exist_ok=True)

def reset_terminal():
    try:
        subprocess.run(["stty", "sane"], check=True)
        log_message("reset terminal")
    except Exception as e:
        log_message(f"reset terminal error: {e}")

def run_command(command, shell=False):
    try:
        process = subprocess.Popen(command, shell=shell, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        return_code = process.wait()
        return return_code
    except KeyboardInterrupt:
        log_message("Process interrupted, terminating")
        kill_process_and_children(process.pid)
        reset_terminal()
        return -1
    except Exception as e:
        log_message(f"Error: {e}")
        kill_process_and_children(process.pid)
        reset_terminal()
        return -1
    finally:
        log_message("Closing process: " + command)

def kill_process_and_children(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)  # 获取所有子进程
        for child in children:
            child.terminate()  # 尝试优雅终止子进程
        parent.terminate()  # 终止主进程

        gone, still_alive = psutil.wait_procs([parent] + children, timeout=5)
        for p in still_alive:
            p.kill()  # 强制杀死仍然存活的进程
        log_message("All processes killed")
    except psutil.NoSuchProcess:
        log_message("No such process")

# 复制、解析并修改RTL文件
def generate_rtl_files(run_snapshot=False, cover_type="toggle"):
    # 获取环境变量
    cover_tasks_path = str(os.getenv("COVER_POINTS_OUT"))
    rtl_init_dir = str(os.getenv("RTL_INIT_DIR"))
    rtl_src_dir = str(os.getenv("RTL_SRC_DIR"))
    rtl_dst_dir = str(os.getenv("RTL_DST_DIR"))

    rtl_src_dir = rtl_src_dir+"_"+cover_type

    # 清理输出目录
    if os.path.exists(cover_tasks_path):
        shutil.rmtree(cover_tasks_path)
    os.makedirs(cover_tasks_path)
    os.makedirs(rtl_dst_dir)
    
    # 遍历文件夹,拷贝文件
    if not os.path.exists(rtl_src_dir):
        log_message(f"RTL source directory {rtl_src_dir} not found.")
        return
    with os.scandir(rtl_src_dir) as entries:
        for entry in entries:
            if entry.name.endswith(".v") or entry.name.endswith(".sv"):
                if run_snapshot:
                    if entry.name == "SimTop.sv":
                        init_file_path = os.path.join(rtl_init_dir, "SimTop_init.sv")
                        shutil.copy(init_file_path, rtl_dst_dir)
                        continue
                    if entry.name == "MemRWHelper.v":
                        init_file_path = os.path.join(rtl_init_dir, "MemRWHelper_formal.v")
                        shutil.copy(init_file_path, rtl_dst_dir)
                        continue
                shutil.copy(entry.path, rtl_dst_dir)
    
    # 解析并修改RTL文件
    cover_points_name = parse_and_modify_rtl_files(run_snapshot, cover_type)

    log_message("Generated RTL files.")
    
    return cover_points_name

# 解析并修改RTL文件
def parse_and_modify_rtl_files(run_snapshot=False, cover_type="toggle"):
    # cover name to cover id
    rtl_dir = str(os.getenv("RTL_SRC_DIR"))
    rtl_dir = rtl_dir+"_"+cover_type
    cover_name_file = rtl_dir + "/firrtl-cover.cpp"
    covername2id = {}
    cover_id = 0
    with open(cover_name_file, 'r') as file:
        lines = file.readlines()
    cover_name_begin = re.compile(r"static const char \*\w+_NAMES\[\] = {")
    cover_name_end = re.compile(r'};')
    cover_name = re.compile(r'\"(.*)\"')
    cover_name_flag = False
    for line in lines:
        cover_name_match = cover_name_begin.search(line)
        if cover_name_match:
            cover_name_flag = True
            continue
        if cover_name_flag:
            if cover_name_end.search(line):
                break
            cover_name_match = cover_name.search(line)
            if cover_name_match:
                covername2id[cover_name_match.group(1)] = cover_id
                cover_id += 1

    # 获取环境变量
    rtl_dir = str(os.getenv("RTL_DST_DIR"))
    if run_snapshot:
        rtl_file = rtl_dir + "/SimTop_init.sv"
    else:
        rtl_file = rtl_dir + "/SimTop.sv"

    with open(rtl_file, 'r') as file:
        lines = file.readlines()
    os.remove(rtl_file)
    
    cover_points = [None] * len(covername2id)
    current_module = None

    # 正则表达式匹配模块声明和cover语句
    module_pattern = re.compile(r'\bmodule\s+(\w+)')
    cover_pattern = re.compile(r'cover\s*\(\s*([^\)]+)\s*\)')
    sub_toggle_pattern = re.compile(r'(_t)(\[\d+\])?$')

    # initial reset
    module_end_pattern = re.compile(r'\);')
    insert_line = "initial assume(reset);\n"
    # has_inserted = False
    has_inserted = True
    
    new_lines = []
    
    for line in lines:
        # 检查模块声明
        module_match = module_pattern.search(line)
        if module_match:
            current_module = module_match.group(1)
        
        # 检查cover语句
        cover_match = cover_pattern.search(line)
        if cover_match and current_module:
            signal_name = cover_match.group(1)
            # 修改 cover 语句，生成带有新的 label 的格式
            cover_name = current_module + "." + signal_name
            cover_name = re.sub(sub_toggle_pattern, r'\2', cover_name)
            cover_id = covername2id.get(cover_name, -1)
            if cover_id == -1:
                log_message(f"cover_name: {cover_name} not found in covername2id.")
                cover_id = len(cover_points)
            new_cover_line = f"    cov_count_{cover_id}: cover({signal_name});\n"
            new_lines.append(new_cover_line)
            cover_points[cover_id] = (current_module, signal_name)
        else:
            # 如果不是 cover 语句，直接将原内容加入到新文件
            new_lines.append(line)
        
        # 插入initial reset
        module_end_match = module_end_pattern.search(line)
        if current_module == "SimTop" and module_end_match and not has_inserted:
            new_lines.append(insert_line)
            has_inserted = True
    
    # 为每个reg插入Initial语句
    if not run_snapshot:
        lines = []
        reg_cnt = 0 
        muti_reg_cnt = 0
        reg_pattern = re.compile(r"reg\s*(\[\d+:\d+\])?\s+(\w+)(\s*=\s*[^;]+)?;")
        muti_reg_pattern = re.compile(r"reg\s*(\[\d+:\d+\])?\s+(\w+)\s*\[(\d+):(\d+)\];")
        for line in new_lines:
            lines.append(line)
            reg_match = reg_pattern.search(line)
            if reg_match:
                if "RAND" in reg_match.group(2):
                    log_message(f"skip RAND reg: {reg_match.group(2)}", False)
                    continue
                reg_cnt += 1
                log_message(f"reg_name: {reg_match.group(2)}", False)
                reg_name = reg_match.group(2)
                if reg_match.group(3):
                    log_message(f"skip reg with init value: {reg_match.group(2)}, init_value: {reg_match.group(3)}", False)
                    continue
                lines.append(f"  initial assume(!{reg_name});\n")
            muti_reg_match = muti_reg_pattern.search(line)
            if muti_reg_match:
                muti_reg_cnt += 1
                reg_name = muti_reg_match.group(2)
                reg_number = int(muti_reg_match.group(4)) - int(muti_reg_match.group(3)) + 1
                if reg_number > 16:
                    log_message(f"skip muti_reg with reg_number > 16: {reg_name}, reg_number: {reg_number}", False)
                    continue
                log_message(f"muti_reg_name: {reg_name}, reg_number: {reg_number}", False)
                for i in range(int(muti_reg_match.group(4)), int(muti_reg_match.group(3)) - 1, -1):
                    lines.append(f"  initial assume(!{reg_name}[{i}]);\n")
        new_lines = lines
        log_message(f"reg_cnt: {reg_cnt}\tmuti_reg_cnt: {muti_reg_cnt}")
    
    # 将修改后的内容写入新的RLT文件
    with open(rtl_file, 'w') as new_file:
        new_file.writelines(new_lines)
        # new_file.writelines(lines)
    
    # 设置MAX_COVER_POINTS
    set_max_cover_points(len(cover_points))

    return cover_points

# 生成 .sby 文件
def generate_sby_files(cover_points):
    # 获取环境变量
    rtl_dir = str(os.getenv("RTL_DST_DIR"))
    cover_tasks_path = str(os.getenv("COVER_POINTS_OUT"))
    sby_template = str(os.getenv("SBY_TEMPLATE"))

    # 读取模板文件内容
    with open(sby_template, 'r') as template_file:
        template_content = template_file.read()
    
    # 获取所有RTL文件
    rtl_files = [os.path.join(rtl_dir, file) for file in os.listdir(rtl_dir)]

    # 生成 formal_files 和 rtl_files 部分内容
    formal_files = '\n'.join([f"read -formal {os.path.basename(file)}" for file in rtl_files])
    verilog_files = '\n'.join([file for file in rtl_files])

    for cover_id in cover_points:
        if cover_id >= MAX_COVER_POINTS:
            log_message(f"cover_id: {cover_id} >= MAX_COVER_POINTS: {MAX_COVER_POINTS}")
            return

        cover_label = f"cov_count_{cover_id}"

        # 使用模板生成 sby 文件内容
        sby_file_content = template_content.format(
            formal_files=formal_files,
            top_module_name="SimTop",
            cover_label=cover_label,
            verilog_files=verilog_files
        )
        
        # 将生成的内容写入新的 .sby 文件
        sby_file_name = os.path.join(cover_tasks_path, f"cover_{cover_id}.sby")
        with open(sby_file_name, 'w') as sby_file:
            sby_file.write(sby_file_content)
    
    log_message("Generated .sby files.")

def set_max_cover_points(max_cover_points):
    global MAX_COVER_POINTS
    default_rocket_toggle_points = 8940
    default_nutshell_toggle_points = 11747
    MAX_COVER_POINTS = max_cover_points

# 清理coverTasks文件夹
def clean_cover_files():
    # 获取环境变量
    cover_points_path = str(os.getenv("COVER_POINTS_OUT"))
    
    # 遍历文件夹,删除cover_前缀的文件
    with os.scandir(cover_points_path) as entries:
        for entry in entries:
            if entry.name.startswith("cover_"):
                if entry.is_file():
                    os.remove(entry.path)
                else:
                    shutil.rmtree(entry.path)
            elif entry.name == "hexbin":
                # 清空hexbin文件夹
                shutil.rmtree(entry.path)
                os.mkdir(entry.path)
    
    log_message("Cleaned cover files.")

def generate_empty_cover_points_file(cover_num=0):
    cover_points_out = str(os.getenv("COVER_POINTS_OUT"))
    cover_points_file_path = cover_points_out + "/cover_points.csv"
    
    # 检查文件是否存在, 如果存在则删除
    if os.path.exists(cover_points_file_path):
        os.remove(cover_points_file_path)
        
    set_max_cover_points(cover_num)
    with open(cover_points_file_path, mode='w', newline='', encoding='utf-8') as file:
        field_name = ['Index', 'Covered']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()

        for i in range(MAX_COVER_POINTS):
            csv_writer.writerow({'Index': i, 'Covered': 0})

if __name__ == "__main__":
    clear_logs()
    log_init()
    clean_cover_files()
    # run_snapshot = False
    run_snapshot = True
    cover_points_name = generate_rtl_files(run_snapshot)
    generate_empty_cover_points_file(len(cover_points_name))
    # generate_sby_files([3933, 4389, 4390, 4392])

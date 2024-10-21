import re
import os
import shutil
import logging

from datetime import datetime

MAX_COVER_POINTS = 1

def log_init():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(os.path.join(current_dir, "logs")):
        os.makedirs(os.path.join(current_dir, "logs"))
    log_file_name = os.path.join(current_dir, "logs", datetime.now().strftime("%Y-%m-%d_%H-%M") + ".log")
    print(log_file_name)
    logging.basicConfig(filename=log_file_name, level=logging.INFO, format='%(asctime)s - %(message)s')

def log_message(message):
    logging.info(message)
    print(message)

# 复制、解析并修改RTL文件
def generate_rtl_files():
    # 获取环境变量
    cover_tasks_path = str(os.getenv("COVER_POINTS_OUT"))
    rtl_src_dir = str(os.getenv("RTL_SRC_DIR"))
    rtl_dst_dir = str(os.getenv("RTL_DST_DIR"))

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
                shutil.copy(entry.path, rtl_dst_dir)
    
    # 解析并修改RTL文件
    cover_points_name = parse_and_modify_rtl_files()

    log_message("Generated RTL files.")
    
    return cover_points_name

# 解析并修改RTL文件
def parse_and_modify_rtl_files():
    # 获取环境变量
    rtl_dir = str(os.getenv("RTL_DST_DIR"))
    rtl_file = rtl_dir + "/SimTop.sv"

    with open(rtl_file, 'r') as file:
        lines = file.readlines()
    os.remove(rtl_file)
    
    cover_points = []
    cover_statements = []
    current_module = None
    cover_id = 0

    # 正则表达式匹配模块声明和cover语句
    module_pattern = re.compile(r'\bmodule\s+(\w+)')
    cover_pattern = re.compile(r'cover\s*\(\s*([^\)]+)\s*\)')

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
            new_cover_line = f"    cov_count_{cover_id}: cover({signal_name});\n"
            new_lines.append(new_cover_line)
            cover_statements.append(f"[{cover_id}] {current_module}.{signal_name}")
            cover_points.append((current_module, signal_name))
            cover_id += 1
        else:
            # 如果不是 cover 语句，直接将原内容加入到新文件
            new_lines.append(line)
        
        # 插入initial reset
        module_end_match = module_end_pattern.search(line)
        if current_module == "SimTop" and module_end_match and not has_inserted:
            new_lines.append(insert_line)
            has_inserted = True
    
    # 将修改后的内容写入新的RLT文件
    with open(rtl_file, 'w') as new_file:
        new_file.writelines(new_lines)
    
    # 设置MAX_COVER_POINTS
    MAX_COVER_POINTS = len(cover_points)

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
        if cover_id < MAX_COVER_POINTS:
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

if __name__ == "__main__":
    # clean_cover_files()
    # cover_points_name = generate_rtl_files()
    # generate_sby_files([1234])
    # generate_sby_files([3933, 4389, 4390, 4392])
    log_init()

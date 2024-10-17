import csv
import random
from cover_run import execute_cover_tasks
from cover_rename import parse_and_modify_verilog, copy_files_to_output_dir
import os

# 输入文件名
input_filename = 'structured_points.csv'

# 读取CSV文件内容
with open(input_filename, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    data = list(reader)

# 将数据按moduleNo分组
modules = {}
for row in data:
    module_no = int(row['moduleNo'])
    if module_no not in modules:
        modules[module_no] = []
    modules[module_no].append(row)

# 随机选择5个moduleNo
selected_modules = random.sample(list(modules.keys()), 5)

# 在每个模块中随机选择4个signNo，并从中选择一个bitNo
selected_cover_nos = []
for module_no in selected_modules:
    signs = {}
    for row in modules[module_no]:
        sign_no = int(row['signNo'])
        if sign_no not in signs:
            signs[sign_no] = []
        signs[sign_no].append(row)
    
    # 如果signNo少于4个，选择所有的signNo
    if len(signs) < 4:
        selected_signs = list(signs.keys())
    else:
        selected_signs = random.sample(list(signs.keys()), 4)
    
    for sign_no in selected_signs:
        selected_bit = random.choice(signs[sign_no])
        selected_cover_nos.append(selected_bit['coverNo'])

# 输出选择的coverNo
print("随机选择的<=20个coverNo:")
print(selected_cover_nos)
env_path = "/home/seddon/Coding/oss-cad-suite/environment"
output_dir = './coverTasks'  # 输出文件夹路径

all_uncovered_no = []
for row in data:
    cover_no = int(row['coverNo'])
    all_uncovered_no.append(cover_no)

all_uncovered_no = [4708, 4709, 4710, 4711, 4712, 4713, 4714, 4715, 4716, 4717, 4718, 4719, 4720]
# all_uncovered_no = [4706, 4707, 4708, 4709]

rtl_dir = '/home/seddon/Coding/fuzz/xfuzz_suite/FuzzingNutShell/ccover/Formal/demo/rtl'  # 原始 RTL 文件夹路径
output_rtl_dir = os.path.join(output_dir, 'rtl')  # 输出 RTL 文件夹路径
new_verilog_file = 'SimTop_renaming.sv'  # 新生成的Verilog文件名

# 复制文件到输出目录
copy_files_to_output_dir(rtl_dir, output_rtl_dir)
top_module_name = "SimTop"
sby_template = './template.sby'
top_module_file = 'SimTop.sv'
verilog_file = os.path.join(output_rtl_dir, top_module_file)
cover_list = parse_and_modify_verilog(
    verilog_file, 
    output_dir, 
    new_verilog_file, 
    # [int(item) for item in selected_cover_nos], 
    all_uncovered_no,
    top_module_name, 
    sby_template, 
    top_module_file
)
# 调用执行函数
# execute_cover_tasks(env_path, selected_cover_nos, output_dir)
execute_cover_tasks(env_path, all_uncovered_no, output_dir)
import csv
import re

# 输入文件名
input_filename = 'uncovered_points.txt'
# 输出文件名
output_filename = 'structured_points.csv'

# 读取文件内容
with open(input_filename, 'r') as file:
    lines = file.readlines()

# 初始化变量
modules = {}
module_index = 0

# 解析每一行
parsed_data = []

for line in lines:
    # 使用正则表达式提取coverNo和name
    match = re.match(r'\[(\d+)\] (.+)', line.strip())
    if match:
        cover_no = int(match.group(1))
        name = match.group(2)

        # 分割name以提取module和sign
        parts = name.split('.')
        module_name = parts[0]
        sign_name = parts[1]

        # 提取bitNo
        bit_match = re.search(r'\[(\d+)\]$', sign_name)
        if bit_match:
            bit_no = int(bit_match.group(1))
            sign_name = sign_name[:bit_match.start()]
        else:
            bit_no = -1

        # 初始化模块信息
        if module_name not in modules:
            modules[module_name] = {
                'moduleNo': module_index,
                'signs': {},
                'next_sign_no': 0
            }
            module_index += 1

        module = modules[module_name]

        # 检查sign是否已存在
        if sign_name not in module['signs']:
            module['signs'][sign_name] = module['next_sign_no']
            module['next_sign_no'] += 1

        sign_no = module['signs'][sign_name]

        # 记录结构化信息
        parsed_data.append({
            'coverNo': cover_no,
            'haveTry': False,
            'haveCover': False,
            'moduleNo': module['moduleNo'],
            'signNo': sign_no,
            'bitNo': bit_no,
            'signName': name
        })

# 将结构化信息写入CSV文件
with open(output_filename, 'w', newline='') as csvfile:
    fieldnames = ['coverNo', 'haveTry', 'haveCover', 'moduleNo', 'signNo', 'bitNo', 'signName']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for data in parsed_data:
        writer.writerow(data)

print(f"数据已成功转换并保存到 {output_filename}")

import re
import os
import shutil

# 复制文件到输出目录
def copy_files_to_output_dir(rtl_dir, output_rtl_dir):
    if not os.path.exists(output_rtl_dir):
        os.makedirs(output_rtl_dir)
    
    for file_name in os.listdir(rtl_dir):
        if file_name.endswith('.v') or file_name.endswith('.sv'):
            full_file_name = os.path.join(rtl_dir, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, output_rtl_dir)

# 解析Verilog文件，并生成新的Verilog文件，同时生成对应的.sby文件
def parse_and_modify_verilog(file_path, output_dir, new_file_name, cover_to_keep, top_module_name="SimTop", sby_template="template.sby", top_module_file="SimTop.sv"):
    output_rtl_dir = os.path.join(output_dir, 'rtl')
    
    # 创建存储输出文件的目录
    if not os.path.exists(output_rtl_dir):
        os.makedirs(output_rtl_dir)
    
    # 生成新的Verilog文件的完整路径
    new_file_path = os.path.join(output_rtl_dir, new_file_name)
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    cover_statements = []
    current_module = None
    cover_id = 0
    
    # 正则表达式匹配模块声明和cover语句
    module_pattern = re.compile(r'\bmodule\s+(\w+)')
    cover_pattern = re.compile(r'cover\s*\(\s*([^\)]+)\s*\)')
    
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
            cover_id += 1
        else:
            # 如果不是 cover 语句，直接将原内容加入到新文件
            new_lines.append(line)
    
    # 将修改后的内容写入新的 Verilog 文件
    with open(new_file_path, 'w') as new_file:
        new_file.writelines(new_lines)
    
    # 为每个指定的 cover_id 生成 .sby 文件
    generate_sby_files(new_file_path, output_dir, cover_to_keep, cover_statements, top_module_name, sby_template, top_module_file)
    
    return cover_statements

# 生成 .sby 文件
def generate_sby_files(verilog_file, output_dir, cover_to_keep, cover_statements, top_module_name, sby_template, top_module_file):
    # 读取模板文件内容
    with open(sby_template, 'r') as template_file:
        template_content = template_file.read()
    
    # 获取所有复制到输出目录的Verilog文件
    output_rtl_dir = os.path.join(output_dir, 'rtl')
    rtl_files = [os.path.join(output_rtl_dir, f) for f in os.listdir(output_rtl_dir) if f.endswith('.v') or f.endswith('.sv')]
    rtl_files.remove(os.path.join(output_rtl_dir, top_module_file))
    # 生成 formal_files 和 verilog_files 部分内容
    formal_files = '\n'.join([f"read -formal {os.path.basename(file)}" for file in rtl_files])
    verilog_files = '\n'.join([f"{os.path.abspath(os.path.join(output_rtl_dir, os.path.basename(file)))}" for file in rtl_files])    
    
    for cover_id in cover_to_keep:
        # 确保 cover_id 合法
        if cover_id < len(cover_statements):
            cover_label = f"cov_count_{cover_id}"

            # 使用模板生成 sby 文件内容
            sby_file_content = template_content.format(
                formal_files=formal_files,
                top_module_name=top_module_name,
                cover_label=cover_label,
                verilog_files=verilog_files
            )
            
            # 将生成的内容写入新的 .sby 文件
            sby_file_name = os.path.join(output_dir, f"cover_{cover_id}.sby")
            with open(sby_file_name, 'w') as sby_file:
                sby_file.write(sby_file_content)
            print(f"Generated {sby_file_name} for {cover_label}")

def main():
    # 使用例子
    rtl_dir = '/home/seddon/Coding/fuzz/xfuzz_suite/FuzzingNutShell/ccover/Formal/demo/rtl'  # 原始 RTL 文件夹路径
    output_dir = './coverTasks'  # 输出文件夹路径
    output_rtl_dir = os.path.join(output_dir, 'rtl')  # 输出 RTL 文件夹路径
    new_verilog_file = 'SimTop_renaming.sv'  # 新生成的Verilog文件名

    # 复制文件到输出目录
    copy_files_to_output_dir(rtl_dir, output_rtl_dir)
    # 指定要保留的 cover 语句编号
    cover_to_keep = [3933, 4389, 4390, 4392]  # 假设你想保留的 cover 语句编号
    # 指定顶层模块名称（可选），默认是 "SimTop"
    top_module_name = "SimTop"
    # top_module_name = "NutCore"
    # 模板文件路径
    sby_template = './template.sby'
    top_module_file = 'SimTop.sv'
    # 调用函数
    verilog_file = os.path.join(output_rtl_dir, top_module_file)
    cover_list = parse_and_modify_verilog(verilog_file, output_dir, new_verilog_file, cover_to_keep, top_module_name, sby_template, top_module_file)
    # # 输出结果
    # for cover in cover_list:
    #     print(cover)
if __name__ == "__main__":
    main()
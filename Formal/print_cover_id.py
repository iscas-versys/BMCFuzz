import re

def print_cover_id(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    cover_statements = []
    current_module = None
    cover_id = 0
    
    # 正则表达式匹配模块声明和cover语句
    module_pattern = re.compile(r'\bmodule\s+(\w+)')
    cover_pattern = re.compile(r'cover\s*\(\s*([^\)]+)\s*\)')
    
    for line in lines:
        # 检查模块声明
        module_match = module_pattern.search(line)
        if module_match:
            current_module = module_match.group(1)
        
        # 检查cover语句
        cover_match = cover_pattern.search(line)
        if cover_match and current_module:
            signal_name = cover_match.group(1)
            cover_statements.append(f"[{cover_id}] {current_module}.{signal_name}")
            cover_id += 1
    
    return cover_statements


def main():
    # 输出SystemVerilog文件中的所有cover声明，格式为:[cover_id] module.cover_signal_name
    verilog_file = './demo/SimTop_1017.sv'  # 替换为你的Verilog文件路径
    cover_list = print_cover_id(verilog_file)

    # 输出结果
    for cover in cover_list:
        print(cover)

if __name__ == "__main__":
    main()
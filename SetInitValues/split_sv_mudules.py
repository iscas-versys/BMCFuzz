import os
import re

def split_sv_modules(file_path):
    # Create output directory
    output_dir = file_path.replace('.sv', '') + '_split'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Read the input .sv file
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Regex to find all module definitions
    module_pattern = re.compile(r'(module\s+(\w+)[\s\S]*?endmodule)', re.MULTILINE)
    modules = module_pattern.findall(content)
    
    # Write each module to its own .sv file
    for module_content, module_name in modules:
        module_file_path = os.path.join(output_dir, f'{module_name}.sv')
        with open(module_file_path, 'w') as module_file:
            module_file.write(module_content)
    
    print(f"Modules have been split into {output_dir} directory.")

if __name__ == "__main__":
    input_file = './SimTop.sv'
    split_sv_modules(input_file)

import json
from Verilog_VCD.Verilog_VCD import parse_vcd
from sys import argv
from runtools import log_message
import re

def convert_netinfo_to_custom_format(netinfo, net_id, net, cpu):
    # 提取网络信息
    hier = net['hier']
    name = net['name']
    size = int(net['size'])
    
    # 提取最后一个时间值对
    last_time_value = netinfo['tv'][-1]
    last_value = last_time_value[1]

    # 修改cycleCnt[63:0]和instrCnt[63:0]的值
    # if name == "cycleCnt[63:0]" or name == "instrCnt[63:0]":
    #     last_value = 0
    full_name = f"{hier}.{name}"

    if cpu == "nutshell":
        cache_tag_pattern = re.compile(r"cache\.metaArray\.ram\..*ram")
        tlb_tag_pattern = re.compile(r"tlb\.mdTLB\.tlbmd_\d+\[\d+\]")
    elif cpu == "rocket":
        cache_tag_pattern = re.compile(r"cache\.tag_array_\d+\[\d+\]")
        tlb_tag_pattern = re.compile(r"ptw\.tags|tag_vpn")
    elif cpu == "boom":
        cache_tag_pattern = None
        tlb_tag_pattern = None
    else:
        cache_tag_pattern = None
        tlb_tag_pattern = None
    
    if cache_tag_pattern is not None and cache_tag_pattern.search(full_name):
        log_message(f"Set cache tag ram {full_name} to 0")
        last_value = 0
    if tlb_tag_pattern is not None and tlb_tag_pattern.search(full_name):
        log_message(f"Set tlb tag {full_name} to 0")
        last_value = 0
    
    # 构造自定义格式的字典
    custom_format = {
        "id": net_id,
        "name": f"{hier}.{name}",
        "value": f"{size}'b{last_value}",
        "width": size
    }
    
    return custom_format

def vcd_to_json(vcd_path, output_json_path, cpu):
    # 解析VCD文件
    vcd_data = parse_vcd(vcd_path)
    # 初始化ID计数器
    net_id = 1
    # 创建一个列表来存储所有网络的自定义格式
    custom_outputs = []
    # 处理每个网络信息并添加到列表中
    for netinfo in vcd_data.values():
        for net in netinfo['nets']:
            custom_output = convert_netinfo_to_custom_format(netinfo, net_id, net, cpu)
            custom_outputs.append(custom_output)
            net_id += 1
    # 输出整个列表为JSON格式
    json_output = json.dumps(custom_outputs, indent=4)
    # save json to output_json_path
    with open(output_json_path, 'w') as f:
        f.write(json_output)

if __name__ == "__main__":
    # 解析VCD文件
    if len(argv) != 3:
        print("[Error] Usage: python vcd_to_json.py <vcd_path> <output_json_path>")
        exit(1)
    vcd_to_json(argv[1], argv[2])
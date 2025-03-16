from Verilog_VCD.Verilog_VCD import parse_vcd
from sys import argv


# Define signal matching rules for different DUTs
SIGNAL_MATCH_RULES = {
    'rocket-chip': [
        {'name': 'imem_rdata', 'hier': 'FormalTop.dut.mem.srams.mem.helper_0', 'role': 'data'},
        {'name': 'r_enable',   'hier': 'FormalTop.dut.mem.srams.mem.helper_0', 'role': 'enable'},
        {'name': 'r_index',    'hier': 'FormalTop.dut.mem.srams.mem.helper_0', 'role': 'addr'}
    ],
    'example_dut': [
        {'name': 'mem_data',   'hier': 'Top.dut.memory.core.data', 'role': 'data'},
        {'name': 'mem_enable', 'hier': 'Top.dut.memory.core.ctrl', 'role': 'enable'},
        {'name': 'mem_addr',   'hier': 'Top.dut.memory.core.ctrl', 'role': 'addr'}
    ]
    # Can continue to add more rules for other DUTs
}


def binary_to_hex_with_separator(binary_str, separator='_'):
    """
    将二进制字符串转换为十六进制字符串，并在每32位之间添加分隔符。

    :param binary_str: 二进制字符串
    :param separator: 分隔符（默认为下划线 '_'）
    :return: 格式化后的十六进制字符串
    """
    # 将二进制字符串转换为整数
    int_value = int(binary_str, 2)
    # 将整数转换为64位十六进制字符串（16个字符）
    hex_str = f"{int_value:016X}"
    # 在每32位之间添加分隔符
    return f"{hex_str[:8]}{separator}{hex_str[8:]}"


def vcd_get_memory_data(vcd_path, output_memory_path, cpu_design='rocket-chip'):
    """
    从 VCD 文件中提取指定处理器设计的访存行为。

    :param vcd_path: VCD 文件路径
    :param output_memory_path: 输出文件路径
    :param cpu_design: 处理器设计名称（默认为 'rocket-chip'）
    """
    # 获取当前处理器设计的信号匹配规则
    if cpu_design not in SIGNAL_MATCH_RULES:
        print(f"[Error] Unsupported CPU design: {cpu_design}")
        exit(1)

    signal_rules = SIGNAL_MATCH_RULES[cpu_design]
    vcd_data = parse_vcd(vcd_path)

    # 存储 enable、addr 和 data 的值
    signal_values = {'enable': {}, 'addr': {}, 'data': {}}

    # 遍历 VCD 数据，提取 enable、addr 和 data 的值
    for netinfo in vcd_data.values():
        for signal in signal_rules:
            if (
                netinfo['nets'][0]['name'] == signal['name'] and
                netinfo['nets'][0]['hier'] == signal['hier']
            ):
                print(f"匹配到{signal['role']}信号: {signal['name']} 在层次 {signal['hier']} (处理器设计: {cpu_design})")            
                for time_sig in netinfo['tv']:
                    clock = time_sig[0]
                    value = time_sig[1]
                    signal_values[signal['role']][clock] = value

    # 匹配访存行为
    memory_access = []
    for time in sorted(signal_values['enable'].keys()):  # 按时间排序
        enable_value = signal_values['enable'].get(time)
        addr_value = signal_values['addr'].get(time)
        data_value = signal_values['data'].get(time)

        # 如果 enable 有效，且 addr 和 data 都存在，则记录访存行为
        if (
            enable_value == '1' and
            addr_value is not None and
            data_value is not None
        ):
            # 将 addr 和 data 转换为十六进制并添加分隔符
            addr_hex = binary_to_hex_with_separator(addr_value)
            data_hex = binary_to_hex_with_separator(data_value)
            memory_access.append({
                'time': time,
                'addr': addr_hex,
                'data': data_hex
            })

    # 输出到文件
    with open(output_memory_path, 'w') as f:
        print('输出到文件:', output_memory_path, '...')
        for access in memory_access:
            f.write(f"Time: {access['time']}, Addr: {access['addr']}, Data: {access['data']}\n")

    print(f"访存行为已提取并保存到 {output_memory_path}")


if __name__ == "__main__":
    if len(argv) < 3 or len(argv) > 4:
        print("[Error] Usage: python new_memory_reader.py <vcd_path> <output_json_path> [cpu_design]")
        print("       cpu_design 默认为 'rocket-chip'")
        exit(1)

    vcd_path = argv[1]
    output_memory_path = argv[2]
    cpu_design = argv[3] if len(argv) == 4 else 'rocket-chip'

    print("Start parsing VCD file:", vcd_path)
    print("Using CPU design:", cpu_design)
    vcd_get_memory_data(vcd_path, output_memory_path, cpu_design)
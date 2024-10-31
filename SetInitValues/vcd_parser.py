#!/usr/bin/env python3

from __future__ import print_function

from argparse import ArgumentParser, RawTextHelpFormatter
import re
import sys
import json
import vcdvcd
from vcdvcd import VCDVCD
def get_bit_width(signal_name):
    import re

    # 正则表达式匹配方括号中的内容
    match = re.search(r'\[(\d+):(\d+)\]', signal_name)
    
    if match:
        # 提取并计算位宽
        high, low = map(int, match.groups())
        return high - low + 1
    else:
        # 如果没有方括号，默认位宽为1
        return 1
    
if __name__ == '__main__':
    parser = ArgumentParser(
        description='Print Verilog value change dump (VCD) files in tabular form.',
        epilog="""
# Examples

Show all signals and values:

    vcdcat a.vcd

Will be too large for any non-trivial design.

Get the list of all signals:

    vcdcat -l a.vcd

Show only selected signals:

    vcdcat -x a.vcd top.module.signal1 top.module.signal2

List all signals that contain the substring "top.":

    vcdcat -l a.vcd top.

This would show both:

    top.module.signal1
    top.module.signal2

Now get the values for signals:

    vcdcat a.vcd top.
""".format(
        f=sys.argv[0]),
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        '-d',
        '--deltas',
        action='store_true',
        default=False,
        help='Only print the signals that changed for each time.',
    )
    parser.add_argument(
        '-l',
        '--list',
        action='store_true',
        default=False,
        help='list signal names and quit',
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-x',
        '--exact',
        action='store_true',
        default=False,
        help='signal names must match exactly, instead of the default substring match',
    )
    group.add_argument(
        '-r',
        '--regexp',
        action='store_true',
        default=False,
        help='signal names are treated as Python regular expressions',
    )
    parser.add_argument(
        'vcd_path',
        metavar='vcd-path',
        nargs='?',
    )
    parser.add_argument(
        'signals',
        help='only print values for these signals. Substrings of the signal are considered a match by default.',
        metavar='signals',
        nargs='*'
    )
    args = parser.parse_args()
    # print("File Path:", args.vcd_path)
    vcd = VCDVCD(args.vcd_path, only_sigs=True)
    all_signals = vcd.signals
    # print(all_signals) # VCD中的全部信号
    # print(args.signals) # 特定的需要打印的signals
    # print(args.list) # 是否列出全部的信号
    # args.exact 是否精确匹配

    if args.signals:
        selected_signals = []
        for s in args.signals:
            r = re.compile(s)
            for a in all_signals:
                if (
                    (args.regexp and r.search(a)) or
                    (args.exact and s == a) or
                    (not args.exact and s in a)
                ):
                    selected_signals.append(a)
    if args.list:
        if args.signals:
            signals = selected_signals
        else:
            signals = all_signals
        print('\n'.join(signals))
    else:
        if args.signals:
            signals = selected_signals
        else:
            signals = []
        if args.deltas:
            callbacks = vcdvcd.PrintDeltasStreamParserCallbacks()
        else:
            callbacks = vcdvcd.PrintDumpsStreamParserCallbacks()
        vcd = VCDVCD(
            vcd_path=args.vcd_path,
            signals=signals,
            store_tvs=False,
            callbacks=callbacks,
        )
        # print(len(vcd.signal_name_list))
        # print(len(vcd.get_endtime_value()[-1]))
        # print(vcd.signal_name_list)
        # print(vcd.get_endtime_value()[-1])
        signal_name_list = vcd.signal_name_list
        endtime_values = vcd.get_endtime_value()[-1]
        signals = []

        for signal_name, idx in signal_name_list.items():
            width = get_bit_width(signal_name)
            signal_info = {
                "id": idx,
                "name": signal_name,
                "value": str(width) + "'b" + bin(int(endtime_values[idx].replace(" ", ""), 16))[2:].zfill(width),
                "width": width
            }
            signals.append(signal_info)
        json_output = json.dumps(signals, indent=4)
        # print(json_output)
        with open('vcd_parser.json', 'w') as file:
            file.write(json_output)

        print("JSON data has been saved to vcd_parser.json")
        # print(vcd.get_endtime_value()[-1][vcd.signal_name_list['counter_tb.enable']])
        # print(bin(int('ffff',16)))
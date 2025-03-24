import os
import re
import argparse
import difflib
import filecmp

NOOP_HOME = os.getenv("NOOP_HOME")
BMCFUZZ_HOME = os.getenv("BMCFUZZ_HOME")

class Snapshot:
    class RegInt:
        reg_name = ["zero", "ra", "sp", "gp",
                    "tp", "t0", "t1", "t2",
                    "s0", "s1", "a0", "a1",
                    "a2", "a3", "a4", "a5",
                    "a6", "a7", "s2", "s3",
                    "s4", "s5", "s6", "s7",
                    "s8", "s9", "s10", "s11",
                    "t3", "t4", "t5", "t6"]
        value = {}
        
        def __init__(self):
            for name in self.reg_name:
                self.value[name] = 0
    
    class RegFloat:
        reg_name = ["ft0", "ft1", "ft2", "ft3",
                    "ft4", "ft5", "ft6", "ft7",
                    "fs0", "fs1", "fa0", "fa1",
                    "fa2", "fa3", "fa4", "fa5",
                    "fa6", "fa7", "fs2", "fs3",
                    "fs4", "fs5", "fs6", "fs7",
                    "fs8", "fs9", "fs10", "fs11",
                    "ft8", "ft9", "ft10", "ft11"]
        value = {}

        def __init__(self):
            for name in self.reg_name:
                self.value[name] = 0
    
    class RegCSR:
        reg_name = ["privilegeMode", "mstatus", "sstatus", "mepc",
                    "sepc", "mtval", "stval", "mtvec",
                    "stvec", "mcause", "scause", "satp",
                    "mip", "mie", "mscratch", "sscratch",
                    "mideleg", "medeleg"]
        value = {}
        
        def __init__(self):
            for name in self.reg_name:
                self.value[name] = 0
    
    class CSR_Buffer:
        value = [0] * 4096
    
    cycleCnt = 0
    reg_int = RegInt()
    reg_fp = RegFloat()
    reg_csr = RegCSR()
    pc = 0
    csr_buffer = CSR_Buffer()

    def input_int_regs(self):
        pass
    
    def output_int_regs(self):
        print("===== Integer Registers =====")
        max_name_length = max(len(name) for name in self.reg_int.reg_name)
        reg_items = list(self.reg_int.value.items())
        for i in range(0, len(reg_items), 4):
            # Generate a row with up to four registers
            row = " ".join(f"{name:>{max_name_length}}({'x'+str(i+cnt):>3}): {value:016x}"
                            for cnt, (name, value) in enumerate(reg_items[i:i + 4]))
            print(row)
    
    def output_fp_regs(self):
        print("===== Floating Point Registers =====")
        max_name_length = max(len(name) for name in self.reg_fp.reg_name)
        reg_items = list(self.reg_fp.value.items())
        for i in range(0, len(reg_items), 4):
            # Generate a row with up to four registers
            row = " ".join(f"{name:>{max_name_length}}: {value:016x}"
                            for name, value in reg_items[i:i + 4])
            print(row)
    
    def output_csr_regs(self):
        print("===== CSR Registers =====")
        print("Cycle Count: ", self.cycleCnt)
        print("PC: 0x{:016x}".format(self.pc))
        # privilegeMode
        print("privilegeMode: ", self.reg_csr.value["privilegeMode"])
        # mstatus, mcause, mepc
        print("mstatus: 0x{:016x} mcause: 0x{:016x} mepc: 0x{:016x}".format(
            self.reg_csr.value["mstatus"], self.reg_csr.value["mcause"], self.reg_csr.value["mepc"]))
        # sstatus, scause, sepc
        print("sstatus: 0x{:016x} scause: 0x{:016x} sepc: 0x{:016x}".format(
            self.reg_csr.value["sstatus"], self.reg_csr.value["scause"], self.reg_csr.value["sepc"]))
        # satp
        print("satp: 0x{:016x}".format(self.reg_csr.value["satp"]))
        # mip, mie
        print("mip: 0x{:016x} mie: 0x{:016x}".format(self.reg_csr.value["mip"], self.reg_csr.value["mie"]))
        # mideleg, medeleg
        print("mideleg: 0x{:016x} medeleg: 0x{:016x}".format(
            self.reg_csr.value["mideleg"], self.reg_csr.value["medeleg"]))
        # mtval, stval, mtvec, stvec
        print("mtval: 0x{:016x} stval: 0x{:016x} mtvec: 0x{:016x} stvec: 0x{:016x}".format(
            self.reg_csr.value["mtval"], self.reg_csr.value["stval"], self.reg_csr.value["mtvec"], self.reg_csr.value["stvec"]))
        # mscratch, sscratch
        print("mscratch: 0x{:016x} sscratch: 0x{:016x}".format(
            self.reg_csr.value["mscratch"], self.reg_csr.value["sscratch"]))

def snapshot_parser(snapshot_id):
    snapshot_file = os.path.join(BMCFUZZ_HOME, "SetInitValues", "csr_snapshot", f"{snapshot_id}")

    snapshot = Snapshot()

    with open(snapshot_file, 'rb') as f:
        # snapshot.cycleCnt = int.from_bytes(f.read(8), byteorder='little')
        for i in range(32):
            snapshot.reg_int.value[snapshot.reg_int.reg_name[i]] = int.from_bytes(f.read(8), byteorder='little')
        # for i in range(32):
        #     snapshot.reg_fp.value[snapshot.reg_fp.reg_name[i]] = int.from_bytes(f.read(8), byteorder='little')
        for i in range(18):
            snapshot.reg_csr.value[snapshot.reg_csr.reg_name[i]] = int.from_bytes(f.read(8), byteorder='little')
            # print(f"{snapshot.reg_csr.reg_name[i]}: {snapshot.reg_csr.value[snapshot.reg_csr.reg_name[i]]}")
        snapshot.pc = int.from_bytes(f.read(8), byteorder='little')
        # for i in range(4096):
        #     snapshot.csr_buffer.value[i] = int.from_bytes(f.read(8), byteorder='little')
    
    snapshot.output_int_regs()
    # snapshot.output_fp_regs()
    snapshot.output_csr_regs()

def cover_point_parser(cover_type):
    rtl_file = os.path.join(NOOP_HOME, "build", "rtl", "SimTop.sv")
    fir_file = os.path.join(NOOP_HOME, "build", "generated-src", "firrtl-cover.cpp")
    
    sva_covers = []
    fir_covers = []

    with open(rtl_file, 'r') as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            # cover_pattern = re.compile(r"cover\((.*)\);")
            # match = cover_pattern.search(line)
            # if match:
            #     # sva_covers.append(lines[index-1])
            #     if "1'h0" in lines[index]:
            #         continue
            #     sva_covers.append(lines[index])
            
            if r"cover(1'h1);" in line: # line cover
                if r"1'h1" in lines[index-1]:
                    continue
                pattern = re.compile(r"if \((.*)\) begin")
                match = pattern.search(lines[index-1])
                if match:
                    sva_covers.append(match.group(1)+"\n")
    
    # with open(fir_file, 'r') as f:
    #     lines = f.readlines()
    #     cover_begin = False
    #     for index, line in enumerate(lines):
    #         if cover_begin:
    #             if r"};" in line:
    #                 cover_begin = False
    #                 break
    #             pattern = re.compile(r"\"(.*)\.(.*)\",")
    #             match = pattern.search(line)
    #             if match:
    #                 fir_covers.append(match.group(2)+"\n")
    #             # fir_covers.append(line)
    #         if f"{cover_type}_NAMES[]" in line:
    #             cover_begin = True
    with open(rtl_file, 'r') as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            fir_pattern = re.compile(r"line_(.*)_valid_reg <= (.*);")
            match = fir_pattern.search(line)
            if match:
                fir_covers.append(match.group(2)+"\n")
    
    sva_output = os.path.join(NOOP_HOME, "tmp", "sva_cover.log")
    fir_output = os.path.join(NOOP_HOME, "tmp", "fir_cover.log")
    
    with open(sva_output, 'w') as f:
        f.writelines(sva_covers)
    
    with open(fir_output, 'w') as f:
        f.writelines(fir_covers)
    
    i, j = 0, 0
    diff = []
    for _ in range(len(sva_covers)):
        # if (i > 725 or j > 725) and (i < 737 or j < 737):
        #     print(i, ' ', j)
        if sva_covers[i] != fir_covers[j]:
            if fir_covers[j].startswith("eq") or fir_covers[j].startswith("not") or "==" in fir_covers[j]:
                i = i + 1
                j = j + 1
                continue
            if sva_covers[i] == fir_covers[j-1] and sva_covers[i-1] == sva_covers[i]:
                # print("======duplicate======")
                # print(f"sva[{i-1}]: {sva_covers[i-1]}")
                # print(f"sva[{i}]: {sva_covers}")
                # print(f"fir[{j-1}]: {fir_covers[j-1]}")
                # print(f"fir[{j}]: {fir_covers}")
                # print("===========================================")
                # diff.append("======duplicate======\n")
                # diff.append(f"sva[{i-1}]: {sva_covers[i-1]}\n")
                # diff.append(f"sva[{i}]: {sva_covers[i]}\n")
                # diff.append(f"fir[{j-1}]: {fir_covers[j-1]}\n")
                # diff.append(f"fir[{j}]: {fir_covers[j]}\n")
                # diff.append("===========================================\n")
                # print(i, ' ', j)
                diff.append(f"sva[{i}]: {sva_covers[i]}\n")
                i = i + 1
                continue
            else:
                # print(list(fir_covers[j]))
                if not sva_covers[i].endswith(fir_covers[j]):
                    # print(sva_covers[i].split(' '), '\n', fir_covers[j])
                    if fir_covers[j] == fir_covers:
                        print(i, ' ', j)
                        print(f"sva[{i}]: {sva_covers[i]}")
                        print(f"fir[{j}]: {fir_covers[j]}")
                        break
            #     diff.append("======diff======\n")
            #     diff.append(f"sva[{i}]: {sva_covers[i]}\n")
            #     diff.append(f"fir[{j}]: {fir_covers[j]}\n")
            #     diff.append("===========================================\n")
        i = i + 1
        j = j + 1
        # print(f"i: {i}, j: {j}")
    
    with open(os.path.join(NOOP_HOME, "tmp", "diff.log"), 'w') as f:
        f.writelines(diff)
    
    print("SVA cover points:", len(sva_covers))
    print("FIR cover points:", len(fir_covers))

def rtl_diff():
    diff_dir = os.path.join(NOOP_HOME, "tmp", "diff")
    os.makedirs(diff_dir, exist_ok=True)

    # 定义要比较的目录
    folder1 = "ccover/Formal/demo/rocket_toggle"
    folder2 = "build/rtl"
    diff_output_dir = "tmp/diff"

    # 确保diff输出目录存在
    os.makedirs(diff_output_dir, exist_ok=True)

    # 获取两个目录中的文件列表
    files1 = set(os.listdir(folder1))
    files2 = set(os.listdir(folder2))

    # 找到两个目录中都有的文件
    common_files = files1 & files2

    def compare_and_save_diff(file1, file2, output_file):
        with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
            
            diff = list(difflib.unified_diff(lines1, lines2, fromfile=file1, tofile=file2))
            
            if diff:
                with open(output_file, 'w', encoding='utf-8') as out:
                    out.writelines(diff)
                print(f"Differences found in {file1} and {file2}, saved to {output_file}")

    # 遍历同名文件并比较
    for filename in common_files:
        file1 = os.path.join(folder1, filename)
        file2 = os.path.join(folder2, filename)
        diff_file = os.path.join(diff_output_dir, f"{filename}.diff")
        
        # 只比较普通文件
        if os.path.isfile(file1) and os.path.isfile(file2):
            if not filecmp.cmp(file1, file2, shallow=False):
                compare_and_save_diff(file1, file2, diff_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--snapshot", "-s", type=int, help="Snapshot id")

    parser.add_argument("--cover", "-c", type=str, help="Cover type", default="toggle")

    args = parser.parse_args()
    
    # snapshot_parser(args.snapshot)

    # cover_point_parser(args.cover)

    rtl_diff()
import os
import sys
import csv
import time
import argparse

from datetime import datetime

from Coverage import Coverage
from Tools import *
from PointSelector import PointSelector
from Executor import Executor

NOOP_HOME = os.getenv("NOOP_HOME")
BMCFUZZ_HOME = os.getenv("BMCFUZZ_HOME")

class FuzzArgs:
    fuzzing = True
    cover_type = "toggle"
    max_runs = 0
    corpus_input = ""
    
    continue_on_errors = False
    insert_nop = False
    save_errors = False
    run_snapshot = False
    only_fuzz = False

    formal_cover_rate = -1.0

    # emu
    max_instr = 100
    max_cycle = 500
    begin_trace = 0

    dump_csr = False

    dump_wave = False
    wave_path = f"{NOOP_HOME}/tmp/run_wave.vcd"

    no_diff = False

    dump_footprints = False
    footprints_path = ""
    as_footprints = False

    snapshot_id = 0
    
    make_log_file = ""
    output_file = ""

    def make_fuzzer(self):
        make_command = f"cd {NOOP_HOME} && source env.sh && unset VERILATOR_ROOT && make clean"
        if self.run_snapshot:
            # make src
            make_command += f" && make emu REF=$(pwd)/ready-to-run/riscv64-spike-so BMCFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 -j16"
            make_command += f" > {self.make_log_file} 2>&1"
            make_command = "bash -c \'" + make_command + "\'"
            log_message(f"Make src command: {make_command}")
            return_code = run_command(make_command, shell=True)
            log_message(f"Make src return code: {return_code}")
            if return_code != 0:
                log_message("Make src failed!")
                sys.exit(1)

            # replace SimTop.sv
            log_message(f"Replace SimTop.sv")
            src_rtl = os.path.join(BMCFUZZ_HOME, "SetInitValues", "SimTop_init.sv")
            dst_rtl = os.path.join(NOOP_HOME, "build", "rtl", "SimTop.sv")

            if os.path.exists(dst_rtl):
                os.remove(dst_rtl)
            
            src_lines = []
            with open(src_rtl, mode='r', encoding='utf-8') as src_file:
                src_lines = src_file.readlines()
                for line in src_lines:
                    if line.startswith("assume"):
                        src_lines.remove(line)
            
            with open(dst_rtl, mode='w', encoding='utf-8') as dst_file:
                dst_file.writelines(src_lines)
            
            # replace MemRWHelper.v
            log_message(f"Replace MemRWHelper.v")
            src_rtl = os.path.join(BMCFUZZ_HOME, "SetInitValues", "MemRWHelper_difftest.v")
            dst_rtl = os.path.join(NOOP_HOME, "build", "rtl", "MemRWHelper.v")

            if os.path.exists(dst_rtl):
                os.remove(dst_rtl)
            shutil.copy(src_rtl, dst_rtl)

            # delete array_0_ext.v
            log_message(f"Delete array_0_ext.v")
            dst_rtl = os.path.join(NOOP_HOME, "build", "rtl", "array_0_ext.v")
            if os.path.exists(dst_rtl):
                os.remove(dst_rtl)

            # make fuzzer
            make_command = f"cd {NOOP_HOME} && source env.sh && unset VERILATOR_ROOT"
            make_command += f" && make fuzzer REF=$(pwd)/ready-to-run/riscv64-spike-so BMCFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 -j16"
            make_command += f" >> {self.make_log_file} 2>&1"
            make_command = "bash -c \'" + make_command + "\'"
            log_message(f"Make fuzzer command: {make_command}")
            return_code = run_command(make_command, shell=True)
            log_message(f"Make fuzzer return code: {return_code}")
            if return_code != 0:
                log_message("Make src failed!")
                sys.exit(1)
        else:
            make_command += f" && make emu REF=$(pwd)/ready-to-run/riscv64-spike-so BMCFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 EMU_SNAPSHOT=1 -j16"
            make_command += f" > {self.make_log_file} 2>&1"
            make_command = "bash -c \'" + make_command + "\'"
            log_message(f"Make fuzzer command: {make_command}")
            return_code = run_command(make_command, shell=True)
            log_message(f"Make fuzzer return code: {return_code}")
            if return_code != 0:
                log_message("Make src failed!")
                sys.exit(1)


    def generate_fuzz_command(self):
        fuzz_command = f"cd {NOOP_HOME} && source env.sh && build/fuzzer"

        if self.fuzzing:
            fuzz_command += " -f"
        fuzz_command += f" -c firrtl.{self.cover_type}"
        if self.max_runs > 0:
            fuzz_command += f" --max-runs {self.max_runs}"
        if self.corpus_input != "":
            fuzz_command += f" --corpus-input {self.corpus_input}"
        
        if self.continue_on_errors:
            fuzz_command += " --continue-on-errors"
        if self.insert_nop:
            fuzz_command += " --insert-nop"
        if self.save_errors:
            fuzz_command += " --save-errors"
        if self.only_fuzz:
            fuzz_command += " --only-fuzz"
        
        if self.formal_cover_rate > 0:
            fuzz_command += f" --formal-cover-rate {self.formal_cover_rate}"
        
        fuzz_command += " --"
        fuzz_command += f" -I {self.max_instr}"
        fuzz_command += f" -C {self.max_cycle}"
        # fuzz_command += f" -b {self.begin_trace}"

        if self.dump_csr:
            fuzz_command += " --dump-csr-change"

        if self.dump_wave:
            fuzz_command += " --dump-wave-full"
            fuzz_command += f" --wave-path {self.wave_path}"

        if self.run_snapshot:
            fuzz_command += " --run-snapshot"
            snapshot_file = os.path.join(BMCFUZZ_HOME, "SetInitValues", "csr_snapshot", f"{self.snapshot_id}")
            fuzz_command += f" --load-snapshot {snapshot_file}"

        if self.no_diff:
            fuzz_command += " --no-diff"

        if self.dump_footprints:
            fuzz_command += f" --dump-footprints {self.footprints_path}"
        if self.as_footprints:
            fuzz_command += " --as-footprints"

        if self.output_file != "":
            fuzz_command += f" > {self.output_file}"
            fuzz_command += " 2>&1"
        
        fuzz_command = "bash -c \'" + fuzz_command + "\'"
        log_message(f"Fuzz command: {fuzz_command}")
        return fuzz_command

class Scheduler:
    coverage = Coverage()

    point_selector = PointSelector()

    executor = Executor()

    points_name = []
    module_name = []
    point2module = []

    run_snapshot = False
    snapshot_id = 0

    cpu = ""
    cover_type = "toggle"

    solver_mode = "sat"

    def init(self, cpu, cover_type, run_snapshot=False):
        log_message("Scheduler init")
        log_message("cpu: " + cpu)
        log_message("cover_type: " + cover_type)
        log_message("run_snapshot: " + str(run_snapshot))
        log_message("solver_mode: " + self.solver_mode)

        self.run_snapshot = run_snapshot
        self.cpu = cpu
        self.cover_type = cover_type
        
        # 初始化Coverage和PointSelector
        log_message("Init Coverage and PointSelector")
        # False for BMCFuzz init
        cover_points_name = generate_rtl_files(False, cpu, cover_type, self.solver_mode)

        point_id = 0
        module_id = 0
        for module, point in cover_points_name:
            if module not in self.module_name:
                self.module_name.append(module)
                module_id += 1
            self.points_name.append(point)
            point_id += 1
            self.point2module.append(module_id-1)
        
        log_message(f"Module num: {module_id}")
        log_message(f"Point num: {point_id}")

        covered_num = 0
        cover_points = [0] * point_id
        self.coverage.init(covered_num, cover_points)

        self.point_selector.init(module_id, self.point2module)

        self.executor.init(cpu, run_snapshot, self.solver_mode)

        generate_empty_cover_points_file(point_id)
    
    def restart_init(self):
        self.point_selector.reset_uncovered_points(self.coverage.cover_points)
    
    def set_snapshot_id(self, snapshot_id):
        self.snapshot_id = snapshot_id
        snapshot_file = os.path.join(BMCFUZZ_HOME, "SetInitValues", "csr_snapshot", f"{snapshot_id}")
        self.executor.set_snapshot_id(snapshot_id, snapshot_file)

    def run_loop(self):
        loop_count = 0

        # make fuzzer
        fuzzer = FuzzArgs()
        fuzzer.cover_type = self.cover_type
        fuzzer.make_log_file = os.path.join(BMCFUZZ_HOME, 'Formal', 'logs', 'make_fuzzer.log')
        fuzzer.make_fuzzer()
        
        while(True):
            loop_count += 1
            log_message(f"Hybrid Loop {loop_count}")

            # 选点并执行formal任务
            if not self.run_formal():
                self.coverage.display_coverage()
                log_message("Hybrid Loop End:No more cover points!")
                break

            # 执行fuzz任务
            self.run_fuzz()

            # 获取fuzz结果并更新Coverage、PointSelector
            self.update_coverage()

            self.output_uncovered_points()
        
        self.display_coverage()
        self.output_uncovered_points()

    def run_formal(self, test_formal=False):
        if self.run_snapshot:
            generate_rtl_files(True, self.cpu, self.cover_type, self.solver_mode)
        if test_formal:
            self.point_selector.MAX_POINT_NUM = len(self.points_name)
        cover_points = self.point_selector.generate_cover_points()
        self.output_unselected_points()
        while(True):
            # 清理并重新生成cover points文件
            clean_cover_files()
            generate_sby_files(cover_points, self.cpu, self.solver_mode)

            # 执行cover任务
            snapshot_file = os.path.join(BMCFUZZ_HOME, 'SetInitValues', 'csr_snapshot', f"{self.snapshot_id}")
            cover_cases, time_cost = self.executor.run(cover_points)
            if len(cover_cases) > 0:
                log_message(f"发现新case: {cover_cases}")
                break
            else:
                log_message("未发现新case,重新选点")
                cover_points = self.point_selector.generate_cover_points()
                self.output_unselected_points()
            if len(cover_points) == 0:
                log_message("未发现新case,且无可选点")
                return False


        # 更新Coverage并生成cover_points文件
        self.coverage.generate_cover_file()
        if test_formal:
            self.coverage.update_formal(cover_cases)
        self.coverage.update_formal_cover_rate(len(cover_cases), time_cost)

        return True
    
    def run_fuzz(self):
        fuzz_log_dir = os.path.join(BMCFUZZ_HOME, 'Formal', 'logs', 'fuzz')
        make_log_file = os.path.join(fuzz_log_dir, f"make_fuzzer.log")
        fuzz_log_file = os.path.join(fuzz_log_dir, f"fuzz_{datetime.now().strftime('%Y-%m-%d_%H%M')}.log")

        fuzz_args = FuzzArgs()
        fuzz_args.cover_type = self.cover_type
        fuzz_args.corpus_input = os.getenv("CORPUS_DIR")

        fuzz_args.continue_on_errors = True
        fuzz_args.insert_nop = True
        fuzz_args.only_fuzz = True
        
        fuzz_args.formal_cover_rate = self.coverage.get_formal_cover_rate()

        fuzz_args.make_log_file = make_log_file
        fuzz_args.output_file = fuzz_log_file

        fuzz_args.as_footprints = True

        self.clean_fuzz_run()

        fuzz_command = fuzz_args.generate_fuzz_command()
        return_code = run_command(fuzz_command, shell=True)
        log_message(f"Fuzz return code: {return_code}")
    
    def run_snapshot_fuzz(self):
        # init fuzz log
        fuzz_log_dir = os.path.join(BMCFUZZ_HOME, 'Formal', 'logs', 'fuzz')
        make_log_file = os.path.join(fuzz_log_dir, f"make_fuzzer.log")
        fuzz_log_file = os.path.join(fuzz_log_dir, f"fuzz_{datetime.now().strftime('%Y-%m-%d_%H%M')}.log")

        # set fuzz args
        fuzz_args = FuzzArgs()
        fuzz_args.cover_type = self.cover_type
        fuzz_args.corpus_input = os.getenv("CORPUS_DIR")

        fuzz_args.continue_on_errors = True
        fuzz_args.save_errors = True
        fuzz_args.run_snapshot = True

        fuzz_args.formal_cover_rate = self.coverage.get_formal_cover_rate()

        fuzz_args.max_instr = 5000
        fuzz_args.max_cycle = 5000

        # fuzz_args.no_diff = True

        fuzz_args.dump_csr = True
        fuzz_args.dump_wave = True

        fuzz_args.snapshot_id = self.snapshot_id

        fuzz_args.as_footprints = True

        fuzz_args.make_log_file = make_log_file
        fuzz_args.output_file = fuzz_log_file

        # clean fuzz run dir
        # fuzz_args.make_fuzzer()
        self.clean_fuzz_run()

        # run fuzz
        fuzz_command = fuzz_args.generate_fuzz_command()
        return_code = run_command(fuzz_command, shell=True)
        log_message(f"Fuzz return code: {return_code}")
    
    def display_coverage(self):
        self.coverage.display_coverage()

    def output_uncovered_points(self, output_file=""):
        if output_file == "":
            output_file = os.path.join(BMCFUZZ_HOME, "Formal", "logs")
            output_file = os.path.join(output_file, f"uncovered_points.log")
        
        log_message(f"Output uncovered points to {output_file}")
        with open(output_file, mode='w', encoding='utf-8') as file:
            uncovered_points = self.coverage.get_uncovered_points()
            file.write(f"Uncovered points: {len(uncovered_points)}\n")
            for point in uncovered_points:
                module = self.point2module[point]
                point_name = self.points_name[point]
                module_name = self.module_name[module]
                file.write(f"{point}:{module_name}.{point_name}\n")
            file.write("\n")
    
    def output_unselected_points(self, output_file=""):
        if output_file == "":
            output_file = os.path.join(BMCFUZZ_HOME, "Formal", "logs")
            output_file = os.path.join(output_file, f"unselected_points.log")
        
        log_message(f"Output unselected points to {output_file}")
        with open(output_file, mode='w', encoding='utf-8') as file:
            unselected_points = self.point_selector.get_unselected_points()
            file.write(f"Unselected points: {len(unselected_points)}\n")
            for point in unselected_points:
                module = self.point2module[point]
                point_name = self.points_name[point]
                module_name = self.module_name[module]
                file.write(f"{point}:{module_name}.{point_name}\n")
            file.write("\n")
    
    def update_coverage(self):
        cover_points_path = os.getenv("COVER_POINTS_OUT") + "/cover_points.csv"
        covered_num = 0
        cover_points = []
        with open(cover_points_path, mode='r', newline='', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if int(row['Covered']) == 1:
                    covered_num += 1
                cover_points.append(int(row['Covered']))

        new_covered_points = self.coverage.update_fuzz(cover_points)
        fuzz_covered_num = len(new_covered_points)
        self.point_selector.update(self.coverage.cover_points)

        log_message(f"Fuzz covered num: {fuzz_covered_num}")

        covered_points_file = os.path.join(BMCFUZZ_HOME, "Formal", "logs")
        covered_points_file = os.path.join(covered_points_file, f"covered_points_{datetime.now().strftime('%Y-%m-%d_%H%M')}_.log")
        with open(covered_points_file, mode='w', encoding='utf-8') as file:
            file.write(f"Fuzz covered points: {fuzz_covered_num}\n")
            for point in new_covered_points:
                module = self.point2module[point]
                point_name = self.points_name[point]
                module_name = self.module_name[module]
                file.write(f"{point}:{module_name}.{point_name}\n")
            file.write("\n")

        # Coverage信息
        self.coverage.display_coverage()
    
    def clean_fuzz_run(self):
        fuzz_run_dir = os.getenv("NOOP_HOME") + "/tmp/fuzz_run"
        if os.path.exists(fuzz_run_dir):
            shutil.rmtree(fuzz_run_dir)
        os.mkdir(fuzz_run_dir)

def test_formal(args=None):
    clear_logs()
    log_init()

    log_message(f"run snapshot:{args.run_snapshot}")
    log_message(f"cpu:{args.cpu}")
    log_message(f"cover type:{args.cover_type}")

    scheduler = Scheduler()
    scheduler.init(args.cpu, args.cover_type, args.run_snapshot)
    all_points = [i for i in range(len(scheduler.points_name))]

    log_message(f"all_points_len: {len(all_points)}")
    log_message("Sleep 10 seconds for background running.")
    time.sleep(10)
    log_message("Start formal.")
    
    while(True):
        if not scheduler.run_formal(True):
            log_message("Exit: no more points to cover.")
            scheduler.display_coverage()
            break
        scheduler.display_coverage()

def run(args=None):
    # 初始化log
    clear_logs()
    log_init()

    log_message(f"run snapshot:{args.run_snapshot}")
    log_message(f"cpu:{args.cpu}")
    log_message(f"cover type:{args.cover_type}")
    
    # current_dir = os.path.dirname(os.path.realpath(__file__))
    # os.chdir(current_dir)

    scheduler = Scheduler()
    scheduler.init(args.cpu, args.cover_type, args.run_snapshot)

    log_message("Sleep 10 seconds for background running.")
    time.sleep(10)
    log_message("Start formal.")
    scheduler.run_loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--run_snapshot', '-r', action='store_true')
    parser.add_argument('--cpu', '-p', type=str, default="rocket")
    parser.add_argument('--cover_type', '-c', type=str, default="toggle")

    args = parser.parse_args()

    run(args)
    # generate_empty_cover_points_file()
    # test_fuzz()
    # test_formal(args)
    
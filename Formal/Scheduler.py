import os
import csv
import time
import argparse

from datetime import datetime

from Coverage import Coverage
from Pretreat import *
from PointSelector import PointSelector
from Executor import execute_cover_tasks, run_command

NOOP_HOME = os.getenv("NOOP_HOME")

class FuzzArgs:
    fuzzing = True
    cover_type = "toggle"
    max_runs = 0
    corpus_input = ""
    
    continue_on_errors = False
    insert_nop = False
    save_errors = False
    run_snapshot = False

    formal_cover_rate = -1.0

    # emu
    max_instr = 100
    max_cycle = 500
    begin_trace = 0

    no_diff = False
    
    make_log_file = ""
    output_file = ""

    def make_fuzzer(self):
        make_command = f"cd {NOOP_HOME} && source env.sh && unset VERILATOR_ROOT && make clean"
        if self.run_snapshot:
            # make src
            make_command += f" && make emu REF=$(pwd)/ready-to-run/riscv64-spike-so XFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 -j16"
            make_command += f" > {self.make_log_file} 2>&1"
            make_command = "bash -c \'" + make_command + "\'"
            log_message(f"Make src command: {make_command}")
            return_code = run_command(make_command, shell=True)
            log_message(f"Make src return code: {return_code}")

            # replace src
            src_rtl = os.path.join(NOOP_HOME, "ccover", "SetInitValues", "SimTop_init.sv")
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

            # make fuzzer
            make_command = f"cd {NOOP_HOME} && source env.sh && unset VERILATOR_ROOT"
            make_command += f" && make fuzzer REF=$(pwd)/ready-to-run/riscv64-spike-so XFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 -j16"
            make_command += f" >> {self.make_log_file} 2>&1"
            make_command = "bash -c \'" + make_command + "\'"
            log_message(f"Make fuzzer command: {make_command}")
            return_code = run_command(make_command, shell=True)
            log_message(f"Make fuzzer return code: {return_code}")
        else:
            make_command += f" && make emu REF=$(pwd)/ready-to-run/riscv64-spike-so XFUZZ=1 FIRRTL_COVER={self.cover_type} EMU_TRACE=1 -j16"
            make_command += f" > {self.make_log_file} 2>&1"
            make_command = "bash -c \'" + make_command + "\'"
            log_message(f"Make fuzzer command: {make_command}")
            return_code = run_command(make_command, shell=True)
            log_message(f"Make fuzzer return code: {return_code}")


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
        
        if self.formal_cover_rate > 0:
            fuzz_command += f" --formal-cover-rate {self.formal_cover_rate}"
        
        fuzz_command += " --"
        fuzz_command += f" -I {self.max_instr}"
        fuzz_command += f" -C {self.max_cycle}"
        fuzz_command += f" -b {self.begin_trace}"

        if self.run_snapshot:
            fuzz_command += " --run-snapshot"

        if self.no_diff:
            fuzz_command += " --no-diff"

        if self.output_file != "":
            fuzz_command += f" > {self.output_file}"
            fuzz_command += " 2>&1"
        
        fuzz_command = "bash -c \'" + fuzz_command + "\'"
        log_message(f"Fuzz command: {fuzz_command}")
        return fuzz_command

class Scheduler:
    coverage = Coverage()

    point_selector = PointSelector()

    pre_fuzz_covered_num = 0

    points_name = []
    module_name = []
    point2module = []

    run_snapshot = False

    cover_type = "toggle"

    def init(self, run_snapshot=False, cover_type="toggle"):
        if run_snapshot:
            clear_logs()
        log_message("Scheduler init")

        self.run_snapshot = run_snapshot
        self.cover_type = cover_type
        
        # 初始化Coverage和PointSelector
        log_message("Init Coverage and PointSelector")
        # False for snapshot fuzz init
        cover_points_name = generate_rtl_files(False, cover_type)

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

        generate_empty_cover_points_file(point_id)
    
    def restart_init(self):
        self.point_selector.reset_uncovered_points(self.coverage.cover_points)
    
    def run_loop(self):
        loop_count = 0
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

    def run_formal(self, test_formal=False):
        if self.run_snapshot:
            generate_rtl_files(True, self.cover_type)
        if test_formal:
            self.point_selector.MAX_POINT_NUM = len(self.points_name)
        cover_points = self.point_selector.generate_cover_points()
        while(True):
            # 清理并重新生成cover points文件
            clean_cover_files()
            generate_sby_files(cover_points)

            # 执行cover任务
            cover_cases, time_cost = execute_cover_tasks(cover_points)
            
            if len(cover_cases) > 0:
                log_message(f"发现新case: {cover_cases}")
                break
            else:
                log_message("未发现新case,重新选点")
                cover_points = self.point_selector.generate_cover_points()
            
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
        formal_cover_rate = self.coverage.get_formal_cover_rate()
        NOOP_HOME = os.getenv("NOOP_HOME")
        FUZZ_LOG = os.getenv("FUZZ_LOG")
        fuzz_log_file = os.path.join(FUZZ_LOG, f"fuzz_{datetime.now().strftime('%Y-%m-%d_%H%M')}.log")
        fuzz_command = f"bash -c 'cd {NOOP_HOME} && source {NOOP_HOME}/env.sh && \
                        {NOOP_HOME}/build/fuzzer -f --formal-cover-rate {formal_cover_rate} --continue-on-errors \
                        --corpus-input $CORPUS_DIR -c firrtl.toggle --insert-nop -- -I 100 -C 500 -b 0 \
                        > {fuzz_log_file} 2>&1'"
        return_code = run_command(fuzz_command, shell=True)
        log_message(f"Fuzz return code: {return_code}")
    
    def run_snapshot_fuzz(self):
        # init fuzz log
        fuzz_log_dir = os.path.join(NOOP_HOME, 'ccover', 'Formal', 'logs', 'fuzz')
        make_log_file = os.path.join(fuzz_log_dir, f"make_{datetime.now().strftime('%Y-%m-%d_%H%M')}.log")
        fuzz_log_file = os.path.join(fuzz_log_dir, f"fuzz_{datetime.now().strftime('%Y-%m-%d_%H%M')}.log")

        # set fuzz args
        fuzz_args = FuzzArgs()
        fuzz_args.cover_type = self.cover_type
        fuzz_args.corpus_input = os.getenv("CORPUS_DIR")

        fuzz_args.continue_on_errors = True
        fuzz_args.save_errors = True
        fuzz_args.run_snapshot = True

        fuzz_args.formal_cover_rate = self.coverage.get_formal_cover_rate()

        fuzz_args.max_instr = 300
        fuzz_args.max_cycle = 1000

        fuzz_args.no_diff = True

        fuzz_args.make_log_file = make_log_file
        fuzz_args.output_file = fuzz_log_file

        fuzz_command = fuzz_args.generate_fuzz_command()

        # make fuzzer and clean fuzz run dir
        fuzz_args.make_fuzzer()
        self.clean_fuzz_run()

        # run fuzz
        return_code = run_command(fuzz_command, shell=True)
        log_message(f"Fuzz return code: {return_code}")
    
    def display_coverage(self):
        self.coverage.display_coverage()
    
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

        self.coverage.update_fuzz(cover_points)
        self.point_selector.update(self.coverage.cover_points)

        fuzz_covered_num = covered_num - self.pre_fuzz_covered_num
        self.pre_fuzz_covered_num = covered_num

        log_message(f"Fuzz covered num: {fuzz_covered_num}")

        # Coverage信息
        self.coverage.display_coverage()
    
    def clean_fuzz_run(self):
        fuzz_run_dir = os.getenv("NOOP_HOME") + "/tmp/fuzz_run"
        if os.path.exists(fuzz_run_dir):
            shutil.rmtree(fuzz_run_dir)
        os.mkdir(fuzz_run_dir)


def run(args=None):
    # 初始化log
    clear_logs()
    log_init()

    # argparse
    run_snapshot = False
    if args.run_snapshot:
        run_snapshot = True
    cover_type = args.cover_type

    log_message(f"run snapshot:{run_snapshot}")
    log_message(f"cover type:{cover_type}")
    
    # current_dir = os.path.dirname(os.path.realpath(__file__))
    # os.chdir(current_dir)

    scheduler = Scheduler()
    scheduler.init(run_snapshot, cover_type)

    log_message("Sleep 10 seconds for background running.")
    time.sleep(10)
    log_message("Start formal.")
    scheduler.run_loop()

def test_formal(args=None):
    clear_logs()
    log_init()

    run_snapshot = False
    if args.run_snapshot:
        run_snapshot = True
    cover_type = args.cover_type

    log_message(f"run snapshot:{run_snapshot}")
    log_message(f"cover type:{cover_type}")

    scheduler = Scheduler()
    scheduler.init(run_snapshot, cover_type)
    all_points = [i for i in range(len(scheduler.points_name))]
    # hexbin_dir = os.getenv("COVER_POINTS_OUT") + "/hexbin"
    # with os.scandir(hexbin_dir) as entries:
    #     for entry in entries:
    #         if entry.name.endswith(".bin"):
    #             cover_id = int(entry.name.split(".")[0].split("_")[1])
    #             log_message(f"cover_id: {cover_id}")
    #             if cover_id in all_points:
    #                 all_points.remove(cover_id)

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

def test_fuzz(args=None):
    clear_logs()
    log_init()

    run_snapshot = False
    if args.run_snapshot:
        run_snapshot = True
    cover_type = args.cover_type

    log_message(f"run snapshot:{run_snapshot}")
    log_message(f"cover type:{cover_type}")

    scheduler = Scheduler()
    scheduler.run_fuzz(0.01)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--run_snapshot', '-r', action='store_true')
    parser.add_argument('--cover_type', '-c', type=str, default="toggle")
    parser.add_argument('--test_formal', '-t', action='store_true')

    args = parser.parse_args()

    if args.test_formal:
        test_formal(args)
    else:
        run(args)
    # generate_empty_cover_points_file()
    # test_fuzz()
    # test_formal(args)
    
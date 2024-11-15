import os
import csv
import time
import argparse

from datetime import datetime

from Coverage import Coverage
from Pretreat import *
from PointSelector import PointSelector
from Executor import execute_cover_tasks, run_command

class Scheduler:
    coverage = Coverage()

    point_selector = PointSelector()

    points_name = []
    module_name = []
    point2module = []

    run_snapshot = False

    cover_type = "toggle"

    def init(self, run_snapshot=False, cover_type="toggle"):
        log_message("Scheduler init")

        self.run_snapshot = run_snapshot
        self.cover_type = cover_type
        
        # 初始化Coverage和PointSelector
        log_message("Init Coverage and PointSelector")
        cover_points_name = generate_rtl_files(run_snapshot, cover_type)

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
    
    def run_loop(self, max_iter, target_coverage=0.9):
        pre_fuzz_covered_num = 0
        for i in range(max_iter):
            log_message(f"Loop {i+1}")

            # 选点并执行formal任务
            cover_points = self.point_selector.generate_cover_points()
            if not self.run_formal(cover_points):
                log_message("Exit:No more cover points!")
                break

            # 执行fuzz任务
            self.run_fuzz(self.coverage.get_formal_cover_rate())

            # 获取fuzz结果并更新Coverage、PointSelector
            cover_points_path = os.getenv("COVER_POINTS_OUT") + "/cover_points.csv"
            covered_num = 0
            cover_points = []
            with open(cover_points_path, mode='r', newline='', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    if int(row['Covered']) == 1:
                        covered_num += 1
                    cover_points.append(int(row['Covered']))
            
            fuzz_covered_num = covered_num - pre_fuzz_covered_num
            pre_fuzz_covered_num = covered_num
            log_message(f"Fuzz covered num: {fuzz_covered_num}")
            self.coverage.update_fuzz(cover_points)
            self.point_selector.update(self.coverage.cover_points)

            # Coverage信息
            log_message(f"Covered: {covered_num}/{len(cover_points)}")
            log_message(f"Coverage: {self.coverage.get_coverage()*100:.2f}%")

            if self.coverage.get_coverage() >= target_coverage:
                log_message("Exit:Coverage reached target!")
                break

    def run_formal(self, cover_points):
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
        # self.coverage.update_formal(cover_cases)
        self.coverage.update_formal_cover_rate(len(cover_cases), time_cost)

        return True
    
    def run_fuzz(self, formal_cover_rate):
        NOOP_HOME = os.getenv("NOOP_HOME")
        FUZZ_LOG = os.getenv("FUZZ_LOG")
        fuzz_log_file = os.path.join(FUZZ_LOG, f"fuzz_{datetime.now().strftime('%Y-%m-%d_%H%M')}.log")
        fuzz_command = f"bash -c 'cd {NOOP_HOME} && source {NOOP_HOME}/env.sh && \
                        {NOOP_HOME}/build/fuzzer -f --formal-cover-rate {formal_cover_rate} --continue-on-errors \
                        --corpus-input $CORPUS_DIR --cover-points-output $COVER_POINTS_OUT -c firrtl.toggle --insert-nop -- -I 100 -C 500 -e 0 \
                        > {fuzz_log_file} 2>&1'"
        return_code = run_command(fuzz_command, shell=True)
        log_message(f"Fuzz return code: {return_code}")


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
    scheduler.run_loop(500)

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
    scheduler.run_formal(all_points)

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

    args = parser.parse_args()

    run(args)
    # generate_empty_cover_points_file()
    # test_fuzz()
    # test_formal(args)
    
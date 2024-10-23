import os
import csv
import shutil
import argparse
import subprocess
import logging

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

    def init(self):
        log_message("Scheduler init")
        
        # 初始化Coverage和PointSelector
        log_message("Init Coverage and PointSelector")
        cover_points_name = generate_rtl_files()

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
    
    def run_loop(self, max_iter):
        for i in range(max_iter):
            log_message(f"Loop {i+1}")
            # 选点并执行formal任务
            cover_points = self.point_selector.generate_cover_points()
            self.run_formal(cover_points)

            # 执行fuzz任务
            # self.run_fuzz(self.coverage.get_formal_cover_rate())
            self.run_fuzz(1000.0)

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
            
            fuzz_covered_num = covered_num - self.coverage.get_covered_num()
            log_message(f"Fuzz covered num: {fuzz_covered_num}")
            self.coverage.update_fuzz(covered_num, cover_points)
            self.point_selector.update(cover_points, self.point2module)

            # Coverage信息
            log_message(f"Covered: {covered_num}/{len(cover_points)}")
            log_message(f"Coverage: {self.coverage.get_coverage()*100:.2f}%")

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
                self.point_selector.remove_points(cover_points, self.point2module)
                cover_points = self.point_selector.generate_cover_points()

        # 更新Coverage并生成cover_points文件
        self.coverage.update_formal(cover_cases)
        self.coverage.update_formal_cover_rate(len(cover_cases), time_cost)
        self.coverage.generate_cover_file()
    
    def run_fuzz(self, formal_cover_rate):
        NOOP_HOME = os.getenv("NOOP_HOME")
        FUZZ_LOG = os.getenv("FUZZ_LOG")
        fuzz_log_file = os.path.join(FUZZ_LOG, f"fuzz_{datetime.now().strftime('%Y-%m-%d_%H%M')}.log")
        fuzz_command = f"bash -c 'cd {NOOP_HOME} && source {NOOP_HOME}/env.sh && \
                        {NOOP_HOME}/build/fuzzer -f --formal-cover-rate {formal_cover_rate} \
                        --corpus-input $CORPUS_DIR --cover-points-output $COVER_POINTS_OUT -c firrtl.toggle -- --no-diff -I 100 -e 0 \
                        > {fuzz_log_file} 2>&1'"
        return_code = run_command(fuzz_command, shell=True)
        log_message(f"Fuzz return code: {return_code}")


def run(args = None):
    # 初始化log
    clear_logs()
    log_init()

    # current_dir = os.path.dirname(os.path.realpath(__file__))
    # os.chdir(current_dir)

    scheduler = Scheduler()
    scheduler.init()

    scheduler.run_loop(1)

def test_fuzz():
    clear_logs()
    log_init()
    scheduler = Scheduler()
    scheduler.run_fuzz(1000)

if __name__ == "__main__":
    # # 初始化Coverage对象
    # coverage = Coverage()
    
    # # 清理并重新生成cover points文件
    # clean_cover_files()
    # cover_points = generate_rtl_files()
    # coverage.init_cover_points(cover_points)
    # coverage.generate_cover_file()
    
    # # 生成样例sby文件
    # sample_cover_points = [3933, 4389, 4390, 4392]
    # generate_sby_files(sample_cover_points)

    run()
    # generate_empty_cover_points_file()
    # test_fuzz()
    
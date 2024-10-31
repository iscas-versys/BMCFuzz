import os
import csv

from Pretreat import *

class Coverage:
    covered_num = 0
    cover_points = []

    # formal cover rate
    max_window_size = 10
    window_count = 0
    formal_cover_rate = 0

    def init(self, covered_num, cover_points):
        self.cover_points = cover_points
        self.covered_num = covered_num

    def update_formal(self, cover_cases):
        self.covered_num += len(cover_cases)
        for cover in cover_cases:
            self.cover_points[cover] = 1
            self.covered_num += 1

    def update_fuzz(self, cover_points):
        for index, cover in enumerate(cover_points):
            if cover and not self.cover_points[index]:
                self.covered_num += 1
                self.cover_points[index] = 1
    
    def update_formal_cover_rate(self, covered_num, time_cost):
        covered_rate = covered_num / time_cost
        if self.window_count < self.max_window_size:
            self.window_count += 1
        self.formal_cover_rate = (self.formal_cover_rate * (self.window_count - 1) + covered_rate) / self.window_count
        log_message(f"Formal cover rate: {self.formal_cover_rate}")
    
    def get_formal_cover_rate(self):
        return self.formal_cover_rate
    
    def get_covered_num(self):
        return self.covered_num
    
    def get_coverage(self):
        return self.covered_num / len(self.cover_points)

    def generate_cover_file(self):
        # 获取环境变量
        cover_points_out = str(os.getenv("COVER_POINTS_OUT"))
        cover_points_file_path = cover_points_out + "/cover_points.csv"

        # 检查文件是否存在, 如果存在则删除
        if os.path.exists(cover_points_file_path):
            os.remove(cover_points_file_path)

        with open(cover_points_file_path, mode='w', newline='', encoding='utf-8') as file:
            field_name = ['Index', 'Covered']
            csv_writer = csv.DictWriter(file, fieldnames=field_name)
            csv_writer.writeheader()
            for i in range(len(self.cover_points)):
                csv_writer.writerow({'Index': i, 'Covered': self.cover_points[i]})

if __name__ == "__main__":
    # generate_empty_cover_points_file()
    # 初始化Coverage对象
    coverage = Coverage()
    
    # 清理并重新生成cover points文件
    clean_cover_files()
    cover_points = generate_rtl_files()
    coverage.init(cover_points)
    coverage.generate_cover_file()

    # 生成样例sby文件
    sample_cover_points = [3933, 4389, 4390, 4392]
    generate_sby_files(sample_cover_points)
    

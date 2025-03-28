import random

from Tools import *

class PointSelector:
    MAX_POINT_NUM = 200

    uncovered_points_num = 0
    module_contain_points = []
    point2module = []
    
    def init(self, module_num, point2module):
        self.point2module = point2module
        self.module_contain_points = [set() for _ in range(module_num)]
        self.uncovered_points_num = len(point2module)
        for point, module in enumerate(point2module):
            self.module_contain_points[module].add(point)
    
    def reset_uncovered_points(self, cover_points):
        self.uncovered_points_num = 0
        for point, covered in enumerate(cover_points):
            module = self.point2module[point]
            if covered == 0:
                self.uncovered_points_num += 1
                self.module_contain_points[module].add(point)

    def update(self, cover_points):
        for point, covered in enumerate(cover_points):
            module = self.point2module[point]
            if covered == 1 and point in self.module_contain_points[module]:
                self.module_contain_points[module].remove(point)
                self.uncovered_points_num -= 1
    
    def remove_points(self, points):
        self.uncovered_points_num -= len(points)
        for point in points:
            module = self.point2module[point]
            if point in self.module_contain_points[module]:
                self.module_contain_points[module].remove(point)
                if len(self.module_contain_points[module]) == 0:
                    log_message("Module %d is empty" % module)
    
    def generate_cover_points(self):
        total_select_num = 0
        total_select_points = []
        
        while total_select_num < self.MAX_POINT_NUM and self.uncovered_points_num > 0:
            max_uncovered_module = 0
            max_uncovered_points = []
            for module, points in enumerate(self.module_contain_points):
                if len(points) > len(max_uncovered_points):
                    max_uncovered_module = module
                    max_uncovered_points = list(points)
        
            select_num = min(len(max_uncovered_points), self.MAX_POINT_NUM-total_select_num)
            select_points = random.sample(max_uncovered_points, select_num)
            self.remove_points(select_points)

            # debug
            log_message("Select %d points from module %d(%d)" % (select_num, max_uncovered_module, len(max_uncovered_points)))
            log_message("Selected points: %s" % str(select_points))
            log_message("Unselected points num: %d" % self.uncovered_points_num)

            total_select_num += select_num
            total_select_points += select_points
        
        log_message("Total select %d points" % total_select_num)

        return total_select_points
    

if __name__ == "__main__":
    clear_logs()
    log_init()
    point2module = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2]
    module_num = 3
    point_selector = PointSelector()
    point_selector.init(module_num, point2module)
    point_selector.generate_cover_points()
    point_selector.generate_cover_points()
    point_selector.generate_cover_points()


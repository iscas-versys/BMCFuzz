import random

from Pretreat import *

class PointSelector:
    MAX_POINT_NUM = 10
    module_contain_points = []
    point2module = []
    
    def init(self, module_num, point2module):
        self.point2module = point2module
        self.module_contain_points = [set() for _ in range(module_num)]
        for point, module in enumerate(point2module):
            self.module_contain_points[module].add(point)

    def update(self, cover_points):
        for point, covered in enumerate(cover_points):
            module = self.point2module[point]
            if covered == 1 and point in self.module_contain_points[module]:
                self.module_contain_points[module].remove(point)
    
    def remove_points(self, points):
        for point in points:
            module = self.point2module[point]
            if point in self.module_contain_points[module]:
                self.module_contain_points[module].remove(point)
    
    def generate_cover_points(self):
        max_uncovered_module = 0
        max_uncovered_points = []
        for module, points in enumerate(self.module_contain_points):
            if len(points) > len(max_uncovered_points):
                max_uncovered_module = module
                max_uncovered_points = list(points)
        
        select_num = min(len(max_uncovered_points), self.MAX_POINT_NUM)
        select_points = random.sample(max_uncovered_points, select_num)

        self.remove_points(select_points)

        # debug
        log_message("Select %d points from module %d(%d)" % (select_num, max_uncovered_module, len(max_uncovered_points)))
        log_message("Selected points: %s" % str(select_points))

        return select_points


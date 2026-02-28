"""
Point selector module for formal verification
"""

import random
from typing import List, Set, Optional
import os
import sys

from utils.logger import BMCFuzzLogger, logger
from core.config import Config

class PointSelector:
    """
    Point selector for coverage-guided formal verification
    
    Selects uncovered points from modules to guide the formal verification process.
    """
    
    def __init__(self):
        """Initialize PointSelector"""
        self.max_point_num = Config.POINT_SELECTOR_MAX_POINT_NUM
        self.uncovered_points_num: int = 0
        self.module_contain_points: List[Set[int]] = []
        self.point2module: List[int] = []
        self.logger = BMCFuzzLogger.get_logger("PointSelector")
    
    def init(self, module_num: int, point2module: List[int]) -> None:
        """
        Initialize point selector with module and point mapping
        
        Args:
            module_num: Number of modules
            point2module: List mapping each point to its module index
        """
        self.point2module = point2module
        self.module_contain_points = [set() for _ in range(module_num)]
        self.uncovered_points_num = len(point2module)
        
        for point, module in enumerate(point2module):
            self.module_contain_points[module].add(point)
    
    def reset_uncovered_points(self, cover_points: List[int]) -> None:
        """
        Reset uncovered points based on coverage status
        
        Args:
            cover_points: List indicating which points are covered (1) or not (0)
        """
        self.logger.info("Reset uncovered points")
        self.uncovered_points_num = 0
        
        for point, covered in enumerate(cover_points):
            module = self.point2module[point]
            if covered == 0:
                self.uncovered_points_num += 1
                self.module_contain_points[module].add(point)
    
    def update(self, cover_points: List[int]) -> None:
        """
        Update uncovered points based on new coverage information
        
        Args:
            cover_points: List indicating which points are covered (1) or not (0)
        """
        for point, covered in enumerate(cover_points):
            module = self.point2module[point]
            if covered == 1 and point in self.module_contain_points[module]:
                self.module_contain_points[module].remove(point)
                self.uncovered_points_num -= 1
    
    def remove_points(self, points: List[int]) -> None:
        """
        Remove specified points from uncovered sets
        
        Args:
            points: List of point indices to remove
        """
        self.uncovered_points_num -= len(points)
        
        for point in points:
            module = self.point2module[point]
            if point in self.module_contain_points[module]:
                self.module_contain_points[module].remove(point)
                if len(self.module_contain_points[module]) == 0:
                    self.logger.warning(f"Module {module} is empty")
    
    def get_unselected_points(self) -> List[int]:
        """
        Get all unselected points across all modules
        
        Returns:
            List of unselected point indices
        """
        unselected_points = []
        
        for points in self.module_contain_points:
            if len(points) > 0:
                unselected_points += list(points)
        
        return unselected_points
    
    def generate_cover_points(self) -> List[int]:
        """
        Generate cover points by selecting uncovered points from modules
        
        Selects up to max_point_num points, prioritizing modules with
        most uncovered points.
        
        Returns:
            Sorted list of selected point indices
        """
        total_select_num = 0
        total_select_points = []
        
        while total_select_num < self.max_point_num and self.uncovered_points_num > 0:
            max_uncovered_module = 0
            max_uncovered_points = []
            
            for module, points in enumerate(self.module_contain_points):
                if len(points) > len(max_uncovered_points):
                    max_uncovered_module = module
                    max_uncovered_points = list(points)
        
            select_num = min(len(max_uncovered_points), self.max_point_num - total_select_num)
            select_points = random.sample(max_uncovered_points, select_num)
            select_points.sort()
            self.remove_points(select_points)

            self.logger.info(f"Select {select_num} points from module {max_uncovered_module} ({len(max_uncovered_points)})")
            self.logger.debug(f"Selected points: {select_points}")
            self.logger.info(f"Unselected points num: {self.uncovered_points_num}")

            total_select_num += select_num
            total_select_points += select_points
        
        self.logger.info(f"Total select {total_select_num} points")

        total_select_points.sort()
        return total_select_points

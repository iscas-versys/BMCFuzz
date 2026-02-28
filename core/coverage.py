"""
Coverage management module for BMCFuzz
"""

import os
import sys
import csv
from typing import List, Tuple

from utils.logger import BMCFuzzLogger, logger
from core.config import Config


class CoverageManager:
    """Coverage tracking and management"""
    
    def __init__(self, total_points: int):
        """
        Args:
            total_points: Total number of coverage points
        """
        self.total_points = total_points
        self.covered_num = 0
        self.cover_points = [0] * total_points
        self.coverage_csv_file = Config.COVERAGE_CSV_FILENAME
        
        # Formal verification
        # self.max_window_size = COVERAGE_MAX_WINDOW_SIZE
        self.window_count = 0
        self.formal_cover_rate = 0.0
        
        self.logger = BMCFuzzLogger.get_logger("Coverage")
        
        self.logger.info(
            f"Coverage manager initialized, total points: {total_points}"
        )
    
    def init(self, covered_num: int, cover_points: List[int]):
        """
        Initialize with existing data (backward compatible)
        
        Args:
            covered_num: Number of covered points
            cover_points: Coverage point status list
        """
        self.covered_num = covered_num
        self.cover_points = cover_points
        self.logger.info(
            f"Initialized with existing data: {covered_num}/{len(cover_points)}"
        )
    
    def update_formal(self, cover_cases: List[int]):
        """
        Update formal verification coverage
        
        Args:
            cover_cases: List of newly covered point IDs
        """
        self.covered_num += len(cover_cases)
        for cover in cover_cases:
            if cover < len(self.cover_points):
                self.cover_points[cover] = 1
            else:
                self.logger.warning(f"Point ID {cover} out of range, ignored")
        
        self.logger.info(
            f"Formal update: {len(cover_cases)} new points, "
            f"total: {self.covered_num}/{self.total_points}"
        )
    
    def update_fuzz(self, cover_points: List[int]) -> List[int]:
        """
        Update fuzzing coverage
        
        Args:
            cover_points: Coverage point status list
        
        Returns:
            List of newly covered point IDs
        """
        new_covered_points = []
        
        for index, cover in enumerate(cover_points):
            if cover and not self.cover_points[index]:
                self.covered_num += 1
                self.cover_points[index] = 1
                new_covered_points.append(index)
        
        if new_covered_points:
            self.logger.info(
                f"Fuzz update: {len(new_covered_points)} new points, "
                f"total: {self.covered_num}/{self.total_points}"
            )
            # self.logger.debug(f"New covered points: {new_covered_points}")
        
        return new_covered_points
    
    def update_formal_cover_rate(self, covered_num: int, time_cost: float):
        """
        Update formal verification coverage rate
        
        Args:
            covered_num: Number of points covered
            time_cost: Time spent
        """
        if time_cost > 0:
            covered_rate = covered_num / time_cost
            self.window_count += 1
            
            self.formal_cover_rate = (
                self.formal_cover_rate * (self.window_count - 1) + covered_rate
            ) / self.window_count
            
            self.logger.debug(
                f"Formal cover rate: {self.formal_cover_rate:.4f}, "
                f"window: {self.window_count}"
            )
    
    def get_formal_cover_rate(self) -> float:
        """Get formal verification coverage rate"""
        return self.formal_cover_rate
    
    def get_covered_num(self) -> int:
        """Get number of covered points"""
        return self.covered_num
    
    def get_coverage(self) -> float:
        """Calculate coverage percentage (0.0-1.0)"""
        if self.total_points == 0:
            self.logger.warning("Total points is 0, returning 0%")
            return 0.0
        return self.covered_num / self.total_points
    
    def get_uncovered_points(self) -> List[int]:
        """Get list of uncovered point IDs"""
        uncovered_points = [
            index for index, cover in enumerate(self.cover_points)
            if not cover
        ]
        self.logger.debug(
            f"Uncovered points: {len(uncovered_points)}/{self.total_points}"
        )
        return uncovered_points
    
    def display_coverage(self):
        """Display current coverage info"""
        coverage_percentage = self.get_coverage() * 100
        self.logger.info(
            f"Coverage: {self.covered_num}/{self.total_points} "
            f"({coverage_percentage:.2f}%)"
        )
        print(
            f"Coverage: {self.covered_num}/{self.total_points} "
            f"({coverage_percentage:.2f}%)"
        )
    
    def generate_cover_file(self):
        """
        Generate coverage CSV file
        
        Args:
            output_dir: Output directory path
        """
        cover_points_file_path = Config.COVERAGE_CSV_FILENAME
        
        if os.path.exists(cover_points_file_path):
            os.remove(cover_points_file_path)
        
        try:
            with open(
                cover_points_file_path,
                mode='w',
                newline='',
                encoding='utf-8'
            ) as file:
                field_name = ['Index', 'Covered']
                csv_writer = csv.DictWriter(file, fieldnames=field_name)
                csv_writer.writeheader()
                
                for i in range(len(self.cover_points)):
                    csv_writer.writerow({
                        'Index': i,
                        'Covered': self.cover_points[i]
                    })
            
            self.logger.info(f"Coverage file generated: {cover_points_file_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to generate coverage file: {e}")
            raise


Coverage = CoverageManager

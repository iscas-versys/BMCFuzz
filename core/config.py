"""
Configuration management for BMCFuzz
"""

import os
import sys

# Get BMCFUZZ_HOME from environment or use current directory
BMCFUZZ_HOME = os.environ.get("BMCFUZZ_HOME", os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import logger


class Config:
    """
    Central configuration for BMCFuzz
    
    Lightweight configuration class containing key parameters
    for different components.
    """
    
    # Project Paths (relative to BMCFUZZ_HOME)
    BMCFUZZ_HOME: str = BMCFUZZ_HOME

    # Formal
    POINT_SELECTOR_MAX_POINT_NUM: int = 5
    FORMAL_MAX_WORKERS: int = 5
    SBY_PATH: str = os.path.join(BMCFUZZ_HOME, "sby", "sbysrc", "sby.py")
    OSS_CAD_SUITE_ENV: str = os.environ.get(
        "OSS_CAD_SUITE_ENV",
        os.path.join(
            os.path.dirname(BMCFUZZ_HOME),
            "oss-cad-suite",
            "environment"
        )
    )
    RIC3_PATH: str = os.environ.get(
        "RIC3_PATH",
        os.path.join(BMCFUZZ_HOME, "formal", "bin", "rIC3")
    )
    FORMAL_RUN_DIR: str = os.path.join(BMCFUZZ_HOME, "formal_run")

    # Fuzzer Paths
    FUZZER_INIT: bool = False
    FUZZER_INIT_RUNS: int = 10
    INIT_CORPUS_DIR: str = os.path.join(BMCFUZZ_HOME, "corpus", "linearized", "riscv-all")
    CORPUS_DIR: str = os.path.join(FORMAL_RUN_DIR, "corpus")

    # Initialization
    SNAPSHOT_DIR: str = os.path.join(BMCFUZZ_HOME, "snapshots")

    # Logging
    LOG_DIR: str = os.path.join(BMCFUZZ_HOME, "logs")
    
    # Coverage Manager Configuration
    # COVERAGE_MAX_WINDOW_SIZE: int = 10
    COVERAGE_CSV_FILENAME: str = os.path.join(BMCFUZZ_HOME, "formal_run", "cover_points.csv")
    
    def __init__(self):
        """Initialize configuration"""
        logger.debug(f"BMCFUZZ_HOME: {self.BMCFUZZ_HOME}")
        logger.debug("Configuration initialized")
    
    @classmethod
    def display(cls):
        """Display current configuration"""
        logger.info("=== BMCFuzz Configuration ===")
        logger.info(f"BMCFUZZ_HOME: {cls.BMCFUZZ_HOME}")
        logger.info(f"SBY_PATH: {cls.SBY_PATH}")
        logger.info(f"OSS_CAD_SUITE_ENV: {cls.OSS_CAD_SUITE_ENV}")
        logger.info(f"RIC3_PATH: {cls.RIC3_PATH}")
        logger.info(f"FORMAL_RUN_DIR: {cls.FORMAL_RUN_DIR}")
        logger.info(f"LOG_DIR: {cls.LOG_DIR}")
        logger.info(f"Point Selector - Max Point Num: {cls.POINT_SELECTOR_MAX_POINT_NUM}")
        logger.info(f"Coverage - CSV Filename: {cls.COVERAGE_CSV_FILENAME}")
        logger.info(f"Formal - Max Workers: {cls.FORMAL_MAX_WORKERS}")
        logger.info("==============================")


# Global configuration instance
config = Config()


if __name__ == "__main__":
    from utils.logger import log_init
    
    log_init(prefix="config_test")
    
    Config.display()
    logger.info(f"Accessing config: {Config.POINT_SELECTOR_MAX_POINT_NUM}")
    logger.info("Configuration test completed!")
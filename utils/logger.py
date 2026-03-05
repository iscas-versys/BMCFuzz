"""
Unified logging system for BMCFuzz
"""

import os
import shutil
import logging
from datetime import datetime
from typing import Optional


class BMCFuzzLogger:
    """Unified logging manager for BMCFuzz"""
    
    _instance = None
    _logger = None
    _log_file = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._logger = logging.getLogger("BMCFuzz")
            self._logger.setLevel(logging.DEBUG)
            self._initialized = False
    
    @classmethod
    def init(cls, log_dir: Optional[str] = None, prefix: str = "bmcfuzz"):
        """
        Initialize logging system
        
        Args:
            log_dir: Directory for log files (default: current dir)
            prefix: Prefix for log file name
        """
        instance = cls()
        
        if log_dir is None:
            log_dir = os.getcwd()
        elif not os.path.isabs(log_dir):
            log_dir = os.path.abspath(log_dir)
        
        logs_main_dir = os.path.join(log_dir, "logs")
        fuzz_log_dir = os.path.join(log_dir, "logs", "fuzz")
        
        os.makedirs(logs_main_dir, exist_ok=True)
        os.makedirs(fuzz_log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        log_file_name = os.path.join(logs_main_dir, f"{prefix}_{timestamp}.log")
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        console_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
        
        file_handler = logging.FileHandler(log_file_name, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        instance._logger.handlers.clear()
        instance._logger.addHandler(file_handler)
        instance._logger.addHandler(console_handler)
        
        instance._log_file = log_file_name
        instance._initialized = True
        
        instance.info("Logging system initialized")
        instance.info(f"Log file: {log_file_name}")
        
        return instance
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None):
        """
        Get logger instance
        
        Args:
            name: Logger name for module identification
        """
        instance = cls()
        if name:
            return logging.getLogger(f"BMCFuzz.{name}")
        return instance._logger
    
    def info(self, message: str):
        """Log info level message"""
        self._logger.info(message)
        # if print_message:
        #     print(message)
    
    def warning(self, message: str):
        """Log warning level message"""
        self._logger.warning(message)
        # if print_message:
        #     print(f"[WARNING] {message}")
    
    def error(self, message: str):
        """Log error level message"""
        self._logger.error(message)
        # if print_message:
        #     print(f"[ERROR] {message}")
    
    def debug(self, message: str):
        """Log debug level message"""
        self._logger.debug(message)
        # if print_message:
        #     print(f"[DEBUG] {message}")
    
    @classmethod
    def clear_logs(cls, log_dir: Optional[str] = None):
        """Clear log directory"""
        if log_dir is None:
            log_dir = os.getcwd()
        elif not os.path.isabs(log_dir):
            log_dir = os.path.abspath(log_dir)
        
        logs_dir = os.path.join(log_dir, "logs")
        if os.path.exists(logs_dir):
            shutil.rmtree(logs_dir)
        
        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(os.path.join(log_dir, "logs", "fuzz"), exist_ok=True)
        
        instance = cls()
        instance.info(f"Log directory cleared: {logs_dir}")


logger = BMCFuzzLogger()


def log_init(log_dir: Optional[str] = None, prefix: str = "bmcfuzz"):
    """Initialize logging system"""
    return BMCFuzzLogger.init(log_dir, prefix)


def log_message(message: str, print_message: bool = True):
    """Log message"""
    logger.info(message, print_message=print_message)


def clear_logs(log_dir: Optional[str] = None):
    """Clear log directory"""
    BMCFuzzLogger.clear_logs(log_dir)


if __name__ == "__main__":
    log_init(prefix="test")
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    logger.debug("Test debug message", print_message=True)
    
    module_logger = BMCFuzzLogger.get_logger("TestModule")
    module_logger.info("Message from TestModule")
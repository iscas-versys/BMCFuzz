import re
import os
import shutil
import logging

from datetime import datetime

def log_init(path=None):
    if path is None:
        current_dir = os.path.dirname(os.path.realpath(__file__))
    else:
        current_dir = path
        
    if not os.path.exists(os.path.join(current_dir, "logs")):
        os.makedirs(os.path.join(current_dir, "logs"))
    if not os.path.exists(os.path.join(current_dir, "logs", "fuzz")):
        os.makedirs(os.path.join(current_dir, "logs", "fuzz"))
    log_file_name = os.path.join(current_dir, "logs", datetime.now().strftime("%Y-%m-%d_%H-%M") + ".log")
    logging.basicConfig(filename=log_file_name, level=logging.INFO, format='%(asctime)s - %(message)s')
    log_message(f"Log initialized in {log_file_name}.")

def log_message(message, print_message=True):
    logging.info(message)
    if print_message:
        print(message)

def clear_logs(path=None):
    if path is None:
        current_dir = os.path.dirname(os.path.realpath(__file__))
    else:
        current_dir = path

    logs_dir = os.path.join(current_dir, "logs")
    if os.path.exists(logs_dir):
        shutil.rmtree(logs_dir)
    os.makedirs(logs_dir)
    fuzz_log_dir = os.getenv("FUZZ_LOG")
    os.makedirs(fuzz_log_dir, exist_ok=True)


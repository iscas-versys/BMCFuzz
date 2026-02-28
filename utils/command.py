"""
Command execution module for BMCFuzz
"""

import subprocess
import psutil
import sys
import os
from typing import Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import BMCFuzzLogger

command_logger = BMCFuzzLogger.get_logger("Command")


class CommandExecutor:
    """Unified command executor"""
    
    def __init__(self, timeout: Optional[int] = None):
        """
        Args:
            timeout: Default timeout in seconds (None = no timeout)
        """
        self.timeout = timeout
        self.command_logger = command_logger
    
    def run(
        self,
        command: str,
        shell: bool = False,
        capture_output: bool = True,
        timeout: Optional[int] = None,
        env: Optional[dict] = None
    ) -> Tuple[int, str, str]:
        """
        Execute command and return result
        
        Returns:
            (return_code, stdout, stderr)
        """
        effective_timeout = timeout if timeout is not None else self.timeout
        
        try:
            self.command_logger.debug(f"Executing: {command}")
            
            stdout_pipe = subprocess.PIPE if capture_output else None
            stderr_pipe = subprocess.PIPE if capture_output else None
            
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=stdout_pipe,
                stderr=stderr_pipe,
                text=True,
                env=env
            )
            
            stdout_data, stderr_data = process.communicate(timeout=effective_timeout)
            return_code = process.returncode
            
            if return_code != 0:
                self.command_logger.warning(
                    f"Command failed, return code: {return_code}, stderr: {stderr_data}"
                )
            
            return return_code, stdout_data, stderr_data
            
        except subprocess.TimeoutExpired:
            self.command_logger.error(f"Command timeout: {command}")
            self._kill_process_tree(process.pid)
            return -1, "", "Timeout"
        
        except KeyboardInterrupt:
            self.command_logger.warning("Command interrupted by user")
            self._kill_process_tree(process.pid)
            return -1, "", "Interrupted"
        
        except Exception as e:
            self.command_logger.error(f"Command error: {e}")
            if 'process' in locals():
                self._kill_process_tree(process.pid)
            return -1, "", str(e)
    
    def run_simple(self, command: str, shell: bool = False) -> int:
        """
        Execute simple command, return code only
        
        Returns:
            Command return code
        """
        try:
            self.command_logger.debug(f"Executing: {command}")
            
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True
            )
            
            return_code = process.wait()
            
            if return_code != 0:
                self.command_logger.warning(f"Command failed, return code: {return_code}")
            
            return return_code
            
        except KeyboardInterrupt:
            self.command_logger.warning("Command interrupted by user")
            self._kill_process_tree(process.pid)
            self._reset_terminal()
            return -1
        
        except Exception as e:
            self.command_logger.error(f"Command error: {e}")
            if 'process' in locals():
                self._kill_process_tree(process.pid)
                self._reset_terminal()
            return -1
    
    @staticmethod
    def _kill_process_tree(pid: int):
        """Kill process and all children"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            for child in children:
                child.terminate()
            
            parent.terminate()
            
            gone, alive = psutil.wait_procs([parent] + children, timeout=5)
            
            for p in alive:
                p.kill()
            
            command_logger.debug(f"Process tree killed: {pid}")
            
        except psutil.NoSuchProcess:
            command_logger.debug(f"Process not found: {pid}")
        except Exception as e:
            command_logger.error(f"Kill process error: {e}")
    
    @staticmethod
    def _reset_terminal():
        """Reset terminal state"""
        try:
            subprocess.run(["stty", "sane"], check=True)
            command_logger.debug("Terminal reset")
        except Exception as e:
            command_logger.error(f"Reset terminal failed: {e}")
    
    def run_with_env(
        self,
        command: str,
        env_file: str,
        shell: bool = False
    ) -> int:
        """
        Execute command after loading env file
        
        Returns:
            Command return code
        """
        full_command = f"bash -c 'source {env_file} && {command}'"
        return self.run_simple(full_command, shell=True)


executor = CommandExecutor()


def run_command(command: str, shell: bool = False) -> int:
    """Execute command and return code"""
    return executor.run_simple(command, shell=shell)


def kill_process_and_children(pid: int):
    """Kill process and children"""
    CommandExecutor._kill_process_tree(pid)


def reset_terminal():
    """Reset terminal"""
    CommandExecutor._reset_terminal()


if __name__ == "__main__":
    from utils.logger import log_init
    
    log_init(prefix="command_test")
    
    result = run_command("echo 'Hello, BMCFuzz!'", shell=True)
    command_logger.info(f"Return code: {result}")
    
    return_code, stdout, stderr = executor.run("ls -la", shell=True)
    command_logger.info(f"Return code: {return_code}")
    command_logger.debug(f"Output: {stdout[:100]}...")
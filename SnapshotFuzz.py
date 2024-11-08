import os
import csv
import sys
import subprocess

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Formal"))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "SetInitValues"))

from datetime import datetime

from SetInitValues.split_sv_mudules import split_sv_modules
from SetInitValues.generate_hierarchy import hierarchy_yaml_parser
from SetInitValues.json_add_initval import add_regs
from SetInitValues.vcd_parser import vcd_to_json
from SetInitValues.connect_reginit_vcd_parser import connect_json_vcd
from SetInitValues.new_init_folder import create_init_files

from Formal.Scheduler import Scheduler
from Formal.Pretreat import log_message, clear_logs, log_init

class SnapshotFuzz:
    split_sv_modules_dir = None
    module_with_regs_json = None

    formal_dir = None
    set_init_values_dir = None
    csr_wave_dir = None
    
    def init(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))

        set_init_values_dir = os.path.join(current_dir, 'SetInitValues')
        formal_dir = os.path.join(current_dir, 'Formal')

        self.set_init_values_dir = set_init_values_dir
        self.formal_dir = formal_dir

        """ Set Init Values """
        log_message("Start Set Init Values")
        default_sv_file = os.path.join(set_init_values_dir, 'SimTop.sv')
        default_top_module_name = 'SimTop'

        # step1: split_sv_modules
        log_message(f"Step1: Split modules")
        split_sv_modules_dir = os.path.join(set_init_values_dir, default_top_module_name + '_split')
        if not os.path.exists(split_sv_modules_dir):
            split_sv_modules(default_sv_file, split_sv_modules_dir)
        self.split_sv_modules_dir = split_sv_modules_dir
        log_message(f"Modules has been split into {split_sv_modules_dir} directory.")

        # step2: run_svinst to generate modules yaml
        log_message(f"Step2: Generate modules yaml")
        output_yaml = os.path.join(set_init_values_dir, default_top_module_name + '.yaml')
        command = f"{set_init_values_dir}/bin/svinst {default_sv_file} > {output_yaml}"
        if not os.path.exists(output_yaml):
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            if result.returncode != 0:
                log_message(f"Generate modules yaml command: {command} failed with return code: {result.returncode}")
                log_message(f"Error output: {result.stderr}")
                exit(result.returncode)
        log_message(f"Generate modules yaml command: {command} executed successfully.")

        # step3: hierarchy yaml parser
        log_message(f"Step3: Generate hierarchy json")
        output_json = os.path.join(set_init_values_dir, default_top_module_name + '.json')
        if not os.path.exists(output_json):
            result = hierarchy_yaml_parser(output_yaml, output_json, default_top_module_name)
            if result != 0:
                log_message(f"Generate hierarchy json failed with return code: {result}")
                exit(result)
        log_message(f"Generate hierarchy json executed successfully.")

        # step4: add regs init values
        log_message(f"Step4: Add regs init values")
        output_json_with_regs = os.path.join(set_init_values_dir, default_top_module_name + '_with_regs.json')
        add_regs(output_json, output_json_with_regs, split_sv_modules_dir)
        self.module_with_regs_json = output_json_with_regs
        log_message(f"Add regs init values executed successfully.")

        # set csr wave dir
        self.csr_wave_dir = os.path.join(set_init_values_dir, 'csr_wave')
        
        log_message("End Set Init Values")
    
    def run_on_wave(self, wave_vcd_path):
        log_message("Start Run On Wave")
        
        # convert wave vcd to json
        wave_json_path = wave_vcd_path.replace('.vcd', '.json')
        if not os.path.exists(wave_json_path):
            vcd_to_json(wave_vcd_path, wave_json_path)
        log_message(f"Convert wave vcd to json executed successfully.")

        # set regs init values
        updated_registers_json = os.path.join(self.set_init_values_dir, 'updated_registers.json')
        result = connect_json_vcd(self.module_with_regs_json, wave_json_path, updated_registers_json)
        if result != 0:
            log_message(f"Set regs init values failed with return code: {result}")
            exit(result)
        log_message(f"Set regs init values executed successfully.")

        # create init files
        init_file_path = os.path.join(self.set_init_values_dir, 'SimTop_init.sv')
        create_init_files(self.split_sv_modules_dir, self.split_sv_modules_dir + '_init', updated_registers_json, init_file_path)
        log_message(f"Create init files executed successfully.")

        log_message("End Run On Wave")

def run():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    clear_logs(current_dir)
    log_init(current_dir)

    fuzz = SnapshotFuzz()
    fuzz.init()
    fuzz.run_on_wave(os.path.join(fuzz.csr_wave_dir, 'csr_wave_0.vcd'))

    scheduler = Scheduler()
    scheduler.init(True)
    scheduler.run_loop(1)

def run_set_init_values():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    clear_logs(current_dir)
    log_init(current_dir)

    fuzz = SnapshotFuzz()
    fuzz.init()
    fuzz.run_on_wave(os.path.join(fuzz.csr_wave_dir, 'csr_wave_0.vcd'))

if __name__ == "__main__":
    run()
    # run_set_init_values()
    pass


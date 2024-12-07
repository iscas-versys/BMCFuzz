import os
import re
import csv
import shutil

from CSRTransitionParser import *
from tools import log_message

class CSRTransitionSelect:
    transition_map = {
        'C_1': {},
        'C_2': {},
        'C_3': {},
        'C_4': {},
        'C_5': {},
        'C_6': {}
    }

    transition_id = 0
    total_transitions = []

    selected_reset = False

    id2transition = {}

    def file_init(self, cover_type="toggle"):
        # init csr_wave directory
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        csr_wave_dir = set_init_dir + "/csr_wave"
        if os.path.exists(csr_wave_dir):
            shutil.rmtree(csr_wave_dir)
        os.makedirs(csr_wave_dir)
        log_message(f"CSR Wave directory initialized.")

        # init reset wave file
        reset_wave_file = set_init_dir + f"/rtl_src/reset_{cover_type}.vcd"
        shutil.copyfile(reset_wave_file, csr_wave_dir + "/0.vcd")
        log_message(f"Reset wave file copied.")

    def update(self):
        fuzz_run_dir = os.getenv("NOOP_HOME") + "/tmp/fuzz_run"

        for fuzz_id in os.listdir(fuzz_run_dir):
            dirpath = fuzz_run_dir + "/" + fuzz_id
            csr_transition_dir = dirpath + "/csr_transition"
            csr_waveform_dir = dirpath + "/csr_wave"
            cycle_pattern = re.compile(r"csr_wave_(\d+)_(\d+).vcd")
            for wave_file in os.listdir(csr_waveform_dir):
                file_basename = os.path.basename(wave_file)
                case_id, case_cycle = cycle_pattern.match(file_basename).groups()
                transition_file = csr_transition_dir + "/csr_transition_" + case_id + ".csv"
                wave_file = csr_waveform_dir + "/" + wave_file
                with open(transition_file, mode="r", newline="", encoding="utf-8") as file:
                    csv_reader = list(csv.DictReader(file))
                    past = csv_reader[0]
                    now = csv_reader[1]
                    score = self.calculate_score(past, now)
                    if score == 0:
                        continue
                    self.transition_id += 1
                    self.total_transitions.append((score, self.transition_id))
                    self.generate_waveform_file(wave_file, self.transition_id)
                    self.id2transition[self.transition_id] = (past, now)
                    log_message(f"Transition ID: {self.transition_id}, Score: {score}")
                    log_message(f"Transition: {self.id2transition[self.transition_id]}")
    
    def select_highest_score_snapshot(self):
        if not self.selected_reset:
            self.selected_reset = True
            return 0
        
        if len(self.total_transitions) == 0:
            return -1
        
        best_score = -1
        best_id = -1
        for csr_score, csr_id in self.total_transitions:
            if csr_score > best_score:
                best_score = csr_score
                best_id = csr_id
        
        self.update_transition_map(self.id2transition[best_id][0], self.id2transition[best_id][1])

        # new_transition = []
        # for _, csr_id in self.total_transitions:
        #     csr_score = self.calculate_score(self.id2transition[csr_id][0], self.id2transition[csr_id][1])
        #     if csr_score == 0:
        #         self.delete_waveform(csr_id)
        #         continue
        #     new_transition.append((csr_score, csr_id))
        # self.total_transitions = new_transition
        self.total_transitions.remove((best_score, best_id))

        log_message(f"Best ID: {best_id}, Score: {best_score}")
        log_message(f"Transition: {self.id2transition[best_id]}")

        return best_id

    def calculate_score(self, past, now):
        score = 0

        criteria = generate_csr_transition_criteria(self.transition_map, past, now)

        for C_i, (past_bits, now_bits), power in criteria:
            transition = (past_bits, now_bits)
            if past_bits == now_bits:
                continue
            if C_i == 'C_2' and (not vm_is_enabled(now['privilegeMode'], now['mstatus'], now['satp'])):
                continue
            if transition not in self.transition_map[C_i]:
                self.transition_map[C_i][transition] = power
            else:
                power = self.transition_map[C_i][transition]
            if power == 0:
                continue
            score += 2 ** power
        
        return score
    
    def update_transition_map(self, past, now):
        criteria = generate_csr_transition_criteria(self.transition_map, past, now)

        for C_i, (past_bits, now_bits), power in criteria:
            transition = (past_bits, now_bits)
            if past_bits == now_bits:
                continue
            if C_i == 'C_2' and (not vm_is_enabled(now['privilegeMode'], now['mstatus'], now['satp'])):
                continue
            self.transition_map[C_i][transition] = max(0, self.transition_map[C_i][transition] - 1)

    def delete_waveform(self, waveform_id):
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        wave_file = set_init_dir + f"/csr_wave/{waveform_id}.vcd"
        os.remove(wave_file)
    
    def generate_waveform_file(self, src_file, waveform_id):
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        dst_file = set_init_dir + f"/csr_wave/{waveform_id}.vcd"
        shutil.copyfile(src_file, dst_file)
    
if __name__ == "__main__":
    csr_transition_select = CSRTransitionSelect()
    csr_transition_select.file_init()
    csr_transition_select.update()
    best_id = csr_transition_select.select_highest_score_snapshot()
    print("Best ID: ", best_id)
    best_id = csr_transition_select.select_highest_score_snapshot()
    print("Best ID: ", best_id)
    best_id = csr_transition_select.select_highest_score_snapshot()
    print("Best ID: ", best_id)
    

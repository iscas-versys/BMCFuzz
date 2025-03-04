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
    transition_scores = []
    total_transitions = set()

    selected_reset = False

    id2transition = {}

    def file_init(self, cpu, cover_type):
        # init csr_wave directory
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        csr_wave_dir = set_init_dir + "/csr_wave"
        if os.path.exists(csr_wave_dir):
            shutil.rmtree(csr_wave_dir)
        os.makedirs(csr_wave_dir)
        csr_snapshot_dir = set_init_dir + "/csr_snapshot"
        if os.path.exists(csr_snapshot_dir):
            shutil.rmtree(csr_snapshot_dir)
        os.makedirs(csr_snapshot_dir)
        log_message(f"CSR Wave directory initialized.")

        # init reset wave file
        reset_wave_file = set_init_dir + f"/rtl_src/{cpu}/reset_{cover_type}.vcd"
        reset_snapshot_file = set_init_dir + f"/rtl_src/{cpu}/reset_snapshot"
        shutil.copyfile(reset_wave_file, csr_wave_dir + "/0.vcd")
        shutil.copyfile(reset_snapshot_file, csr_snapshot_dir + "/0")
        log_message(f"Reset wave file and snapshot copied.")

    def update(self):
        fuzz_run_dir = os.getenv("NOOP_HOME") + "/tmp/fuzz_run"

        for fuzz_id in os.listdir(fuzz_run_dir):
            if not os.path.isdir(fuzz_run_dir + "/" + fuzz_id):
                continue
            dirpath = fuzz_run_dir + "/" + fuzz_id
            csr_transition_dir = dirpath + "/csr_transition"
            csr_waveform_dir = dirpath + "/csr_wave"
            csr_snapshot_dir = dirpath + "/csr_snapshot"
            cycle_pattern = re.compile(r"csr_wave_(\d+)_(\d+).vcd")
            for wave_file in os.listdir(csr_waveform_dir):
                file_basename = os.path.basename(wave_file)
                case_id, case_cycle = cycle_pattern.match(file_basename).groups()
                transition_file = csr_transition_dir + "/csr_transition_" + case_id + ".csv"
                snapshot_file = csr_snapshot_dir + "/csr_snapshot_" + case_id;
                wave_file = csr_waveform_dir + "/" + wave_file
                with open(transition_file, mode="r", newline="", encoding="utf-8") as file:
                    csv_reader = list(csv.DictReader(file))
                    past = csv_reader[0]
                    now = csv_reader[1]
                    transition_str = str(past) + str(now)
                    if transition_str in self.total_transitions:
                        log_message(f"Transition already exists: {past}, {now}")
                        continue
                    self.total_transitions.add(transition_str)
                    score = self.calculate_score(past, now)
                    if score == 0:
                        log_message(f"Transition score is 0: {past}, {now}")
                        continue
                    self.transition_id += 1
                    self.transition_scores.append((score, self.transition_id))
                    self.copy_waveform_file(wave_file, self.transition_id)
                    self.copy_snapshot_file(snapshot_file, self.transition_id)
                    self.id2transition[self.transition_id] = (past, now)
                    log_message(f"Transition ID: {self.transition_id}, Score: {score}")
                    log_message(f"Transition: {self.id2transition[self.transition_id]}")
    
    def select_highest_score_snapshot(self):
        if len(self.transition_scores) == 0:
            return -1
        
        best_score = -1
        best_id = -1
        for csr_score, csr_id in self.transition_scores:
            if csr_score > best_score:
                best_score = csr_score
                best_id = csr_id

        if not self.selected_reset and best_score <= 32:
            self.selected_reset = True
            log_message(f"Selecting reset snapshot.")
            return 0
        
        self.update_transition_map(self.id2transition[best_id][0], self.id2transition[best_id][1])
        self.transition_scores.remove((best_score, best_id))

        new_transition = []
        for _, csr_id in self.transition_scores:
            csr_score = self.calculate_score(self.id2transition[csr_id][0], self.id2transition[csr_id][1])
            log_message(f"Transition ID: {csr_id}, Score: {csr_score}")
            log_message(f"Transition: {self.id2transition[csr_id]}")
            new_transition.append((csr_score, csr_id))
        self.transition_scores = new_transition

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
        wave_json = set_init_dir + f"/csr_wave/{waveform_id}.json"
        os.remove(wave_file)
        os.remove(wave_json)
    
    def delete_snapshot(self, snapshot_id):
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        snapshot_file = set_init_dir + f"/csr_snapshot/{snapshot_id}"
        os.remove(snapshot_file)
    
    def copy_waveform_file(self, src_file, waveform_id):
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        dst_file = set_init_dir + f"/csr_wave/{waveform_id}.vcd"
        shutil.copyfile(src_file, dst_file)
    
    def copy_snapshot_file(self, src_file, snapshot_id):
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        dst_file = set_init_dir + f"/csr_snapshot/{snapshot_id}"
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
    

import os
import re
import csv
import shutil
import heapq

from CSRTransitionParser import *

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

    id2transition = {}
    id2cycle = {}

    def file_init(self):
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        csr_snapshot_dir = set_init_dir + "/csr_snapshot"
        csr_wave_dir = set_init_dir + "/csr_wave"
        if os.path.exists(csr_snapshot_dir):
            shutil.rmtree(csr_snapshot_dir)
        if os.path.exists(csr_wave_dir):
            shutil.rmtree(csr_wave_dir)
        os.makedirs(csr_snapshot_dir)
        os.makedirs(csr_wave_dir)

    def update(self):
        fuzz_run_dir = os.getenv("NOOP_HOME") + "/tmp/fuzz_run"

        for fuzz_id in os.listdir(fuzz_run_dir):
            dirpath = fuzz_run_dir + "/" + fuzz_id
            testcase = dirpath + "/fuzz_testcase"
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
                    heapq.heappush(self.total_transitions, (-score, self.transition_id))
                    self.generate_snapshot_file(testcase, self.transition_id)
                    self.generate_waveform_file(wave_file, self.transition_id)
                    self.id2transition[self.transition_id] = (past, now)
                    self.id2cycle[self.transition_id] = case_cycle
    
    def select_highest_score_snapshot(self):
        best_score, best_id = heapq.heappop(self.total_transitions)
        best_score = -best_score
        return best_id, self.id2cycle[best_id], self.id2transition[best_id], best_score

    def calculate_score(self, past, now):
        score = 0

        past_c1 = past['privilegeMode']
        now_c1 = now['privilegeMode']

        past_c2 = parse_c2_bits(past['mstatus'], get_satp_hi(past['satp']), past['privilegeMode'])
        now_c2 = parse_c2_bits(now['mstatus'], get_satp_hi(now['satp']), now['privilegeMode'])
        
        past_c3 = parse_c3_bits(past['mstatus'])
        now_c3 = parse_c3_bits(now['mstatus'])
        
        past_c4 = parse_c4_bits(past['mstatus'])
        now_c4 = parse_c4_bits(now['mstatus'])
        
        past_c5 = past['medeleg']
        now_c5 = now['medeleg']
        
        criteria = [
            # C1: Privilege mode changed
            ('C_1', (past_c1, now_c1), 6),
            # C2: Virtual memory enabled
            ('C_2', (past_c2, now_c2), 5),
            # C3: Single function changed (TSR, TW, TVM)
            ('C_3', (past_c3, now_c3), 4),
            # C4: Other mstatus bits changed (MPP, SPP, MPIE, SPIE, MIE, SIE)
            ('C_4', (past_c4, now_c4), 3),
            # C5: M mode delegation changed
            ('C_5', (past_c5, now_c5), 2),
            # C6: Other custom CSRs changed
            # ('C_6', (past_custom_csrs, now_custom_csrs), k)
        ]

        for C_i, (past_bits, now_bits), power in criteria:
            transition = (past_bits, now_bits)
            if past_bits != now_bits:
                if C_i == 'C_2' and (not vm_is_enabled(now['privilegeMode'], now['mstatus'], now['satp'])):
                    continue
            if transition not in self.transition_map[C_i]:
                self.transition_map[C_i][transition] = power
            else:
                power = self.transition_map[C_i][transition]
            score += 2 ** power
            self.transition_map[C_i][transition] = max(0, self.transition_map[C_i][transition] - 1)
        
        return score

    def delete_snapshot(self, snapshot_id):
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        snapshot_file = set_init_dir + f"/csr_snapshot/{snapshot_id}"
        os.remove(snapshot_file)
    
    def delete_waveform(self, waveform_id):
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        wave_file = set_init_dir + f"/csr_wave/{waveform_id}.vcd"
        os.remove(wave_file)
    
    def generate_snapshot_file(self, src_file, snapshot_id):
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        dst_file = set_init_dir + f"/csr_snapshot/{snapshot_id}"
        shutil.copyfile(src_file, dst_file)
    
    def generate_waveform_file(self, src_file, waveform_id):
        set_init_dir = os.getenv("NOOP_HOME") + "/ccover/SetInitValues"
        dst_file = set_init_dir + f"/csr_wave/{waveform_id}.vcd"
        shutil.copyfile(src_file, dst_file)
    
if __name__ == "__main__":
    csr_transition_select = CSRTransitionSelect()
    csr_transition_select.file_init()
    csr_transition_select.update()
    csr_transition_select.select_highest_score_snapshot()
    
    pass

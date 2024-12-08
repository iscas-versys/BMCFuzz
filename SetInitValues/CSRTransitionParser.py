
def generate_csr_transition_criteria(transition_map, past, now):
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
        ('C_1', (past_c1, now_c1), 3),
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

    return criteria

def parse_c2_bits(mstatus, satp_mode, privilege_mode):
    parsed_mstatus = parse_mstatus(mstatus)
    mxr_sum = ''.join(parsed_mstatus[bit] for bit in ['MXR', 'SUM'])
    return mxr_sum + satp_mode + privilege_mode

def parse_c3_bits(mstatus):
    parsed_mstatus = parse_mstatus(mstatus)
    return ''.join(parsed_mstatus[bit] for bit in ['TSR', 'TW', 'TVM'])

def parse_c4_bits(mstatus):
    parsed_mstatus = parse_mstatus(mstatus)
    return ''.join(parsed_mstatus[bit] for bit in ['MPP', 'SPP', 'MPIE', 'SPIE', 'MIE', 'SIE'])

fields = {
    "SD": (63, 63),
    "WPRI1": (62, 38),
    "MBE": (37, 37),
    "SBE": (36, 36),
    "SXL": (35, 34),
    "UXL": (33, 32),
    "WPRI2": (31, 23),
    "TSR": (22, 22),
    "TW": (21, 21),
    "TVM": (20, 20),
    "MXR": (19, 19),
    "SUM": (18, 18),
    "MPRV": (17, 17),
    "XS": (16, 15),
    "FS": (14, 13),
    "MPP": (12, 11),
    "VS": (10, 9),
    "SPP": (8, 8),
    "MPIE": (7, 7),
    "UBE": (6, 6),
    "SPIE": (5, 5),
    "WPRI3": (4, 4),
    "MIE": (3, 3),
    "WPRI4": (2, 2),
    "SIE": (1, 1),
    "WPRI5": (0, 0),
}

def vm_is_enabled(privilege_mode, mstatus, satp):
    # 解析 mstatus 和 satp
    parsed_mstatus = parse_mstatus(mstatus)
    mprv = parsed_mstatus['MPRV'] == '1'
    mpp = parsed_mstatus['MPP']
    satp_mode = int(get_satp_hi(satp), 2)

    if satp_mode == 8 and ((privilege_mode in ['00', '01']) or (mprv and mpp in ['00', '01'])):
        return True
    return False

def parse_mstatus(mstatus_hex):
    mstatus_bin = bin(int(mstatus_hex, 16))[2:].zfill(64)
    parsed_fields = {}
    for name, (start, end) in fields.items():
        value = mstatus_bin[63 - start:64 - end]
        parsed_fields[name] = value
    return parsed_fields

def get_satp_hi(satp):
    satp_bin = bin(int(satp, 16))[2:].zfill(64)
    return satp_bin[:4]

if __name__ == "__main__":
    Transition = ({'privilegeMode': '3', 'mstatus': 'a00001800', 'satp': ' 0', 'medeleg': ' 0'}, {'privilegeMode': '3', 'mstatus': 'a00141800', 'satp': ' 0', 'medeleg': ' 0'})
    transition_map = {
        'C_1': {},
        'C_2': {},
        'C_3': {},
        'C_4': {},
        'C_5': {},
        'C_6': {}
    }
    past = Transition[0]
    now = Transition[1]

    print(str(past))
    print(str(now))
    
    criteria = generate_csr_transition_criteria(transition_map, past, now)

    score = 0
    for C_i, (past_bits, now_bits), power in criteria:
        transition = (past_bits, now_bits)
        if past_bits == now_bits:
            continue
        if C_i == 'C_2' and (not vm_is_enabled(now['privilegeMode'], now['mstatus'], now['satp'])):
            continue
        print(C_i, transition, power)
        print(2 ** power)

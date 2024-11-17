

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

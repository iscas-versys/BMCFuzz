# Define the bit positions for each field
fields = {
    "SD"  : (63, 63),
    "WPRI1": (62, 38),
    "MBE" : (37, 37),
    "SBE" : (36, 36),
    "SXL" : (35, 34),
    "UXL" : (33, 32),
    "WPRI2": (31, 23),
    "TSR" : (22, 22),
    "TW"  : (21, 21),
    "TVM" : (20, 20),
    "MXR" : (19, 19),
    "SUM" : (18, 18),
    "MPRV": (17, 17),
    "XS"  : (16, 15),
    "FS"  : (14, 13),
    "MPP" : (12, 11),
    "VS"  : (10, 9),
    "SPP" : (8, 8),
    "MPIE": (7, 7),
    "UBE" : (6, 6),
    "SPIE": (5, 5),
    "WPRI3": (4, 4),
    "MIE" : (3, 3),
    "WPRI4": (2, 2),
    "SIE" : (1, 1),
    "WPRI5": (0, 0),
}

def parse_mstatus(mstatus_hex):
    # Convert hex to binary string
    mstatus_bin = bin(int(mstatus_hex, 16))[2:].zfill(64)

    # Parse each field
    parsed_fields = {}
    for name, (start, end) in fields.items():
        value = mstatus_bin[63 - start:64 - end]
        parsed_fields[name] = '0' if value.count('1') == 0 else value
    
    return parsed_fields

def format_mstatus(mstatus):
    # Format the mstatus value with underscores
    return "0x" + "_".join(mstatus[i:i+4] for i in range(0, 16, 4))

def main():
    # Define mstatus values in hex
    mstatus_list = ['0x00001800', '0xa00001800', '0x000E0800', '0xa00001800', '0xa00000080']

    # Ensure each mstatus value is a 64-bit hex string
    mstatus_list = [f"{int(mstatus, 16):016x}" for mstatus in mstatus_list]
    formatted_mstatus_list = [format_mstatus(mstatus) for mstatus in mstatus_list]

    # Parse each mstatus value
    parsed_results = [(formatted_mstatus, parse_mstatus(f"0x{mstatus}")) for formatted_mstatus, mstatus in zip(formatted_mstatus_list, mstatus_list)]

    # Print the parsed fields using a loop
    print("Parsed mstatus fields:")
    headers = " | ".join(f"{name:^6}" for name in fields.keys())
    separator = "-" * (len(headers) + 3 * (len(fields) + 1) - 79)
    print(f"+{'-'*24}+{separator}+")
    print(f"+{'mstatus':^23} | {headers} |")
    print(f"+{'-'*24}+{separator}+")
    
    for mstatus, parsed_fields in parsed_results:
        values = " | ".join(f"{parsed_fields[name]:^6}" for name in fields.keys())
        print(f"| {mstatus:^22} | {values} |")
        print(f"+{'-'*24}+{separator}+")
    
if __name__ == "__main__":
    main()

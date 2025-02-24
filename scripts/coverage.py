import re
import os
import shutil
import logging
import csv
import argparse

NOOP_HOME = os.getenv("NOOP_HOME")

def parse_hebxin_log(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    cover_pattern = re.compile(r"hexbin/cover_(\d+).bin")
    
    cover_points = [0 for _ in range(11747)]
    for line in lines:
        match = cover_pattern.search(line)
        if match:
            cover_points[int(match.group(1))] = 1
    
    with open("hexbin.csv", "w", newline='', encoding='utf-8') as file:
        field_name = ['Index', 'Covered']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in range(11747):
            csv_writer.writerow({'Index': i, 'Covered': cover_points[i]})
    
    with open("hexbin.log", "w") as f:
        f.write("")

def parse_formal_log(file_path):
    uncover_case_pattern = re.compile(r"未发现case: cover_(\d+)")
    cover_case_pattern = re.compile(r"发现case: cover_(\d+)")

    with open(file_path, "r") as f:
        lines = f.readlines()
    
    cover_points = [0 for _ in range(11747)]
    for line in lines:
        if uncover_case_pattern.search(line):
            continue
        match = cover_case_pattern.search(line)
        if match:
            cover_points[int(match.group(1))] = 1
    
    with open("formal.csv", "w", newline='', encoding='utf-8') as file:
        field_name = ['Index', 'Covered']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in range(11747):
            csv_writer.writerow({'Index': i, 'Covered': cover_points[i]})
    
    with open("formal.log", "w") as f:
        f.write("")
    

def diff_hexbin_log(file1, file2):
    hexbin20_covered = [0 for _ in range(11747)]
    with open(file1, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if int(row['Covered']) == 1:
                hexbin20_covered[int(row['Index'])] = 1
    
    hexbin30_covered = [0 for _ in range(11747)]
    with open(file2, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if int(row['Covered']) == 1:
                hexbin30_covered[int(row['Index'])] = 1
    
    timeout_covered = []
    added_covered = []
    for i in range(11747):
        if hexbin20_covered[i] == 0 and hexbin30_covered[i] == 1:
            added_covered.append(i)
        if hexbin20_covered[i] == 1 and hexbin30_covered[i] == 0:
            timeout_covered.append(i)
    
    print("File1 covered: ", len(timeout_covered))
    print("File2 covered: ", len(added_covered))
    
    with open("file1.csv", "w", newline='', encoding='utf-8') as file:
        field_name = ['Index']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in timeout_covered:
            csv_writer.writerow({'Index': i})
    
    with open("file2.csv", "w", newline='', encoding='utf-8') as file:
        field_name = ['Index']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in added_covered:
            csv_writer.writerow({'Index': i})

if __name__ == "__main__":
    os.chdir(NOOP_HOME)

    parser = argparse.ArgumentParser()
    
    parser.add_argument("--parse", '-p', action='store_true', help="Parse hexbin log")
    parser.add_argument("--formal", '-f', action='store_true', help="Parse formal log")
    parser.add_argument("--file", '-f', type=str, default="hexbin.log", help="File")

    parser.add_argument("--diff", '-d', action='store_true', help="Diff hexbin log")
    parser.add_argument("--file1", '-f1', type=str, default="hexbin20.csv", help="File1")
    parser.add_argument("--file2", '-f2', type=str, default="hexbin30_init.csv", help="File2")

    args = parser.parse_args()

    if args.parse:
        if args.formal:
            parse_formal_log(args.file)
        else:
            parse_hebxin_log(args.file)
    if args.diff:
        diff_hexbin_log(args.file1, args.file2)


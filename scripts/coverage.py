import re
import os
import shutil
import logging
import csv
import argparse

from runtools import NOOP_HOME, BMCFUZZ_HOME

MAX_COVER_POINTS = 38253

def parse_uncovered_log(file_path, output_path):
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    # cover_pattern = re.compile(r"hexbin/cover_(\d+).bin")
    cover_pattern = re.compile(r"(\d+):\w+")
    
    cover_points = [1 for _ in range(MAX_COVER_POINTS)]
    for line in lines:
        match = cover_pattern.search(line)
        if match:
            cover_points[int(match.group(1))] = 0
    
    with open(output_path, "w", newline='', encoding='utf-8') as file:
        field_name = ['Index', 'Covered']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in range(MAX_COVER_POINTS):
            csv_writer.writerow({'Index': i, 'Covered': cover_points[i]})
    
    # with open(file_path, "w") as f:
    #     f.write("")

def parse_covered_log(file_path, output_path):
    uncover_case_pattern = re.compile(r"未发现case: cover_(\d+)")
    cover_case_pattern = re.compile(r"发现case: cover_(\d+)")

    with open(file_path, "r") as f:
        lines = f.readlines()
    
    cover_points = [0 for _ in range(MAX_COVER_POINTS)]
    for line in lines:
        if uncover_case_pattern.search(line):
            continue
        match = cover_case_pattern.search(line)
        if match:
            cover_points[int(match.group(1))] = 1
    
    with open(output_path, "w", newline='', encoding='utf-8') as file:
        field_name = ['Index', 'Covered']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in range(MAX_COVER_POINTS):
            csv_writer.writerow({'Index': i, 'Covered': cover_points[i]})
    
    # with open(file_path, "w") as f:
    #     f.write("")
    

def diff_covered_points(file1, file2):
    file1_covered = [0 for _ in range(MAX_COVER_POINTS)]
    with open(file1, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if int(row['Covered']) == 1:
                file1_covered[int(row['Index'])] = 1
    
    file2_covered = [0 for _ in range(MAX_COVER_POINTS)]
    with open(file2, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if int(row['Covered']) == 1:
                file2_covered[int(row['Index'])] = 1
    
    point2name = {}
    cover_name_file = os.path.join(BMCFUZZ_HOME, "scripts", "cover_name.dat")
    with open(cover_name_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            index, name = line.strip().split(",")
            point2name[int(index)] = name
    
    file1_add = []
    file2_add = []
    for i in range(MAX_COVER_POINTS):
        if file1_covered[i] == 0 and file2_covered[i] == 1:
            file2_add.append(i)
        if file1_covered[i] == 1 and file2_covered[i] == 0:
            file1_add.append(i)
    
    print("File1 covered: ", len(file1_add))
    print("File2 covered: ", len(file2_add))
    
    field_name = ['Index', 'Name']

    file1_dir = os.path.dirname(file1)
    file1_output = os.path.join(file1_dir, "file1.csv")
    with open(file1_output, "w", newline='', encoding='utf-8') as file:
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in file1_add:
            csv_writer.writerow({'Index': i, 'Name': point2name[i]})
    
    file2_dir = os.path.dirname(file2)
    file2_output = os.path.join(file2_dir, "file2.csv")
    with open(file2_output, "w", newline='', encoding='utf-8') as file:
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in file2_add:
            csv_writer.writerow({'Index': i, 'Name': point2name[i]})

if __name__ == "__main__":
    os.chdir(NOOP_HOME)

    parser = argparse.ArgumentParser()
    
    parser.add_argument("--parse-covered", '-pc', action='store_true', help="Parse covered log")
    parser.add_argument("--parse-uncovered", '-pu', action='store_true', help="Parse uncovered log")
    parser.add_argument("--diff", '-d', action='store_true', help="Diff hexbin log")

    parser.add_argument("--file1", '-f1', type=str, default="hexbin20.csv", help="File1")
    parser.add_argument("--file2", '-f2', type=str, default="hexbin30_init.csv", help="File2")

    args = parser.parse_args()

    if args.parse_covered:
        parse_covered_log(args.file1, args.file2)
    if args.parse_uncovered:
        parse_uncovered_log(args.file1, args.file2)
    if args.diff:
        diff_covered_points(args.file1, args.file2)


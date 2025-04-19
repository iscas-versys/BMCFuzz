import re
import os
import shutil
import logging
import csv
import argparse

from runtools import NOOP_HOME, BMCFUZZ_HOME

MAX_COVER_POINTS = 0

def merge_csv_files(input_dir, output_file):
    point2name = parse_cover_name_file()

    cover_points = [0 for _ in range(MAX_COVER_POINTS)]
    with os.scandir(input_dir) as entries:
        for entry in entries:
            if entry.name.endswith(".csv"):
                with open(entry.path, mode='r', newline='', encoding='utf-8') as file:
                    csv_reader = csv.DictReader(file)
                    for row in csv_reader:
                        if int(row['Covered']) == 1:
                            cover_points[int(row['Index'])] = 1
    covered = sum(cover_points)

    with open(output_file, "w", newline='', encoding='utf-8') as file:
        field_name = ['Index', 'Covered', 'Name']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in range(MAX_COVER_POINTS):
            csv_writer.writerow({'Index': i, 'Covered': cover_points[i], 'Name': point2name[i]})
        
    print(f"Merged CSV file created at: {output_file}")
    print(f"Covered points: {covered}/ {MAX_COVER_POINTS} {covered / MAX_COVER_POINTS * 100:.2f}%")

def generage_cover_name_file():
    firrtl_cover_file = os.path.join(NOOP_HOME, "build", "generated-src", "firrtl-cover.cpp")
    cover_name_file = os.path.join(BMCFUZZ_HOME, "scripts", "cover_name.dat")

    cover_name_begin_pattern = re.compile(r"_NAMES\[\]")
    cover_name_end_pattern = re.compile(r"};")

    point2name = {}

    with open(firrtl_cover_file, "r") as f:
        lines = f.readlines()
        index = 0
        cover_name_begin = False
        for line in lines:
            if cover_name_begin and cover_name_end_pattern.search(line):
                break
            if cover_name_begin:
                match = re.search(r"\"(.*?)\"", line)
                if match:
                    name = match.group(1)
                    point2name[index] = name
                    index += 1
            if cover_name_begin_pattern.search(line):
                cover_name_begin = True
    
    with open(cover_name_file, "w") as f:
        f.write("Index,Name\n")
        for index, name in point2name.items():
            f.write(f"{index},{name}\n")

def parse_cover_name_file():
    global MAX_COVER_POINTS
    cover_name_file = os.path.join(BMCFUZZ_HOME, "scripts", "cover_name.dat")
    point2name = {}
    with open(cover_name_file, "r") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            index = int(row['Index'])
            name = row['Name']
            point2name[index] = name
        MAX_COVER_POINTS = len(point2name)
    return point2name

def parse_cover_name(src_file):
    point2name = parse_cover_name_file()
    
    output_dir = os.path.dirname(src_file)
    covered_file = os.path.join(output_dir, "covered.csv")
    uncovered_file = os.path.join(output_dir, "uncovered.csv")
    
    covered_points = {}
    uncovered_points = {}
    with open(src_file, "r") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            index = int(row['Index'])
            covered = int(row['Covered'])
            if covered:
                covered_points[index] = point2name[index]
            else:
                uncovered_points[index] = point2name[index]
    
    with open(covered_file, "w", newline='', encoding='utf-8') as file:
        field_name = ['Index', 'Name']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        for index, name in covered_points.items():
            csv_writer.writerow({'Index': index, 'Name': name})
    
    with open(uncovered_file, "w", newline='', encoding='utf-8') as file:
        field_name = ['Index', 'Name']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        for index, name in uncovered_points.items():
            csv_writer.writerow({'Index': index, 'Name': name})

def parse_uncovered_log(file_path, output_path):
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    # cover_pattern = re.compile(r"hexbin/cover_(\d+).bin")
    cover_pattern = re.compile(r"(\d+):\w+")

    point2name = parse_cover_name_file()
    
    cover_points = [1 for _ in range(MAX_COVER_POINTS)]
    for line in lines:
        match = cover_pattern.search(line)
        if match:
            cover_points[int(match.group(1))] = 0
    
    with open(output_path, "w", newline='', encoding='utf-8') as file:
        field_name = ['Index', 'Covered', 'Name']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in range(MAX_COVER_POINTS):
            csv_writer.writerow({'Index': i, 'Covered': cover_points[i], 'Name': point2name[i]})
    
    # with open(file_path, "w") as f:
    #     f.write("")

def parse_covered_log(file_path, output_path):
    uncover_case_pattern = re.compile(r"未发现case: cover_(\d+)")
    cover_case_pattern = re.compile(r"发现case: cover_(\d+)")

    with open(file_path, "r") as f:
        lines = f.readlines()
    
    point2name = parse_cover_name_file()
    
    cover_points = [0 for _ in range(MAX_COVER_POINTS)]
    for line in lines:
        if uncover_case_pattern.search(line):
            continue
        match = cover_case_pattern.search(line)
        if match:
            cover_points[int(match.group(1))] = 1
    
    with open(output_path, "w", newline='', encoding='utf-8') as file:
        field_name = ['Index', 'Covered', 'Name']
        csv_writer = csv.DictWriter(file, fieldnames=field_name)
        csv_writer.writeheader()
        
        for i in range(MAX_COVER_POINTS):
            csv_writer.writerow({'Index': i, 'Covered': cover_points[i], 'Name': point2name[i]})
    
    # with open(file_path, "w") as f:
    #     f.write("")
    

def diff_covered_points(file1, file2):
    point2name = parse_cover_name_file()
    
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

    parser.add_argument("--generate-cover-name", '-g', action='store_true', help="Generate cover name file")
    
    parser.add_argument("--parse-name", '-pn', action='store_true', help="Parse cover name file")
    parser.add_argument("--parse-covered", '-pc', action='store_true', help="Parse covered log")
    parser.add_argument("--parse-uncovered", '-pu', action='store_true', help="Parse uncovered log")
    parser.add_argument("--diff", '-d', action='store_true', help="Diff hexbin log")

    parser.add_argument("--file1", '-f1', type=str, default="hexbin20.csv", help="File1")
    parser.add_argument("--file2", '-f2', type=str, default="hexbin30_init.csv", help="File2")

    args = parser.parse_args()

    if args.generate_cover_name:
        generage_cover_name_file()

    if args.parse_name:
        parse_cover_name(args.file1)
    if args.parse_covered:
        parse_covered_log(args.file1, args.file2)
    if args.parse_uncovered:
        parse_uncovered_log(args.file1, args.file2)
    if args.diff:
        diff_covered_points(args.file1, args.file2)


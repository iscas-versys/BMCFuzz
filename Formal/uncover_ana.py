import pandas as pd
import os

# 读取CSV文件
csv_file = 'uncover_points_in_NutShell.csv'
df = pd.read_csv(csv_file)

# 初始化统计变量
unreached_count = 0
unreached_indices = []

# 遍历每个coverNo
for index, row in df.iterrows():
    cover_no = row['coverNo']
    # print(f"正在处理 coverNo: {cover_no}")
    logfile_path = f'/home/seddon/Coding/formal_fuzzing/CoverCount/coverTasks/cover_{cover_no}/engine_0/logfile.txt'
    
    # 检查日志文件是否存在
    # print(f"{logfile_path} 存在")
    if os.path.exists(logfile_path):
        with open(logfile_path, 'r') as logfile:
            content = logfile.read()
            print(logfile_path)
            # 检查是否含有特定字符串
            if "cking cover reachability in step 19" in content:
                unreached_count += 1
            else:
                unreached_indices.append(cover_no)

# 输出结果
print(f"有 {unreached_count} 个日志文件包含 'Unreached cover statement at'。")
print("不包含该字符串的序号:", unreached_indices)

import os
import xml.etree.ElementTree as ET
import pandas as pd
from collections import defaultdict


def merge_blocks(blocks):
    """
    合并有交集的代码段。
    输入：blocks 是一个列表，每个元素是一个 (start_line, end_line) 的元组。
    输出：合并后的代码段列表。
    """
    if not blocks:
        return []

    # 按起始行排序
    blocks.sort(key=lambda x: x[0])
    merged = [list(blocks[0])]  # 初始化合并后的列表

    for current_start, current_end in blocks[1:]:
        last_end = merged[-1][1]

        if current_start <= last_end:  # 如果有交集
            merged[-1][1] = max(last_end, current_end)  # 合并
        else:
            merged.append([current_start, current_end])  # 添加新的代码段

    return merged


def parse_simian_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    file_clone_blocks = defaultdict(list)  # 按文件名分组存储代码段

    for set_element in root.findall('.//set'):
        for block_element in set_element.findall('.//block'):
            source_file = block_element.get('sourceFile')
            if source_file.endswith('.cpp'):
                source_file = source_file[:-4] + '.cc'
            start_line = int(block_element.get('startLineNumber'))
            end_line = int(block_element.get('endLineNumber'))
            file_clone_blocks[source_file].append((start_line, end_line))

    # 合并每个文件中的代码段
    clone_data = []
    for file_name, blocks in file_clone_blocks.items():
        merged_blocks = merge_blocks(blocks)
        for start, end in merged_blocks:
            clone_lines = end - start + 1
            clone_data.append({
                'File': file_name,
                'cc_start_line': start,
                'cc_end_line': end,
                'cc_lines': clone_lines
            })

    return clone_data


def update_excel_with_clone_counts(excel_path, sheet_name, clone_data):
    """
    将克隆数据写入Excel表格。
    如果表格不存在，则创建新的表格；如果表格已存在，则覆盖。
    """
    try:
        # 读取现有表格（如果存在）
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
    except FileNotFoundError:
        print(f"The file {excel_path} does not exist. Creating a new one.")
        df = pd.DataFrame(columns=['File', 'cc_start_line', 'cc_end_line', 'cc_lines'])
    except Exception as e:
        print(f"Error reading sheet {sheet_name}: {e}")
        df = pd.DataFrame(columns=['File', 'cc_start_line', 'cc_end_line', 'cc_lines'])

    # 检查clone_data的结构是否正确
    if not clone_data:
        print(f"No clone data to update for sheet {sheet_name}. Skipping.")
        return

    # 将克隆数据转换为DataFrame
    try:
        clone_df = pd.DataFrame(clone_data)
    except ValueError as e:
        print(f"Error converting clone data to DataFrame: {e}")
        print(f"Clone data structure: {clone_data}")
        return

    # 合并现有数据和新数据
    df = pd.concat([df, clone_df], ignore_index=True)

    # 写入Excel表格
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"Successfully updated sheet {sheet_name} in {excel_path}")
    except Exception as e:
        print(f"Error saving Excel file for {sheet_name}: {e}")


def main():
    directory = input('please input your clone .xml file directory:')
    # directory = '../clone_xml/apollo'
    excel_path = input('please input your excel path:')
    # excel_path = 'results/apollo.xlsx'

    # 检查Excel文件是否存在，如果不存在则创建一个空的Excel文件
    if not os.path.exists(excel_path):
        print(f"The file {excel_path} does not exist. Creating a new one.")
        pd.DataFrame(columns=['File', 'cc_start_line', 'cc_end_line', 'cc_lines']).to_excel(excel_path, index=False)

    # 获取目录中的XML文件列表
    file_names = [f for f in os.listdir(directory) if f.endswith('-dup.xml')]
    versions = [f"apollo-{f.split('-')[1]}" for f in file_names]

    for version in versions:
        sheet_name = version
        clone_data = []  # 初始化克隆数据

        # 遍历目录，找到对应的XML文件
        for file_name in os.listdir(directory):
            if file_name.startswith(version) and file_name.endswith('-dup.xml'):
                file_path = os.path.join(directory, file_name)
                clone_data.extend(parse_simian_xml(file_path))  # 解析XML文件并更新克隆数据
                print(f"Parsed {file_path} for version {version}")

        # 将克隆数据写入Excel表格
        update_excel_with_clone_counts(excel_path, sheet_name, clone_data)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Process interrupted by user.")
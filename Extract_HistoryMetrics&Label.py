import os
import xml.dom.minidom
import re
import pandas as pd


def check_bug_flag(commit_msg):
    """
    检查提交信息中是否包含与 bug 相关的关键词
    :param commit_msg: 提交信息
    :return: 如果包含则返回 1，否则返回 0
    """
    corrective_word_list = ['bug', 'fix', 'wrong', 'error', 'fail', 'problem', 'patch', 'correct']
    for word in corrective_word_list:
        if word.lower() in commit_msg.lower():
            return 1
    return 0


def extract_diff_info(commit):
    """
    从 commit 节点中提取文件修改信息
    :param commit: 单个 commit 节点
    :return: 包含文件修改信息的列表
    """
    bug_flag = check_bug_flag(commit.getElementsByTagName('msg')[0].firstChild.nodeValue)
    author = commit.getAttribute('author')
    modified_files = commit.getElementsByTagName('modified_files')
    if not modified_files:
        return []
    modified_files = modified_files[0]
    diff_lines = []
    for file in modified_files.getElementsByTagName('file'):
        file_path = file.getAttribute('old_path')
        added_lines = int(file.getAttribute('added_lines'))
        deleted_lines = int(file.getAttribute('deleted_lines'))
        diff_nodes = file.getElementsByTagName('diff')
        if not diff_nodes:
            continue
        diff = diff_nodes[0].firstChild
        if not diff:
            continue
        match = re.search(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', diff.nodeValue)
        if match:
            start_line = int(match.group(1))
            period = int(match.group(2))
            end_line = start_line + period
            diff_lines.append((file_path, author, added_lines, deleted_lines, start_line, end_line, bug_flag))
    return diff_lines


def process_diff_lines(diff_lines):
    """
    处理差异行信息，统计文件的修改信息
    :param diff_lines: 差异行信息列表
    :return: 包含文件修改信息的列表和 bug 提交信息列表
    """
    file_info = {}
    for line in diff_lines:
        file_path = line[0]
        added_lines = line[2]
        deleted_lines = line[3]
        if file_path not in file_info:
            file_info[file_path] = {
                'authors': set(),
                'modify_count': 0,
                'total_added': 0,
                'total_deleted': 0
            }
        file_info[file_path]['authors'].add(line[1])
        file_info[file_path]['modify_count'] += 1
        file_info[file_path]['total_added'] += added_lines
        file_info[file_path]['total_deleted'] += deleted_lines

    modified_info = []
    for file_path, info in file_info.items():
        author_count = len(info['authors'])
        modify_count = info['modify_count']
        avg_added = int(info['total_added'] / modify_count if modify_count > 0 else 0)
        avg_deleted = int(info['total_deleted'] / modify_count if modify_count > 0 else 0)
        modified_info.append((file_path, author_count, modify_count, avg_added, avg_deleted))

    bug_commit = [(line[0], line[4], line[5], line[6]) for line in diff_lines if line[6]]
    return modified_info, bug_commit


def extract_diff_lines(xml_file):
    """
    从 XML 文件中提取相关信息
    :param xml_file: XML 文件路径
    :return: 包含文件修改信息的列表和 bug 提交信息列表
    """
    dom = xml.dom.minidom.parse(xml_file)
    document = dom.documentElement
    diff_lines = []
    for commit in document.getElementsByTagName('commit'):
        diff_lines.extend(extract_diff_info(commit))
    return process_diff_lines(diff_lines)


def update_excel_columns(df, new_columns):
    """
    更新 DataFrame 中的列
    :param df: DataFrame 对象
    :param new_columns: 新列名列表
    :return: 更新后的 DataFrame
    """
    for col in new_columns:
        if col not in df.columns:
            df[col] = 0
    return df


def update_excel(excel_path, modified_info, sheet_name):
    """
    更新 Excel 文件中的相关信息
    :param excel_path: Excel 文件路径
    :param modified_info: 包含文件修改信息的列表
    :param sheet_name: 工作表名称
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
    except FileNotFoundError:
        print(f"错误: Excel 文件 {excel_path} 未找到。")
        return
    except pd.errors.ParserError:
        print(f"错误: 无法解析 Excel 文件 {excel_path}。")
        return

    new_columns = ['author_count', 'modify_count', 'avg_added', 'avg_deleted']
    df = update_excel_columns(df, new_columns)

    for file_path, author_count, modify_count, avg_added, avg_deleted in modified_info:
        prefix = f"D:\\download\\{sheet_name}\\{sheet_name}\\"
        file_name = prefix + file_path
        matched_rows = df[df['File'] == file_name]
        if not matched_rows.empty:
            df.loc[matched_rows.index, 'author_count'] = author_count
            df.loc[matched_rows.index, 'modify_count'] = modify_count
            df.loc[matched_rows.index, 'avg_added'] = avg_added
            df.loc[matched_rows.index, 'avg_deleted'] = avg_deleted

    try:
        with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    except Exception as e:
        print(f"写入 Excel 文件失败：{e}")


def check_intersection(range1, range2):
    """
    检查两个范围是否有交集
    :param range1: 第一个范围 (start, end)
    :param range2: 第二个范围 (start, end)
    :return: 如果有交集返回 True，否则返回 False
    """
    start1, end1 = range1
    start2, end2 = range2
    return not (end1 < start2 or end2 < start1)


def lable(excel_path, bug_commit, sheet_name):
    """
    标记 Excel 中的 Bug 列
    :param excel_path: Excel 文件路径
    :param bug_commit: 包含 bug 提交信息的列表
    :param sheet_name: 工作表名称
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
    except FileNotFoundError:
        print(f"错误: Excel 文件 {excel_path} 未找到。")
        return
    except pd.errors.ParserError:
        print(f"错误: 无法解析 Excel 文件 {excel_path}。")
        return

    new_columns = ['Bug']
    df = update_excel_columns(df, new_columns)

    for file_path, modified_start_line, modified_end_line, _ in bug_commit:
        prefix = f"D:\\download\\{sheet_name}\\{sheet_name}\\"
        file_name = prefix + file_path
        matched_rows = df[df['File'] == file_name]
        if not matched_rows.empty:
            for index, row in matched_rows.iterrows():
                cc_start_line = row['cc_start_line']
                cc_end_line = row['cc_end_line']
                if check_intersection((modified_start_line, modified_end_line), (cc_start_line, cc_end_line)):
                    df.loc[index, 'Bug'] = 1
                else:
                    df.loc[index, 'Bug'] = 0

    try:
        with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"Excel 文件已更新：{excel_path}")
    except Exception as e:
        print(f"写入 Excel 文件失败：{e}")


def main():
    # directory = 'all_commit\\apollo'
    # excel_path = 'results\\apollo.xlsx'
    directory = input('please input your commit directory:')
    excel_path = input('please input your excel path:')
    versions = []
    # 遍历目录
    for filename in os.listdir(directory):
        # 检查文件名是否符合格式
        if filename.endswith('_commit.xml'):
            # 分割文件名中的版本号
            parts = filename.split('_')
            version = parts[0] + '_' + parts[1] + '_' + parts[2]
            versions.append(version)
    for version in versions:
        parts = version.split("_")
        sheet_name = parts[0] + "-" + parts[1]
        xml_file = os.path.join(directory, f"{version}_commit.xml")
        if os.path.exists(xml_file):
            diff_data, bug_info = extract_diff_lines(xml_file)
            print(f"Parsed {xml_file} for version {sheet_name}")
            update_excel(excel_path, diff_data, sheet_name)
            lable(excel_path, bug_info, sheet_name)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Process interrupted by user.")

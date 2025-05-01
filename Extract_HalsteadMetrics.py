from Halstead_parser_code import code_halstead_extract
import pandas as pd
import os

def Get_SourceFile(excel_path, version):
    try:
        SourceFile = []
        # 读取指定工作表的数据
        df = pd.read_excel(excel_path, sheet_name=version)
        # 提取前三列
        first_three_columns = df.iloc[:, :3]
        for index, row in first_three_columns.iterrows():
            File = row["File"]
            start_line = row["cc_start_line"]  # 起始行号
            end_line = row["cc_end_line"]  # 终止行号

            # 将提取的数据存储到列表中
            SourceFile.append({
                "File": File,
                "Start_Line": start_line,
                "End_Line": end_line
            })
        return SourceFile

    except FileNotFoundError:
        print(f"Error: The file {excel_path} does not exist.")
        return None
    except ValueError as e:
        print(f"Error: {e}. Please ensure the file has at least three columns.")
        return None
    except KeyError:
        print(f"Error: The sheet '{version}' does not exist in the Excel file.")
        return None
    except Exception as e:
        print(f"Error reading columns: {e}")
        return None

def save_metrics_to_excel(excel_path, version, df):
    try:
        # 保存修改后的 Excel 文件
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=version, index=False)
        print(f"Metrics saved successfully to sheet '{version}' in {excel_path}")
    except Exception as e:
        print(f"Error saving metrics to Excel: {e}")

def main():
    excel_path = 'results\\apollo.xlsx'
    analyzer = code_halstead_extract.HalsteadMetrics()

    # 获取 Excel 文件中所有工作表名称
    try:
        all_sheets = pd.ExcelFile(excel_path).sheet_names
    except FileNotFoundError:
        print(f"Error: The file {excel_path} does not exist.")
        return
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # 遍历所有工作表
    for version in all_sheets:
        print(f"Processing version: {version}")
        All_SourceFile = Get_SourceFile(excel_path, version)
        if All_SourceFile is None:
            continue

        # 读取原始 Excel 文件
        df = pd.read_excel(excel_path, sheet_name=version)

        metrics_list = []
        for SourceFile in All_SourceFile:
            File = SourceFile["File"]
            start_line = SourceFile["Start_Line"]  # 起始行号
            end_line = SourceFile["End_Line"]  # 终止行号

            # 检查文件是否存在
            if not os.path.exists(File):  # 如果文件不存在
                # 检查文件是否以 .cc 结尾
                if File.endswith('.cc'):
                    # 替换为 .cpp 并再次检查
                    File_alternative = File.replace('.cc', '.cpp')
                    if os.path.exists(File_alternative):  # 如果替换后的文件存在
                        File = File_alternative  # 更新文件路径
                    else:
                        print(f"Warning: Neither {File} nor {File_alternative} exists.")
                        df = df[~((df.iloc[:, 0] == SourceFile["File"]) & (df.iloc[:, 1] == start_line) & (df.iloc[:, 2] == end_line))]  # 删除当前文件行
                        continue  # 跳过当前文件
                else:
                    print(f"Warning: File {File} does not exist.")
                    df = df[~((df.iloc[:, 0] == SourceFile["File"]) & (df.iloc[:, 1] == start_line) & (df.iloc[:, 2] == end_line))]  # 删除当前文件行
                    continue  # 跳过当前文件

            # 计算 Halstead 度量
            metrics = analyzer.analyze(File, start_line, end_line)
            metrics['File'] = SourceFile["File"]  # 添加文件名到度量数据
            metrics['Start_Line'] = start_line
            metrics['End_Line'] = end_line
            metrics_list.append(metrics)

        # 确保有足够的列来保存度量数据
        if len(df.columns) < 7:
            df['unique_operators'] = None
            df['unique_operands'] = None
            df['total_operators'] = None
            df['total_operands'] = None

        # 将度量数据写入到对应的行
        for metrics in metrics_list:
            file_name = metrics['File']
            start_line = metrics['Start_Line']
            end_line = metrics['End_Line']
            rows = df[(df.iloc[:, 0] == file_name) & (df.iloc[:, 1] == start_line) & (df.iloc[:, 2] == end_line)].index  # 找到对应的文件行
            for row_index in rows:
                df.at[row_index, 'unique_operators'] = metrics['unique_operators']
                df.at[row_index, 'unique_operands'] = metrics['unique_operands']
                df.at[row_index, 'total_operators'] = metrics['total_operators']
                df.at[row_index, 'total_operands'] = metrics['total_operands']

        # 保存度量到 Excel 表格
        save_metrics_to_excel(excel_path, version, df)

if __name__ == "__main__":
    main()
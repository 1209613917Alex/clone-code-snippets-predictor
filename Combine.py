import pandas as pd


def merge_intervals(intervals):
    intervals.sort(key=lambda x: x[0])
    merged = []
    for interval in intervals:
        if not merged or merged[-1][1] < interval[0]:
            merged.append(interval)
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], interval[1]))
    return merged


def merge_and_aggregate_data(input_excel_path, output_excel_path):
    # 读取所有工作表
    excel_file = pd.ExcelFile(input_excel_path)
    sheet_names = excel_file.sheet_names

    # 存储所有工作表的数据
    all_data = []

    for sheet in sheet_names:
        df = excel_file.parse(sheet)
        # 按 \\ 分割 File 列并取最后一部分
        df['File'] = df['File'].str.split('\\').str[-1]
        all_data.append(df)

    # 合并所有工作表的数据
    combined_df = pd.concat(all_data, ignore_index=True)

    final_result = []
    for file, group in combined_df.groupby('File'):
        intervals = [(row['cc_start_line'], row['cc_end_line']) for _, row in group.iterrows()]
        merged_intervals = merge_intervals(intervals)

        for start, end in merged_intervals:
            sub_group = group[((group['cc_start_line'] <= start) & (group['cc_end_line'] >= start)) |
                              ((group['cc_start_line'] <= end) & (group['cc_end_line'] >= end))]
            agg_result = {
                'File': file,
                'cc_start_line': start,
                'cc_end_line': end,
                "cc_lines": sub_group['cc_lines'].mean(),
                "author_count": sub_group['author_count'].mean(),
                "modify_count": sub_group['modify_count'].mean(),
                "avg_added": sub_group['avg_added'].mean(),
                "avg_deleted": sub_group['avg_deleted'].mean(),
                "unique_operators": sub_group['unique_operators'].mean(),
                "unique_operands": sub_group['unique_operands'].mean(),
                "total_operators": sub_group['total_operators'].mean(),
                "total_operands": sub_group['total_operands'].mean(),
                'Bug': sub_group['Bug'].max()
            }
            final_result.append(agg_result)

    aggregated_df = pd.DataFrame(final_result)

    # 保存结果到新的Excel文件
    aggregated_df.to_excel(output_excel_path, index=False)
    print(f"Aggregated data has been saved to {output_excel_path}")


if __name__ == "__main__":
    input_excel_path = input('please input your input excel path:')
    output_excel_path = input('please input your output excel path:')
    # input_excel_path = 'results/autoware.xlsx'  # 输入文件路径
    # output_excel_path = 'results/autoware_aggregated.xlsx'  # 输出文件路径
    merge_and_aggregate_data(input_excel_path, output_excel_path)

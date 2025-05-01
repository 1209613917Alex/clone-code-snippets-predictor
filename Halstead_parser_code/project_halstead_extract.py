import os
import re
import time
from collections import Counter
import pandas as pd


class HalsteadMetrics:
    def __init__(self):
        # C++操作符列表，包括操作符关键字
        self.operators = [
            '+=', '-=', '*=', '/=', '%=', '>>=', '<<=', '&=', '^=', '|=',
            '++', '--', '->', '::', '<<', '>>', '<=', '>=', '==', '!=', '&&', '||',
            '+', '-', '*', '/', '%', '=', '<', '>', '&', '|', '^', '~',
            '.', '?', ':',
            'if', 'else', 'while', 'for', 'do', 'switch',
            'case', 'break', 'continue', 'goto',
            'throw', 'try', 'catch', 'return'
        ]
        # 不计入统计的声明关键字
        self.declarations = {
            'class', 'struct', 'union', 'enum',
            'public', 'private', 'protected',
            'static', 'const', 'void',
            'int', 'float', 'double', 'char',
            'bool', 'long', 'short', 'include',
            'unsigned', 'signed', 'auto',
            'extern', 'register', 'typedef',
            'virtual', 'friend', 'operator',
            'template', 'typename', 'namespace',
            'using', 'volatile', 'explicit',
            'inline', 'constexpr', 'mutable'
        }
        # 不作为操作数的字符和关键字
        self.others = {
            '(', ')', '{', '}', '[', ']', ';', ','
        }
        # 初始化计数器
        self.unique_operators = set()
        self.unique_operands = set()
        self.total_operators = 0
        self.total_operands = 0
        self.operator_counts = Counter()
        self.operand_counts = Counter()

    def remove_comments(self, code):
        # 移除单行注释
        code = re.sub(r'//.*?\n', '\n', code)
        # 移除多行注释
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code

    def remove_strings(self, code):
        # 移除字符串字面量，但保留为操作数
        code = re.sub(r'".*?"', 'STRING_LITERAL', code)
        code = re.sub(r'\'.*?\'', 'CHAR_LITERAL', code)
        return code

    def remove_includes(self, code):
        # 移除#include指令
        code = re.sub(r'#include\s*["<][^">]*[">]', '', code)
        return code

    def remove_macros(self, code):
        # 移除宏定义
        code = re.sub(r'#define\s+.*?\\\n|#define\s+.*?\n', '', code, flags=re.DOTALL)
        code = re.sub(r'#.*?\n', '', code)
        return code

    def tokenize(self, code):
        # 创建正则表达式模式
        escaped_operators = [re.escape(op) for op in sorted(self.operators, key=len, reverse=True)]
        operator_pattern = '|'.join(escaped_operators)
        # 使用原始字符串（在字符串前加上r）来处理正则表达式
        pattern = fr'({operator_pattern})|([a-zA-Z_][a-zA-Z0-9_]*)|(\d+(?:\.\d+)?)|(\S)'
        tokens = re.findall(pattern, code)
        # 返回所有非空token
        return [token for group in tokens for token in group if token]

    def analyze(self, filename):
        try:
            start_time = time.time()  # 记录开始时间
            with open(filename, 'r', encoding='utf-8') as file:
                code = file.read()
            original_code = code
            code = self.remove_comments(code)
            code = self.remove_strings(code)
            code = self.remove_includes(code)
            code = self.remove_macros(code)
            tokens = self.tokenize(code)

            # 遍历tokens并分析每个token
            for token in tokens:
                # 实时检测时间是否超过15秒
                if time.time() - start_time > 15:
                    print(f"Analysis of {filename} took too long. Skipping...")
                    return None  # 返回None表示跳过该文件

                if token in self.operators:
                    self.unique_operators.add(token)
                    self.total_operators += 1
                    self.operator_counts[token] += 1
                elif (token.strip() and
                      token not in self.declarations and
                      token not in self.others):  # 使用others集合进行过滤
                    if not token.isspace():
                        self.unique_operands.add(token)
                        self.total_operands += 1
                        self.operand_counts[token] += 1

            return self.calculate_metrics()
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return None

    def calculate_metrics(self):
        n1 = len(self.unique_operators)
        n2 = len(self.unique_operands)
        N1 = self.total_operators
        N2 = self.total_operands
        # 计算Halstead度量
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * vocabulary
        difficulty = (n1 / n2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume
        time = effort / 18 if effort > 0 else 0
        bugs = volume / 3000 if volume > 0 else 0
        return {
            'unique_operators': n1,
            'unique_operands': n2,
            'total_operators': N1,
            'total_operands': N2,
            'vocabulary': vocabulary,
            'length': length,
            'volume': volume,
            'difficulty': difficulty,
            'effort': effort,
            'time': time,
            'bugs': bugs,
            'unique_operators_list': sorted(list(self.unique_operators)),
            'unique_operands_list': sorted(list(self.unique_operands)),
            'operator_counts': dict(self.operator_counts),
            'operand_counts': dict(self.operand_counts)
        }


def analyze_project(root_dir):
    # 遍历项目目录，找到所有头文件和源文件
    file_extensions = ['.cpp', '.h', '.cc', '.c', '.hpp']
    file_metrics = {}
    previous_metrics = None  # 用于存储前一个文件的度量值

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                filepath = os.path.join(root, file)
                print(f"Analyzing {filepath}...")
                analyzer = HalsteadMetrics()
                metrics = analyzer.analyze(filepath)

                # 如果当前文件分析时间过长，使用上一个文件的度量值
                if metrics is None:
                    if previous_metrics:
                        print(f"Using previous metrics for {filepath} due to long analysis time.")
                        file_metrics[filepath] = previous_metrics
                else:
                    file_metrics[filepath] = metrics
                    previous_metrics = metrics  # 更新为当前文件的度量值

    return file_metrics


def save_to_excel(file_metrics, output_file='halstead_metrics_apollo-8.0.0.xlsx'):
    # 使用绝对路径保存到本地
    output_file = os.path.join(os.getcwd(), output_file)  # 修改为本地路径
    print(f"Saving metrics to {output_file}")

    # 构建 DataFrame 和保存
    records = []
    for filepath, metrics in file_metrics.items():
        record = {
            'File': filepath,
            'Unique Operators (n1)': metrics['unique_operators'],
            'Unique Operands (n2)': metrics['unique_operands'],
            'Total Operators (N1)': metrics['total_operators'],
            'Total Operands (N2)': metrics['total_operands'],
            'Vocabulary (n)': metrics['vocabulary'],
            'Length (N)': metrics['length'],
            'Volume': metrics['volume'],
            'Difficulty': metrics['difficulty'],
            'Effort': metrics['effort'],
            'Time (s)': metrics['time'],
            'Bugs': metrics['bugs'],
        }
        records.append(record)

    df = pd.DataFrame(records)
    df.to_excel(output_file, index=False)
    print(f"Metrics saved to {output_file}")


def print_results(file_metrics):
    for filepath, metrics in file_metrics.items():
        print(f"\nHalstead Metrics Results for {filepath}:")
        print(f"Number of unique operators (n1): {metrics['unique_operators']}")
        print(f"Number of unique operands (n2): {metrics['unique_operands']}")
        print(f"Total number of operators (N1): {metrics['total_operators']}")
        print(f"Total number of operands (N2): {metrics['total_operands']}")
        print(f"Vocabulary (n): {metrics['vocabulary']}")
        print(f"Length (N): {metrics['length']}")
        print(f"Volume: {metrics['volume']}")
        print(f"Difficulty: {metrics['difficulty']}")
        print(f"Effort: {metrics['effort']}")
        print(f"Estimated time to implement: {metrics['time']:.2f} seconds")
        print(f"Estimated number of bugs: {metrics['bugs']:.4f}")

        print("\nOperator counts:")
        for operator, count in sorted(metrics['operator_counts'].items()):
            print(f"{operator:10} : {count}")

        print("\nOperand counts:")
        for operand, count in sorted(metrics['operand_counts'].items()):
            print(f"{operand:20} : {count}")


def main():
    project_root = input("Enter the root directory of the project: ").strip()
    file_metrics = analyze_project(project_root)
    print_results(file_metrics)
    save_to_excel(file_metrics)


if __name__ == "__main__":
    main()
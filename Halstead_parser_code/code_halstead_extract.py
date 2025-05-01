import re
import html
from collections import Counter


class HalsteadMetrics:
    def __init__(self):
        # 按长度降序排列的操作符列表，确保优先匹配长操作符
        self.operators = [
            '>>=', '<<=', '->*', '::', '.*',
            '+=', '-=', '*=', '/=', '%=', '&=', '^=', '|=',
            '==', '!=', '<=', '>=', '&&', '||', '++', '--',
            '<<', '>>', '->',
            '+', '-', '*', '/', '%',
            '<', '>', '!', '&', '|', '^', '~', '=',
            '?', ':', '.', ',',
            # 控制流关键字
            'if', 'else', 'while', 'for', 'do', 'switch',
            'case', 'break', 'continue', 'goto', 'throw',
            'try', 'catch', 'return'
        ]
        # 转义后的操作符替换为原始符号
        self.operator_replacements = {
            '&amp;': '&',
            '<': '<',
            '>': '>'
        }
        # 声明关键字和其他忽略项
        self.declarations = {
            'class', 'struct', 'union', 'enum', 'public',
            'private', 'protected', 'static', 'const', 'void',
            'int', 'float', 'double', 'char', 'bool', 'long',
            'short', 'include', 'unsigned', 'signed', 'auto',
            'extern', 'register', 'typedef', 'virtual', 'friend',
            'operator', 'template', 'typename', 'namespace',
            'using', 'volatile', 'explicit', 'inline', 'constexpr',
            'mutable', '#include'
        }
        self.others = {'(', ')', '{', '}', '[', ']', ';', ',', '...'}

    def unescape_html(self, code):
        # 替换HTML转义字符为原始符号
        for escaped, char in self.operator_replacements.items():
            code = code.replace(escaped, char)
        return code

    def remove_comments(self, code):
        code = re.sub(r'//.*?\n', '\n', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code

    def remove_strings(self, code):
        code = re.sub(r'".*?"', 'STRING_LITERAL', code)
        code = re.sub(r'\'.*?\'', 'CHAR_LITERAL', code)
        return code

    def remove_includes(self, code):
        # 改进正则以匹配所有#include行
        code = re.sub(r'#include\s*[<"][>"]*[>"]', '', code)
        return code

    def remove_macros(self, code):
        code = re.sub(r'#define\s+.*?\\\n|#define\s+.*?\n', '', code, flags=re.DOTALL)
        code = re.sub(r'#.*?\n', '', code)
        return code

    def tokenize(self, code):
        # 生成操作符正则模式（按长度降序）
        escaped_ops = sorted([re.escape(op) for op in self.operators],
                             key=lambda x: -len(x))
        operator_pattern = '|'.join(escaped_ops)
        pattern = fr'({operator_pattern})|([a-zA-Z_]\w*)|(\d+\.?\d*)|(\S)'
        tokens = re.findall(pattern, code)
        return [t for group in tokens for t in group if t]

    def analyze(self, filename, start_line=None, end_line=None):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            code = ''.join(lines[start_line - 1:end_line] if (start_line and end_line) else lines)

            code = self.unescape_html(code)  # 处理HTML转义
            code = self.remove_includes(code)
            code = self.remove_macros(code)
            code = self.remove_comments(code)
            code = self.remove_strings(code)

            tokens = self.tokenize(code)

            # 重置计数器
            self.unique_operators = set()
            self.unique_operands = set()
            self.total_operators = 0
            self.total_operands = 0
            self.operator_counts = Counter()
            self.operand_counts = Counter()

            for token in tokens:
                if token in self.operators:
                    self.unique_operators.add(token)
                    self.total_operators += 1
                    self.operator_counts[token] += 1
                elif token not in self.declarations and token not in self.others:
                    if not token.strip().isdigit() and not token.startswith('STRING_'):
                        self.unique_operands.add(token)
                        self.total_operands += 1
                        self.operand_counts[token] += 1

            return self.calculate_metrics()

        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def calculate_metrics(self):
        n1 = len(self.unique_operators)
        n2 = len(self.unique_operands)
        return {
            'unique_operators': n1,
            'unique_operands': n2,
            'total_operators': self.total_operators,
            'total_operands': self.total_operands,
            'vocabulary': n1 + n2,
            'length': self.total_operators + self.total_operands,
            'operators': dict(self.operator_counts),
            'operands': dict(self.operand_counts)
        }

def main():
    analyzer = HalsteadMetrics()
    filename = r"example.cpp"  # 替换为你的C++文件路径
    metrics = analyzer.analyze(filename)
    if metrics:
        print(metrics)


if __name__ == "__main__":
    main()
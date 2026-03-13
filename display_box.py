#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shell风格显示框生成器
支持多种样式的文本框，模仿shell脚本的视觉效果
"""

import sys
import io

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class ShellDisplayBox:
    """Shell风格显示框类"""
    
    # ANSI颜色代码
    COLORS = {
        'red': '\033[0;31m',
        'green': '\033[0;32m',
        'yellow': '\033[1;33m',
        'blue': '\033[0;34m',
        'purple': '\033[0;35m',
        'cyan': '\033[0;36m',
        'white': '\033[1;37m',
        'reset': '\033[0m',
        'bold': '\033[1m',
    }
    
    def __init__(self, width=50, use_color=True):
        """
        初始化显示框
        :param width: 框的宽度
        :param use_color: 是否使用颜色
        """
        self.width = width
        self.use_color = use_color and self._supports_color()
    
    def _supports_color(self):
        """检查终端是否支持颜色"""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    def _color(self, text, color_name):
        """给文本添加颜色"""
        if not self.use_color:
            return text
        color_code = self.COLORS.get(color_name, '')
        reset_code = self.COLORS['reset']
        return f"{color_code}{text}{reset_code}"
    
    def single_box(self, text):
        """单线框"""
        border = self._color("-" * self.width, 'cyan')
        padding = (self.width - len(text)) // 2
        
        top_bottom = border
        middle = (
            self._color("|", 'cyan') + 
            " " * padding + 
            self._color(text, 'white') + 
            " " * (self.width - padding - len(text) - 1) + 
            self._color("|", 'cyan')
        )
        
        return f"{top_bottom}\n{middle}\n{top_bottom}"
    
    def double_box(self, text):
        """双线框"""
        border = self._color("=" * self.width, 'green')
        padding = (self.width - len(text)) // 2
        
        top_bottom = border
        middle = (
            self._color("|", 'green') + 
            " " * padding + 
            self._color(text, 'white') + 
            " " * (self.width - padding - len(text) - 1) + 
            self._color("|", 'green')
        )
        
        return f"{top_bottom}\n{middle}\n{top_bottom}"
    
    def star_box(self, text):
        """星形框"""
        border = self._color("*" * self.width, 'yellow')
        padding = (self.width - len(text)) // 2
        
        top_bottom = border
        middle = (
            self._color("*", 'yellow') + 
            " " * padding + 
            self._color(text, 'white') + 
            " " * (self.width - padding - len(text) - 1) + 
            self._color("*", 'yellow')
        )
        
        return f"{top_bottom}\n{middle}\n{top_bottom}"
    
    def hash_box(self, text):
        """井号框"""
        border = self._color("#" * self.width, 'purple')
        padding = (self.width - len(text)) // 2
        
        top_bottom = border
        middle = (
            self._color("#", 'purple') + 
            " " * padding + 
            self._color(text, 'white') + 
            " " * (self.width - padding - len(text) - 1) + 
            self._color("#", 'purple')
        )
        
        return f"{top_bottom}\n{middle}\n{top_bottom}"
    
    def info_box(self, title, content_lines):
        """信息框（多行）"""
        lines = []
        
        # 顶部边框
        lines.append(self._color("═" * self.width, 'blue'))
        
        # 标题行
        title_padding = (self.width - len(title) - 2) // 2
        title_line = (
            self._color("║", 'blue') + 
            " " * title_padding + 
            self._color(title, 'yellow') + 
            " " * (self.width - title_padding - len(title) - 2) + 
            self._color("║", 'blue')
        )
        lines.append(title_line)
        
        # 分隔线
        separator = self._color("║", 'blue') + "─" * (self.width - 2) + self._color("║", 'blue')
        lines.append(separator)
        
        # 内容行
        if isinstance(content_lines, str):
            content_lines = [content_lines]
        
        for line in content_lines:
            content_line = (
                self._color("║", 'blue') + 
                " " + 
                self._color(line, 'white') + 
                " " * (self.width - len(line) - 3) + 
                self._color("║", 'blue')
            )
            lines.append(content_line)
        
        # 底部边框
        lines.append(self._color("═" * self.width, 'blue'))
        
        return "\n".join(lines)
    
    def warning_box(self, text):
        """警告框"""
        border = self._color("!" * self.width, 'red')
        message = self._color("!", 'red') + " " + self._color("WARNING:", 'yellow') + " " + self._color(text, 'white')
        return f"{border}\n{message}\n{border}"
    
    def success_box(self, text):
        """成功框"""
        # 使用ASCII字符替代Unicode字符
        border = self._color("OK" * (self.width // 2), 'green')
        message = self._color("[OK]", 'green') + " " + self._color("SUCCESS:", 'white') + " " + self._color(text, 'green')
        return f"{border}\n{message}\n{border}"
    
    def code_box(self, code_lines, language=""):
        """代码框"""
        lines = []
        
        # 顶部边框
        title = f" {language} " if language else " CODE "
        lines.append(self._color("+" + "-" * (self.width - 2) + "+", 'cyan'))
        
        # 代码内容
        if isinstance(code_lines, str):
            code_lines = code_lines.split('\n')
        
        for line in code_lines:
            code_line = (
                self._color("|", 'cyan') + 
                " " + 
                line + 
                " " * (self.width - len(line) - 3) + 
                self._color("|", 'cyan')
            )
            lines.append(code_line)
        
        # 底部边框
        lines.append(self._color("+" + "-" * (self.width - 2) + "+", 'cyan'))
        
        return "\n".join(lines)


def demo():
    """演示所有样式"""
    print("\n" * 2)
    
    box = ShellDisplayBox(width=50)
    
    # 演示各种样式
    print(box.single_box("Single Box Demo"))
    print()
    
    print(box.double_box("Double Box Demo"))
    print()
    
    print(box.star_box("Star Box Demo"))
    print()
    
    print(box.hash_box("Hash Box Demo"))
    print()
    
    print(box.info_box("Info Box", [
        "Multi-line info box demo",
        "Can display multiple lines",
        "Good for detailed information"
    ]))
    print()
    
    print(box.warning_box("This is a warning message"))
    print()
    
    print(box.success_box("Operation completed successfully"))
    print()
    
    print(box.code_box([
        "def hello_world():",
        "    print('Hello, World!')",
        "    return True",
        "",
        "# This is a code example",
        "result = hello_world()"
    ], "Python"))


def interactive():
    """交互式模式"""
    print("\n=== Shell Style Display Box Generator ===\n")
    
    box = ShellDisplayBox(width=50)
    
    while True:
        print("\nSelect box style:")
        print("1. Single Box")
        print("2. Double Box")
        print("3. Star Box")
        print("4. Hash Box")
        print("5. Info Box")
        print("6. Warning Box")
        print("7. Success Box")
        print("8. Code Box")
        print("9. Show All Demo")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-9): ").strip()
        
        if choice == '0':
            print("Goodbye!")
            break
        elif choice == '1':
            text = input("Enter text: ")
            print(f"\n{box.single_box(text)}\n")
        elif choice == '2':
            text = input("Enter text: ")
            print(f"\n{box.double_box(text)}\n")
        elif choice == '3':
            text = input("Enter text: ")
            print(f"\n{box.star_box(text)}\n")
        elif choice == '4':
            text = input("Enter text: ")
            print(f"\n{box.hash_box(text)}\n")
        elif choice == '5':
            title = input("Enter title: ")
            content = input("Enter content: ")
            print(f"\n{box.info_box(title, [content])}\n")
        elif choice == '6':
            text = input("Enter warning message: ")
            print(f"\n{box.warning_box(text)}\n")
        elif choice == '7':
            text = input("Enter success message: ")
            print(f"\n{box.success_box(text)}\n")
        elif choice == '8':
            code = input("Enter code (use \\n for multiple lines): ")
            lines = code.split('\\n')
            print(f"\n{box.code_box(lines, 'Code')}\n")
        elif choice == '9':
            demo()
        else:
            print("Invalid choice, please try again")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        demo()
    else:
        interactive()

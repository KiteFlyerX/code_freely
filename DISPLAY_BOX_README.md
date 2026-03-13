# Shell风格显示框生成器

这是一个用Python实现的Shell风格显示框生成器，可以创建多种样式的文本框，模仿shell脚本的视觉效果。

## 功能特性

- **多种框样式**：单线框、双线框、星形框、井号框等
- **彩色输出**：支持ANSI颜色代码，在支持的终端中显示彩色
- **多行支持**：信息框和代码框支持多行内容
- **交互式模式**：可以交互式选择样式和输入内容
- **演示模式**：一键演示所有可用样式

## 使用方法

### 1. 直接运行（交互式模式）

```bash
python display_box.py
```

进入交互式模式，按照提示选择样式和输入内容。

### 2. 演示模式

```bash
python display_box.py --demo
```

自动演示所有可用的显示框样式。

### 3. 作为模块使用

```python
from display_box import ShellDisplayBox

# 创建显示框实例
box = ShellDisplayBox(width=50)

# 使用不同的样式
print(box.single_box("Hello World"))
print(box.double_box("Important Message"))
print(box.star_box("Featured Content"))
print(box.hash_box("Note"))

# 多行信息框
print(box.info_box("Information", [
    "Line 1",
    "Line 2", 
    "Line 3"
]))

# 警告和成功框
print(box.warning_box("This is a warning"))
print(box.success_box("Operation successful"))

# 代码框
print(box.code_box([
    "def hello():",
    "    print('Hello')",
    "    return True"
], "Python"))
```

## 可用的显示框样式

### 1. 单线框 (Single Box)
```
--------------------------------------------------
|              Your Text Here                    |
--------------------------------------------------
```

### 2. 双线框 (Double Box)
```
==================================================
|              Your Text Here                    |
==================================================
```

### 3. 星形框 (Star Box)
```
**************************************************
*              Your Text Here                    *
**************************************************
```

### 4. 井号框 (Hash Box)
```
##################################################
#              Your Text Here                    #
##################################################
```

### 5. 信息框 (Info Box)
```
══════════════════════════════════════════════════
║                    Title                       ║
║────────────────────────────────────────────────║
║ Content line 1                                 ║
║ Content line 2                                 ║
══════════════════════════════════════════════════
```

### 6. 警告框 (Warning Box)
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! WARNING: Your warning message here
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

### 7. 成功框 (Success Box)
```
OKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOK
[OK] SUCCESS: Your success message here
OKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOKOK
```

### 8. 代码框 (Code Box)
```
+------------------------------------------------+
| def hello_world():                             |
|     print('Hello, World!')                     |
|     return True                                |
+------------------------------------------------+
```

## 自定义选项

### 调整框的宽度

```python
box = ShellDisplayBox(width=80)  # 创建宽度为80的框
```

### 禁用颜色

```python
box = ShellDisplayBox(width=50, use_color=False)  # 纯文本输出
```

## 系统要求

- Python 3.6+
- 支持ANSI颜色代码的终端（可选）

## 注意事项

- 在Windows CMD中可能无法正确显示颜色，建议使用Windows Terminal或PowerShell
- 某些字符在不同终端中的显示效果可能不同
- 如果遇到编码问题，请确保终端使用UTF-8编码

## 示例输出

运行 `python display_box.py --demo` 可以看到所有样式的实际效果。

## 许可证

MIT License

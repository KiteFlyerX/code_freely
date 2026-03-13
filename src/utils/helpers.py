"""
工具函数模块
提供通用的工具函数
"""
from pathlib import Path
from typing import Optional, List


def get_project_root(path: Optional[str] = None) -> Path:
    """
    获取项目根目录

    检测常见版本控制目录来确认项目根目录

    Args:
        path: 起始路径，None 表示当前目录

    Returns:
        Path: 项目根目录
    """
    if path is None:
        path = Path.cwd()
    else:
        path = Path(path)

    # 检查当前目录
    vcs_dirs = {".git", ".svn", ".hg"}
    for vcs_dir in vcs_dirs:
        if (path / vcs_dir).exists():
            return path

    # 向上查找
    parent = path.parent
    if parent != path:  # 没有到达文件系统根目录
        return get_project_root(str(parent))

    return path


def is_valid_project_path(path: str) -> bool:
    """
    检查是否是有效的项目路径

    Args:
        path: 路径

    Returns:
        bool: 是否有效
    """
    p = Path(path)
    return p.exists() and p.is_dir()


def find_code_files(
    project_path: str,
    extensions: Optional[List[str]] = None,
) -> List[str]:
    """
    查找项目中的代码文件

    Args:
        project_path: 项目路径
        extensions: 文件扩展名列表，None 表示默认列表

    Returns:
        List[str]: 代码文件路径列表（相对于项目根目录）
    """
    if extensions is None:
        extensions = [
            ".py", ".js", ".ts", ".tsx", ".jsx",
            ".java", ".cpp", ".c", ".cs", ".go",
            ".rs", ".rb", ".php", ".swift", ".kt",
        ]

    project_root = Path(project_path)
    code_files = []

    for ext in extensions:
        for file_path in project_root.rglob(f"*{ext}"):
            # 排除 node_modules、venv 等目录
            if "node_modules" not in str(file_path) and "venv" not in str(file_path):
                rel_path = file_path.relative_to(project_root)
                code_files.append(str(rel_path))

    return sorted(code_files)


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        str: 格式化后的大小（如 "1.5 MB"）
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀

    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_code_blocks(text: str, language: Optional[str] = None) -> List[str]:
    """
    从文本中提取代码块

    Args:
        text: 包含代码块的文本
        language: 指定语言过滤，None 表示提取所有

    Returns:
        List[str]: 代码块列表
    """
    import re

    pattern = r"```(\w*)\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)

    if language:
        return [code for lang, code in matches if lang.lower() == language.lower()]
    else:
        return [code for lang, code in matches]


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        str: 清理后的文件名
    """
    import re

    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # 限制长度
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255 - len(ext)] + ('.' + ext if ext else '')

    return filename

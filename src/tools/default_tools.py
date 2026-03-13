"""
基础工具实现
提供文件读取、写入、命令执行等基础功能
"""
import os
import subprocess
from pathlib import Path
from typing import Optional

from .base import BaseTool, ToolCategory, ToolResult, ToolParameter, tool_registry


class Read(BaseTool):
    """
    读取文件工具
    读取指定文件的内容
    """

    def __init__(self):
        super().__init__()
        self.name = "Read"
        self.category = ToolCategory.FILE
        self.description = "读取文件内容。如果需要查看特定文件，请使用此工具。"
        self.parameters = [
            ToolParameter(
                name="file_path",
                type="string",
                description="要读取的文件路径（相对于当前工作目录的相对路径，或绝对路径）",
                required=True,
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="可选，读取的最大行数。默认读取整个文件",
                required=False,
                default=None,
            ),
            ToolParameter(
                name="offset",
                type="integer",
                description="可选，从第几行开始读取。默认从第1行开始",
                required=False,
                default=1,
            ),
        ]

    def execute(self, file_path: str, limit: Optional[int] = None, offset: int = 1) -> ToolResult:
        """执行文件读取"""
        try:
            # 获取当前工作目录
            cwd = Path.cwd()

            # 处理路径
            path = Path(file_path)
            if not path.is_absolute():
                path = cwd / path

            # 检查文件是否存在
            if not path.exists():
                return ToolResult(
                    success=False,
                    error=f"文件不存在: {path}"
                )

            # 检查是否是文件
            if not path.is_file():
                return ToolResult(
                    success=False,
                    error=f"路径不是文件: {path}"
                )

            # 读取文件
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                if limit:
                    # 跳过 offset-1 行
                    for _ in range(offset - 1):
                        f.readline()
                    # 读取 limit 行
                    lines = []
                    for _ in range(limit):
                        line = f.readline()
                        if not line:
                            break
                        lines.append(line.rstrip("\n"))
                    content = "\n".join(lines)
                else:
                    content = f.read()

            return ToolResult(
                success=True,
                data={
                    "file_path": str(path),
                    "content": content,
                    "size": len(content),
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"读取文件失败: {str(e)}"
            )


class Write(BaseTool):
    """
    写入文件工具
    将内容写入指定文件
    """

    def __init__(self):
        super().__init__()
        self.name = "Write"
        self.category = ToolCategory.FILE
        self.description = "将内容写入文件。如果文件已存在，将会覆盖整个文件。如果要修改现有文件，请先使用 Read 工具读取文件内容。"
        self.parameters = [
            ToolParameter(
                name="file_path",
                type="string",
                description="要写入的文件路径（相对于当前工作目录的相对路径，或绝对路径）",
                required=True,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="要写入的内容",
                required=True,
            ),
        ]

    def execute(self, file_path: str, content: str) -> ToolResult:
        """执行文件写入"""
        try:
            # 获取当前工作目录
            cwd = Path.cwd()

            # 处理路径
            path = Path(file_path)
            if not path.is_absolute():
                path = cwd / path

            # 创建父目录
            path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return ToolResult(
                success=True,
                data={
                    "file_path": str(path),
                    "bytes_written": len(content.encode("utf-8")),
                    "message": f"文件已写入: {path}",
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"写入文件失败: {str(e)}"
            )


class Bash(BaseTool):
    """
    执行命令工具
    在 shell 中执行命令
    """

    def __init__(self):
        super().__init__()
        self.name = "Bash"
        self.category = ToolCategory.SYSTEM
        self.description = "在 shell 中执行命令。用于执行系统命令、git 操作、运行测试等。"
        self.parameters = [
            ToolParameter(
                name="command",
                type="string",
                description="要执行的命令",
                required=True,
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="可选，命令超时时间（秒）。默认120秒",
                required=False,
                default=120,
            ),
        ]

    def execute(self, command: str, timeout: int = 120) -> ToolResult:
        """执行命令"""
        try:
            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(Path.cwd())
            )

            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"

            return ToolResult(
                success=result.returncode == 0,
                data={
                    "command": command,
                    "returncode": result.returncode,
                    "output": output,
                }
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error=f"命令执行超时（超过 {timeout} 秒）"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"命令执行失败: {str(e)}"
            )


class Glob(BaseTool):
    """
    文件搜索工具
    使用 glob 模式搜索文件
    """

    def __init__(self):
        super().__init__()
        self.name = "Glob"
        self.category = ToolCategory.SEARCH
        self.description = "使用 glob 模式搜索文件。例如: **/*.py 搜索所有 Python 文件，src/**/*.tsx 搜索 src 目录下的所有 TSX 文件。"
        self.parameters = [
            ToolParameter(
                name="pattern",
                type="string",
                description="glob 搜索模式。支持 ** 递归匹配，* 单级匹配等",
                required=True,
            ),
        ]

    def execute(self, pattern: str) -> ToolResult:
        """执行文件搜索"""
        try:
            import glob as glob_module

            # 在当前工作目录搜索
            matches = glob_module.glob(pattern, recursive=True)

            return ToolResult(
                success=True,
                data={
                    "pattern": pattern,
                    "matches": matches,
                    "count": len(matches),
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"文件搜索失败: {str(e)}"
            )


# 注册所有工具
def register_default_tools():
    """注册默认工具"""
    tool_registry.register(Read())
    tool_registry.register(Write())
    tool_registry.register(Bash())
    tool_registry.register(Glob())


# 自动注册
register_default_tools()

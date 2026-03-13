"""
工具系统
提供 AI 可调用的工具
"""
from .base import (
    BaseTool,
    ToolCategory,
    ToolParameter,
    ToolResult,
    ToolRegistry,
    tool_registry,
)

# 注册默认工具
from .default_tools import register_default_tools

# 确保默认工具已注册
register_default_tools()

__all__ = [
    "BaseTool",
    "ToolCategory",
    "ToolParameter",
    "ToolResult",
    "ToolRegistry",
    "tool_registry",
    "register_default_tools",
]

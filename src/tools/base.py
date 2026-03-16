"""
工具系统
提供 AI 可调用的工具，用于读取文件、写入代码、执行命令等
"""
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum


class ToolCategory(Enum):
    """工具分类"""
    FILE = "file"  # 文件操作
    CODE = "code"  # 代码操作
    SYSTEM = "system"  # 系统命令
    SEARCH = "search"  # 搜索


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str  # string, integer, boolean, array, object
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None  # 枚举值限制


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        return result


class BaseTool:
    """
    工具基类
    所有工具必须继承此类
    """

    def __init__(self):
        self.name = self.__class__.__name__
        self.category = ToolCategory.SYSTEM
        self.description = ""
        self.parameters: List[ToolParameter] = []
        self.requires_confirmation: bool = False  # 是否需要用户确认

    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的 OpenAI function calling 格式 schema

        Returns:
            Dict[str, Any]: 工具 schema
        """
        properties = {}
        required = []

        for param in self.parameters:
            prop_schema = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop_schema["enum"] = param.enum
            if param.default is not None:
                prop_schema["default"] = param.default

            properties[param.name] = prop_schema
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def execute(self, **kwargs) -> ToolResult:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        raise NotImplementedError("子类必须实现 execute 方法")

    def get_confirmation_message(self, **kwargs) -> str:
        """
        获取确认消息（当需要用户确认时）

        Args:
            **kwargs: 工具参数

        Returns:
            str: 确认消息
        """
        return f"确认执行 {self.name}?"


class ToolRegistry:
    """
    工具注册表
    管理所有可用工具
    """

    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, BaseTool] = {}
    _permission_handler: Optional[Callable[[str, Dict[str, Any]], bool]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)

    def set_permission_handler(self, handler: Callable[[str, Dict[str, Any]], bool]):
        """
        设置权限处理器

        Args:
            handler: 权限检查函数 (tool_name, arguments) -> bool
                     返回 True 表示允许执行，False 表示拒绝
        """
        self._permission_handler = handler

    def list_tools(self, category: Optional[ToolCategory] = None) -> List[BaseTool]:
        """列出工具"""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def get_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 schema"""
        return [tool.get_schema() for tool in self._tools.values()]

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"工具 '{tool_name}' 不存在"
            )

        # 检查权限
        if self._permission_handler:
            allowed = self._permission_handler(tool_name, kwargs)
            if not allowed:
                return ToolResult(
                    success=False,
                    error=f"工具 '{tool_name}' 执行被用户拒绝"
                )

        return tool.execute(**kwargs)


# 全局工具注册表实例
tool_registry = ToolRegistry()

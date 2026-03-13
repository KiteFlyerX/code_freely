"""
AI 接口抽象层
定义统一的 AI 模型接口，支持多种 AI 提供商和工具调用
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, Optional, List, Dict, Any, Callable
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"  # 工具返回消息


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None  # 工具执行结果


@dataclass
class Message:
    """对话消息"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: Optional[List[ToolCall]] = None  # 工具调用列表
    tool_call_id: Optional[str] = None  # 关联的工具调用 ID


@dataclass
class AIResponse:
    """AI 响应结果"""
    content: str
    model: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None
    tool_calls: Optional[List[ToolCall]] = None  # 工具调用列表


@dataclass
class AIRequestConfig:
    """AI 请求配置"""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    stream: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)
    tools: Optional[List[Dict[str, Any]]] = None  # 可用工具列表
    tool_choice: Any = None  # 工具选择策略：None, "auto", "any", 或具体工具名


class BaseAI(ABC):
    """
    AI 接口抽象基类
    所有 AI 提供商实现必须继承此类
    """

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        初始化 AI 客户端

        Args:
            api_key: API 密钥
            model: 模型名称
            **kwargs: 其他配置参数
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        config: Optional[AIRequestConfig] = None
    ) -> AIResponse:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            config: 请求配置

        Returns:
            AIResponse: AI 响应结果
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        config: Optional[AIRequestConfig] = None
    ) -> AsyncIterator[str]:
        """
        流式聊天请求

        Args:
            messages: 消息列表
            config: 请求配置

        Yields:
            str: 流式响应片段
        """
        pass

    async def chat_stream_collect_tools(
        self,
        messages: List[Message],
        config: Optional[AIRequestConfig] = None
    ) -> tuple[AsyncIterator[str], List[ToolCall]]:
        """
        流式聊天请求，同时收集工具调用（可选实现）

        默认实现使用非流模式，子类可以重写以支持真正的流式

        Args:
            messages: 消息列表
            config: 请求配置

        Returns:
            tuple: (流式文本迭代器, 工具调用列表)
        """
        # 默认实现：使用非流模式
        response = await self.chat(messages, config)

        async def text_gen():
            if response.content:
                yield response.content

        tool_calls = response.tool_calls if response.tool_calls else []
        return text_gen(), tool_calls

    @abstractmethod
    def validate_api_key(self) -> bool:
        """
        验证 API 密钥是否有效

        Returns:
            bool: 密钥是否有效
        """
        pass

    async def chat_with_tools_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_executor: Optional[Callable] = None,
        config: Optional[AIRequestConfig] = None,
        max_iterations: int = 10,
    ) -> AsyncIterator[str]:
        """
        带工具调用的流式聊天

        Args:
            messages: 消息列表
            tools: 可用工具列表
            tool_executor: 工具执行函数 (tool_name, arguments) -> ToolResult
            config: 请求配置
            max_iterations: 最大工具调用迭代次数

        Yields:
            str: 流式响应片段
        """
        if config is None:
            config = AIRequestConfig()
        config.tools = tools

        current_messages = messages.copy()
        iterations = 0

        while iterations < max_iterations:
            # 调用 AI（流式输出，同时收集工具调用）
            text_stream, tool_calls = await self.chat_stream_collect_tools(current_messages, config)

            # 流式输出文本内容
            full_content = ""
            async for chunk in text_stream:
                full_content += chunk
                yield chunk

            # 如果没有工具调用，直接返回
            if not tool_calls:
                return

            # 添加 AI 响应到消息列表
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=full_content,
                tool_calls=tool_calls,
            )
            current_messages.append(assistant_message)

            # 显示工具调用信息
            for tool_call in tool_calls:
                # 格式化参数显示
                args_str = ""
                if tool_call.arguments:
                    if isinstance(tool_call.arguments, dict):
                        args_str = " ".join([f"{k}={v}" for k, v in list(tool_call.arguments.items())[:2]])
                yield f"\n🔧 {tool_call.name} {args_str}"

            # 执行工具调用
            for tool_call in tool_calls:
                if tool_executor:
                    result = tool_executor(tool_call.name, tool_call.arguments)
                    # result 可能是 dict 或 ToolResult 对象
                    if isinstance(result, dict):
                        result_str = str(result)
                    elif hasattr(result, 'to_dict'):
                        result_str = str(result.to_dict())
                    else:
                        result_str = str(result)
                    tool_call.result = result_str

                    # 显示工具结果（简化显示）
                    if isinstance(result, dict) and result.get('success'):
                        data = result.get('data', {})
                        if isinstance(data, dict):
                            if 'content' in data:
                                content = data['content']
                                if len(content) > 100:
                                    yield f"✓ 已读取 {len(content)} 字符"
                                else:
                                    yield f"✓ 读取成功"
                            elif 'output' in data:
                                output = data['output']
                                lines = output.split('\n')
                                if len(lines) > 5:
                                    yield f"✓ 命令输出: {len(lines)} 行"
                                elif len(output) > 200:
                                    yield f"✓ 输出: {output[:100]}..."
                                else:
                                    # 只显示前两行
                                    preview_lines = lines[:2]
                                    preview = '\n'.join(preview_lines)
                                    if len(lines) > 2:
                                        preview += f"\n... ({len(lines)-2} 更多行)"
                                    yield f"✓ 输出:\n{preview}"
                            elif 'message' in data:
                                yield f"✓ {data['message']}"
                            elif 'auto_committed' in data and data.get('auto_committed'):
                                # Write 工具自动提交成功
                                yield f"✓ 已写入并自动提交"
                            else:
                                yield f"✓ 执行成功"
                        else:
                            yield f"✓ 执行成功"
                    elif isinstance(result, dict):
                        error = result.get('error', '未知错误')
                        if len(error) > 100:
                            error = error[:100] + "..."
                        yield f"✗ 错误: {error}"
                    else:
                        preview = result_str[:100]
                        if len(result_str) > 100:
                            preview += "..."
                        yield f"→ 结果: {preview}"

                    # 添加工具结果消息
                    tool_message = Message(
                        role=MessageRole.TOOL,
                        content=tool_call.result,
                        tool_call_id=tool_call.id,
                    )
                    current_messages.append(tool_message)

            iterations += 1

    async def chat_with_tools(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_executor: Optional[Callable] = None,
        config: Optional[AIRequestConfig] = None,
        max_iterations: int = 10,
    ) -> AIResponse:
        """
        带工具调用的聊天

        Args:
            messages: 消息列表
            tools: 可用工具列表
            tool_executor: 工具执行函数 (tool_name, arguments) -> ToolResult
            config: 请求配置
            max_iterations: 最大工具调用迭代次数

        Returns:
            AIResponse: 最终 AI 响应结果
        """
        if config is None:
            config = AIRequestConfig()
        config.tools = tools

        current_messages = messages.copy()
        iterations = 0

        while iterations < max_iterations:
            # 调用 AI
            response = await self.chat(current_messages, config)

            # 如果没有工具调用，直接返回
            if not response.tool_calls:
                return response

            # 添加 AI 响应到消息列表
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=response.content or "",
                tool_calls=response.tool_calls,
            )
            current_messages.append(assistant_message)

            # 执行工具调用
            for tool_call in response.tool_calls:
                if tool_executor:
                    result = tool_executor(tool_call.name, tool_call.arguments)
                    # result 可能是 dict 或 ToolResult 对象
                    if isinstance(result, dict):
                        tool_call.result = str(result)
                    elif hasattr(result, 'to_dict'):
                        tool_call.result = str(result.to_dict())
                    else:
                        tool_call.result = str(result)

                    # 添加工具结果消息
                    tool_message = Message(
                        role=MessageRole.TOOL,
                        content=tool_call.result,
                        tool_call_id=tool_call.id,
                    )
                    current_messages.append(tool_message)

            iterations += 1

        # 达到最大迭代次数，返回最后一次响应
        return response

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "provider": self.__class__.__name__,
            "model": self.model,
        }

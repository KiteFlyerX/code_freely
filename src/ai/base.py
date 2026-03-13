"""
AI 接口抽象层
定义统一的 AI 模型接口，支持多种 AI 提供商
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, Optional, List, Dict, Any
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """对话消息"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AIResponse:
    """AI 响应结果"""
    content: str
    model: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None


@dataclass
class AIRequestConfig:
    """AI 请求配置"""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    stream: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)


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

    @abstractmethod
    def validate_api_key(self) -> bool:
        """
        验证 API 密钥是否有效

        Returns:
            bool: 密钥是否有效
        """
        pass

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
